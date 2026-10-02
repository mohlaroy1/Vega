from django.contrib import admin

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


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("blood_request", "donor", "distance_km", "status", "created_at")
    list_filter = ("status",)
