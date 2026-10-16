
import requests
from django.conf import settings

from .matching import is_request_active
from .models import Match


def send_telegram_message(chat_id, message):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)

    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError):
        return False

    return data.get("ok") is True


def notify_donor(match):
    blood_request = match.blood_request
    donor = match.donor

    # Notify only for verified, active requests and new notifications.
    if not blood_request.verified or not is_request_active(blood_request):
        return False

    if match.status != Match.Status.NOTIFIED or match.telegram_notified:
        return False

    if not donor.telegram_chat_id:
        return False

    message = (
        "Vega — Qon so'rovi\n\n"
        f"Qon guruhi: {blood_request.blood_type}\n"
        f"Shifoxona: {blood_request.hospital_name}\n"
        f"Masofa: {match.distance_km} km\n"
        f"Shoshilinchlik: {blood_request.get_urgency_display()}\n\n"
        "Siz mos donor bo'lishingiz mumkin.\n"
        "Donorlik uchun mos ekanligingizni tibbiy xodimlar "
        "tasdiqlashi kerak. Iltimos, qon markaziga murojaat qiling."
    )

    if not send_telegram_message(donor.telegram_chat_id, message):
        return False

    match.telegram_notified = True
    match.save(update_fields=["telegram_notified"])
    return True
