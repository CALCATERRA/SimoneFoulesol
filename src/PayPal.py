# paypal.py

import requests
from requests.auth import HTTPBasicAuth
import os

# Leggi le credenziali dal tuo ambiente (puoi usare dotenv)
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# Usa SANDBOX o LIVE a seconda dell'ambiente
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"


def get_paypal_token():
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "it_IT"
    }
    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data,
                             auth=HTTPBasicAuth(PAYPAL_CLIENT_ID, PAYPAL_SECRET))

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Errore token PayPal:", response.text)
        return None


def create_payment_link(access_token, telegram_user_id, photo_number):
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "EUR",
                "value": "0.99"
            },
            "custom_id": f"{telegram_user_id}_photo{photo_number}"
        }],
        "application_context": {
            "return_url": "https://t.me/tuobot?start=pagato",  # Modifica se hai webhook
            "cancel_url": "https://t.me/tuobot?start=annullato"
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        order = response.json()
        approval_url = next(link["href"] for link in order["links"] if link["rel"] == "approve")
        return approval_url
    else:
        print("Errore creazione ordine:", response.text)
        return None
