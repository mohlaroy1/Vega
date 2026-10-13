
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import BloodRequestForm, DonorRegistrationForm
from .models import BloodRequest, DonorProfile, Match

class DonorRegistrationFormTests(TestCase):
    def valid_data(self):
        return {
            "username": "testdonor",
            "first_name": "Test",
            "last_name": "Donor",
            "email": "donor@example.com",
            "password1": "SafeTestPass123!",
            "password2": "SafeTestPass123!",
            "blood_type": "O+",
            "city": "Fergana",
            "district": "",
            "latitude": "40.3864",
            "longitude": "71.7864",
            "last_donation_date": "",
            "consent": "on",
        }

    def test_valid_coordinates_are_accepted(self):
        form = DonorRegistrationForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_latitude_is_rejected(self):
        data = self.valid_data()
        data["latitude"] = "91"
        form = DonorRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("latitude", form.errors)

    def test_invalid_longitude_is_rejected(self):
        data = self.valid_data()
        data["longitude"] = "181"
        form = DonorRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("longitude", form.errors)


class BloodRequestFormTests(TestCase):
    def valid_data(self):
        return {
            "blood_type": "O+",
            "hospital_name": "Test Hospital",
            "hospital_address": "Fergana",
            "latitude": "40.3864",
            "longitude": "71.7864",
            "urgency": "normal",
            "description": "Test request",
        }

    def test_valid_coordinates_are_accepted(self):
        form = BloodRequestForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_latitude_is_rejected(self):
        data = self.valid_data()
        data["latitude"] = "-91"
        form = BloodRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("latitude", form.errors)

    def test_invalid_longitude_is_rejected(self):
        data = self.valid_data()
        data["longitude"] = "-181"
        form = BloodRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("longitude", form.errors)

    def test_request_expires_after_24_hours(self):
        form = BloodRequestForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

        request = form.save(commit=False)
        remaining = request.expires_at - timezone.now()

        self.assertAlmostEqual(
            remaining.total_seconds(),
            24 * 60 * 60,
            delta=5,
        )


class MatchResponseTests(TestCase):
    def setUp(self):
        self.donor_user = User.objects.create_user(
            username="donor",
            password="SafeTestPass123!",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="SafeTestPass123!",
        )
        self.donor = DonorProfile.objects.create(
            user=self.donor_user,
            blood_type="O+",
            city="Fergana",
            latitude=40.3864,
            longitude=71.7864,
            consent=True,
        )
        self.blood_request = BloodRequest.objects.create(
            requester=self.other_user,
            blood_type="O+",
            hospital_name="Test Hospital",
            hospital_address="Fergana",
            latitude=40.3864,
            longitude=71.7864,
            urgency="normal",
            verified=True,
            expires_at=timezone.now() + timedelta(hours=2),
        )
        self.match = Match.objects.create(
            blood_request=self.blood_request,
            donor=self.donor,
            distance_km=1.0,
        )
        self.url = reverse(
            "respond_to_match",
            args=[self.match.id, "accept"],
        )

    def test_get_request_is_not_allowed(self):
        self.client.force_login(self.donor_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.NOTIFIED)

    def test_donor_can_accept_match_with_post(self):
        self.client.force_login(self.donor_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.RESPONDED)


    def test_donor_can_decline_match_with_post(self):
        self.client.force_login(self.donor.user)

        response = self.client.post(
            reverse(
                "respond_to_match",
                args=[self.match.id, "decline"],
            )
        )

        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.DECLINED)

    def test_another_user_cannot_accept_match(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.NOTIFIED)

    def test_expired_request_cannot_be_accepted(self):
        self.blood_request.expires_at = timezone.now() - timedelta(hours=1)
        self.blood_request.save(update_fields=["expires_at"])

        self.client.force_login(self.donor_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.NOTIFIED)