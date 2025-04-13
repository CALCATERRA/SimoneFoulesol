import json
import os
import requests
from flask import Request

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"

# Memoria temporanea per lo stato dei pagamenti
user_payments = {}

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=payload)

def send_photo(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": PHOTO_URL
    }
    requests.post(url, data=payload)

def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    return response.json()['access_token']

def create_payment_link(chat_id):
    token = get_paypal_token()
    url = "https://api.sandbox.paypal.com/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "EUR",
                    "value": "0.99"
                },
                "custom_id": str(chat_id),
                "notify_url": "https://67f6d3471e1e1546c937.appwrite.global/"  # Tuo IPN handler
            }
        ],
        "application_context": {
            "return_url": "https://www.paypal.com/checkoutnow/error",  # Non usato
            "cancel_url": "https://www.paypal.com/checkoutnow/cancel"  # Non usato
        }
    }
    response = requests.post(url, headers=headers, json=data)
    approval_url = next(link['href'] for link in response.json()['links'] if link['rel'] == 'approve')
    return approval_url

async def main(context):
    req = context.req
    res = context.res

    try:
        data = req.body

        # 1. Messaggio Telegram
        if "message" in data:
            chat_id = str(data["message"]["chat"]["id"])
            text = data["message"].get("text", "")
            if text == "/start":
                payment_link = create_payment_link(chat_id)
                user_payments[chat_id] = {'paid': False}
                keyboard = {
                    "inline_keyboard": [[{"text": "Paga 0,99€ con PayPal", "url": payment_link}]]
                }
                send_telegram_message(chat_id, "Clicca sul pulsante per effettuare il pagamento:", keyboard)

        # 2. Callback Telegram
        elif "callback_query" in data:
            chat_id = str(data["callback_query"]["message"]["chat"]["id"])
            if data["callback_query"]["data"] == "photo":
                if user_payments.get(chat_id, {}).get("paid", False):
                    send_photo(chat_id)
                else:
                    send_telegram_message(chat_id, "Pagamento non trovato. Completa il pagamento con PayPal.")

        # 3. Notifica IPN da PayPal
        elif req.headers.get("user-agent", "").startswith("PayPal"):
            ipn_data = req.body
            chat_id = ipn_data.get("custom")
            payment_status = ipn_data.get("payment_status")

            if payment_status == "Completed" and chat_id:
                user_payments[chat_id] = {'paid': True}
                keyboard = {
                    "inline_keyboard": [[{"text": "Guarda foto", "callback_data": "photo"}]]
                }
                send_telegram_message(chat_id, "Pagamento ricevuto! Premi il pulsante per vedere la foto:", keyboard)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        return res.json({"status": "error", "message": str(e)}, 500)
