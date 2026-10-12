from math import atan2, cos, radians, sin, sqrt

from django.utils import timezone

from .models import DonorProfile, Match


# Preliminary red blood cell donor compatibility.
# Clinical staff must confirm compatibility before transfusion.
COMPATIBLE_DONORS = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}


def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    a = max(0, min(1, a))
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def find_potential_donors(blood_request):
    # Nothing happens until a human (you, via admin) verifies the
    # request. This is the safety gate — never remove this check.
    if not blood_request.verified or not is_request_active(blood_request):
        return []

    compatible_types = COMPATIBLE_DONORS.get(
        blood_request.blood_type, []
    )

    donors = DonorProfile.objects.filter(
        blood_type__in=compatible_types,
        available=True,
        consent=True,
        latitude__isnull=False,
        longitude__isnull=False,
    )

    results = []
    for donor in donors:
        distance = calculate_distance(
            blood_request.latitude,
            blood_request.longitude,
            donor.latitude,
            donor.longitude,
        )
        if distance <= 50:
            results.append({"donor": donor, "distance_km": round(distance, 2)})

    results.sort(key=lambda item: item["distance_km"])
    return results


def create_matches(blood_request):
    potential_donors = find_potential_donors(blood_request)
    matches = []

    for item in potential_donors:
        donor = item["donor"]
        distance = item["distance_km"]

        match, _ = Match.objects.update_or_create(
            blood_request=blood_request,
            donor=donor,
            defaults={"distance_km": distance},
        )
        matches.append(match)

    return matches


def is_request_active(blood_request):
    return (
        blood_request.status == blood_request.Status.OPEN
        and blood_request.expires_at > timezone.now()
    )
