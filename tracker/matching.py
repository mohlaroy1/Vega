from math import atan2, cos, radians, sin, sqrt

from django.utils import timezone

from .models import DonorProfile, Match


def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1 = radians(lat1)
    lat2 = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def find_potential_donors(blood_request):
    # Nothing happens until a human (you, via admin) verifies the
    # request. This is the safety gate — never remove this check.
    if not blood_request.verified:
        return []

    # An expired request shouldn't match either, even if re-run.
    if blood_request.expires_at <= timezone.now():
        return []

    donors = DonorProfile.objects.filter(
        blood_type=blood_request.blood_type,
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
