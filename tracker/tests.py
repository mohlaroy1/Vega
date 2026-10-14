
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import BloodRequestForm, DonorRegistrationForm
from .models import BloodRequest, DonorProfile, Match
from .matching import create_matches, find_potential_donors

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


    
class DonorAvailabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="availability_donor",
            password="SafeTestPass123!",
        )
        self.profile = DonorProfile.objects.create(
            user=self.user,
            blood_type="O+",
            city="Fergana",
            latitude=40.3864,
            longitude=71.7864,
            available=True,
            consent=True,
        )

    def test_donor_can_toggle_availability_off(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("toggle_availability"))

        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.available)

    def test_get_request_cannot_toggle_availability(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("toggle_availability"))

        self.assertEqual(response.status_code, 405)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.available)




class MatchingLogicTests(TestCase):
    def setUp(self):
        self.requester = User.objects.create_user(
            username="matching_requester",
            password="SafeTestPass123!",
        )

        self.blood_request = BloodRequest.objects.create(
            requester=self.requester,
            blood_type="A+",
            hospital_name="Test Hospital",
            hospital_address="Fergana",
            latitude=40.3864,
            longitude=71.7864,
            urgency="normal",
            verified=True,
            status=BloodRequest.Status.OPEN,
            expires_at=timezone.now() + timedelta(hours=2),
        )

    def make_donor(
        self,
        username,
        blood_type="O+",
        available=True,
        consent=True,
        latitude=40.3864,
        longitude=71.7864,
    ):
        user = User.objects.create_user(
            username=username,
            password="SafeTestPass123!",
        )

        return DonorProfile.objects.create(
            user=user,
            blood_type=blood_type,
            city="Fergana",
            latitude=latitude,
            longitude=longitude,
            available=available,
            consent=consent,
        )

    def test_only_eligible_donors_are_matched(self):
        eligible = self.make_donor("eligible_donor")
        self.make_donor("unavailable_donor", available=False)
        self.make_donor("no_consent_donor", consent=False)
        self.make_donor("incompatible_donor", blood_type="B+")

        results = find_potential_donors(self.blood_request)
        donor_ids = [item["donor"].id for item in results]

        self.assertEqual(donor_ids, [eligible.id])

    def test_unverified_request_has_no_matches(self):
        self.blood_request.verified = False
        self.blood_request.save(update_fields=["verified"])

        self.assertEqual(
            find_potential_donors(self.blood_request),
            [],
        )
        self.assertEqual(create_matches(self.blood_request), [])

    def test_closed_request_has_no_new_matches(self):
        self.make_donor("closed_request_donor")

        self.blood_request.status = BloodRequest.Status.CLOSED
        self.blood_request.save(update_fields=["status"])

        self.assertEqual(create_matches(self.blood_request), [])
        self.assertEqual(
            Match.objects.filter(
                blood_request=self.blood_request
            ).count(),
            0,
        )

    def test_expired_request_has_no_new_matches(self):
        self.make_donor("expired_request_donor")

        self.blood_request.expires_at = (
            timezone.now() - timedelta(hours=1)
        )
        self.blood_request.save(update_fields=["expires_at"])

        self.assertEqual(create_matches(self.blood_request), [])
        self.assertEqual(
            Match.objects.filter(
                blood_request=self.blood_request
            ).count(),
            0,
        )

    def test_running_matching_twice_creates_no_duplicates(self):
        donor = self.make_donor("duplicate_test_donor")

        create_matches(self.blood_request)

        # Move the donor slightly to verify the saved distance refreshes.
        donor.latitude = 40.4
        donor.save(update_fields=["latitude"])

        create_matches(self.blood_request)

        matches = Match.objects.filter(
            blood_request=self.blood_request,
            donor=donor,
        )

        self.assertEqual(matches.count(), 1)
        self.assertGreater(matches.get().distance_km, 0)
