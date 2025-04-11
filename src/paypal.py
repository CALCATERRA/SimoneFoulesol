import os
import requests
from dotenv import load_dotenv

load_dotenv()

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com"


def get_paypal_token():
    url = f"{PAYPAL_API_BASE}/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET)
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print("Errore nel recupero del token PayPal:", str(e))
        return None


def create_payment_link(access_token, telegram_user_id, photo_number):
    url = f"{PAYPAL_API_BASE}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": f"user_{telegram_user_id}_photo_{photo_number}",
            "amount": {
                "currency_code": "EUR",
                "value": "0.99"
            }
        }],
        "application_context": {
            "return_url": "https://t.me/IlTuoBot",  # ← Puoi cambiarlo
            "cancel_url": "https://t.me/IlTuoBot"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        order = response.json()
        approval_link = next(link["href"] for link in order["links"] if link["rel"] == "approve")
        return approval_link
    except Exception as e:
        print("Errore nella creazione dell’ordine PayPal:", str(e))
        return None