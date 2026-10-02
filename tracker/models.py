from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class BloodType(models.TextChoices):
    A_POSITIVE = "A+", "A+"
    A_NEGATIVE = "A-", "A-"
    B_POSITIVE = "B+", "B+"
    B_NEGATIVE = "B-", "B-"
    AB_POSITIVE = "AB+", "AB+"
    AB_NEGATIVE = "AB-", "AB-"
    O_POSITIVE = "O+", "O+"
    O_NEGATIVE = "O-", "O-"


class DonorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="donor_profile"
    )
    blood_type = models.CharField(max_length=3, choices=BloodType.choices)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    available = models.BooleanField(default=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True)
    consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.blood_type}"


class BloodRequest(models.Model):

    class Urgency(models.TextChoices):
        NORMAL = "normal", _("Oddiy")
        URGENT = "urgent", _("Shoshilinch")
        CRITICAL = "critical", _("Kritik")

    class Status(models.TextChoices):
        OPEN = "open", _("Ochiq")
        MATCHED = "matched", _("Moslashtirilgan")
        CLOSED = "closed", _("Yopiq")
        EXPIRED = "expired", _("Muddati tugagan")

    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blood_requests"
    )
    blood_type = models.CharField(max_length=3, choices=BloodType.choices)
    hospital_name = models.CharField(max_length=200)
    hospital_address = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    urgency = models.CharField(
        max_length=20, choices=Urgency.choices, default=Urgency.NORMAL
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blood_type} - {self.hospital_name}"


class Match(models.Model):

    class Status(models.TextChoices):
        NOTIFIED = "notified", _("Xabar berildi")
        RESPONDED = "responded", _("Javob berdi")
        DECLINED = "declined", _("Rad etdi")

    blood_request = models.ForeignKey(
        BloodRequest, on_delete=models.CASCADE, related_name="matches"
    )
    donor = models.ForeignKey(
        DonorProfile, on_delete=models.CASCADE, related_name="matches"
    )
    distance_km = models.FloatField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOTIFIED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blood_request", "donor")

    def __str__(self):
        return f"{self.donor} -> {self.blood_request}"
