import requests
from django.conf import settings


def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url, json={"chat_id": chat_id, "text": message}, timeout=10
    )
    return response.json()


def notify_donor(match):
    donor = match.donor

    if not donor.telegram_chat_id:
        # Donor hasn't linked their Telegram account yet — see Step 6
        # below for how to get your own chat_id to test this manually.
        return False

    blood_request = match.blood_request

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

    try:
        send_telegram_message(donor.telegram_chat_id, message)
        return True
    except requests.exceptions.RequestException:
        # Network/Telegram unavailable — don't crash the whole
        # batch over one failed notification. The match record
        # still exists; it can be retried later.
        return False
