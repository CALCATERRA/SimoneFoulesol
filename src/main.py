import os
import json
import requests

# Configurazione
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
RETURN_URL = "https://calcaterra.github.io/paypal-return/paypal-return.html"
CANCEL_URL = "https://t.me/FoulesolExclusive_bot"

# Stato pagamenti utenti temporaneo (da sostituire con DB in produzione)
user_payments = {}

def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {"grant_type": "client_credentials"}

    res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    res.raise_for_status()
    return res.json()['access_token']

def create_payment_link(chat_id, amount):
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
                "amount": {"currency_code": "EUR", "value": str(amount)},
                "custom_id": str(chat_id)
            }
        ],
        "application_context": {
            "return_url": RETURN_URL,
            "cancel_url": CANCEL_URL
        }
    }

    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()

    for link in res.json()['links']:
        if link['rel'] == 'approve':
            return link['href']

    raise Exception("Approve link not found in PayPal response.")

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=payload)

def send_payment_link(chat_id):
    payment_link = create_payment_link(chat_id, 0.99)
    user_payments[chat_id] = {'payment_pending': True}

    keyboard = {
        "inline_keyboard": [
            [{"text": "💳 Paga 0,99€ con PayPal", "url": payment_link}]
        ]
    }

    message = (
        "Ciao 😘 clicca sul pulsante per offrirmi un caffè su PayPal. "
        "Dopo il pagamento, torna qui e premi *Guarda foto* per riceverla 😏"
    )
    send_message(chat_id, message, keyboard)

def send_view_photo_button(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "👀 Guarda foto", "callback_data": "photo"}]
        ]
    }
    send_message(chat_id, "Pagamento ricevuto! Premi qui sotto per vedere la foto 👇", keyboard)

def send_photo(chat_id):
    if not user_payments.get(chat_id, {}).get('payment_pending', True):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": PHOTO_URL
        }
        requests.post(url, data=payload)
    else:
        send_message(chat_id, "⚠️ Non risulta un pagamento completato. Riprova o attendi qualche secondo.")

def handle_paypal_ipn(request_data):
    verify_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    verify_payload = 'cmd=_notify-validate&' + request_data
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    res = requests.post(verify_url, headers=headers, data=verify_payload)

    if res.text == "VERIFIED":
        ipn = dict(x.split('=') for x in request_data.split('&') if '=' in x)
        payment_status = ipn.get("payment_status")
        chat_id = ipn.get("custom")

        if payment_status == "Completed" and chat_id:
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)

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
        return res.json({"status": "error", "message": str(e)}, 500)
