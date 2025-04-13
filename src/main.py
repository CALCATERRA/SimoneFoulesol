import json
import os
import requests
from urllib.parse import parse_qs

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# Stato utenti
user_payments = {}

def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    if res.status_code == 200:
        return res.json()['access_token']
    else:
        raise Exception(f"PayPal token error: {res.text}")

def create_payment_link(chat_id, amount):
    token = get_paypal_token()
    url = "https://api.sandbox.paypal.com/v2/checkout/orders"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": "EUR", "value": str(amount)},
                "custom_id": str(chat_id),
                "notify_url": "https://67f6d3471e1e1546c937.appwrite.global/v1/functions/67f6d345003e6da67d40/executions"
            }
        ],
        "application_context": {
            "return_url": "https://t.me/FoulesolExclusive_bot",
            "cancel_url": "https://t.me/FoulesolExclusive_bot"
        }
    }
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 201:
        return next(link['href'] for link in res.json()['links'] if link['rel'] == 'approve')
    else:
        raise Exception(f"PayPal create payment error: {res.text}")

def send_payment_link(chat_id):
    payment_link = create_payment_link(chat_id, 0.99)
    user_payments[chat_id] = {'payment_pending': True}

    # Invia messaggio con link PayPal
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Paga 0,99€ con PayPal", "url": payment_link}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": (
            "Ciao 😘 clicca sul pulsante per offrirmi un caffè su PayPal.\n"
            "Dopo il pagamento, torna qui e premi *Guarda foto* per riceverla 😏"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print("Telegram error (payment link):", r.text)

    # Invia subito il pulsante "Guarda foto"
    send_view_photo_button(chat_id)

def send_view_photo_button(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Guarda foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Dopo il pagamento, premi qui sotto per vedere la foto 👇",
        "reply_markup": json.dumps(keyboard)
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print("Telegram error (view button):", r.text)

def send_photo(chat_id):
    if not user_payments.get(chat_id):
        user_payments[chat_id] = {'payment_pending': True}

    if user_payments[chat_id]['payment_pending'] is False:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": PHOTO_URL
        }
        r = requests.post(url, data=payload)
        if r.status_code != 200:
            print("Telegram error (send photo):", r.text)
    else:
        print(f"Pagamento non completato per chat_id {chat_id}")

# Gestione IPN PayPal
def handle_paypal_ipn(request_data):
    verify_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    verify_payload = 'cmd=_notify-validate&' + request_data
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(verify_url, headers=headers, data=verify_payload)

    if res.text == "VERIFIED":
        ipn = {k: v[0] for k, v in parse_qs(request_data).items()}
        payment_status = ipn.get("payment_status")
        chat_id = ipn.get("custom")

        if payment_status == "Completed" and chat_id:
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)
        else:
            print("Pagamento non completato o chat_id mancante.")
    else:
        print("IPN non verificato:", res.text)

# Funzione principale Appwrite
async def main(context):
    req = context.req
    res = context.res

    try:
        content_type = req.headers.get("content-type", "")
        if content_type == "application/x-www-form-urlencoded":
            raw_body = req.body_raw.decode()
            handle_paypal_ipn(raw_body)
            return res.json({"status": "IPN received"}, 200)

        data = req.body
        message = data.get("message")
        callback = data.get("callback_query")

        if message:
            chat_id = str(message["chat"]["id"])
            if message.get("text") == "/start":
                send_payment_link(chat_id)

        elif callback:
            chat_id = str(callback["message"]["chat"]["id"])
            if callback.get("data") == "photo":
                send_photo(chat_id)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        print("Errore:", str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
