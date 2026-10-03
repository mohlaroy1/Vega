from django.contrib import admin

from .matching import create_matches
from .telegram import notify_donor
from .models import BloodRequest, DonorProfile, Match


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "blood_type",
        "city",
        "available",
        "last_donation_date",
        "consent",
    )
    list_filter = ("blood_type", "available", "consent", "city")
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        "hospital_name",
        "blood_type",
        "urgency",
        "status",
        "verified",
        "created_at",
        "expires_at",
    )
    list_filter = ("blood_type", "urgency", "status", "verified")

    actions = ["verify_and_match"]

    def verify_and_match(self, request, queryset):
        total_matches = 0
        total_notified = 0

        for blood_request in queryset:
            blood_request.verified = True
            blood_request.save(update_fields=["verified"])

            matches = create_matches(blood_request)
            total_matches += len(matches)

            for match in matches:
                if notify_donor(match):
                    total_notified += 1

        self.message_user(
            request,
            f"Verified {queryset.count()} request(s). "
            f"Created {total_matches} match(es). "
            f"Notified {total_notified} donor(s) via Telegram.",
        )

    verify_and_match.short_description = "Verify request and find matching donors"


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("blood_request", "donor", "distance_km", "status", "created_at")
    list_filter = ("status",)
