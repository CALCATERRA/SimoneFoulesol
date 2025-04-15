import json
import os
import requests

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://i.imgur.com/tIcTyUK.jpg"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# Stato utenti (runtime)
user_payments = {}

# 🔐 Access token da PayPal
def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    res.raise_for_status()
    return res.json()['access_token']

# 💳 Crea link pagamento PayPal
def create_payment_link(chat_id, amount):
    token = get_paypal_token()
    url = "https://api.sandbox.paypal.com/v2/checkout/orders"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "EUR", "value": str(amount)},
            "custom_id": str(chat_id),
            "notify_url": "https://67fd01767b6cc3ff6cc6.appwrite.global/v1/functions/67fd0175002fa4a735c4/executions"
        }],
        "application_context": {
            "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
            "cancel_url": "https://t.me/FoulesolExclusive_bot"
        }
    }
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return next(link['href'] for link in res.json()['links'] if link['rel'] == 'approve')

# 📩 Invia link pagamento
def send_payment_link(chat_id):
    payment_link = create_payment_link(chat_id, 0.99)
    user_payments[chat_id] = {'payment_pending': True}
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Paga 0,99€ con PayPal", "url": payment_link}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": (
            "Ciao 😘 clicca sul pulsante per offrirmi un caffè su PayPal. "
            "Dopo il pagamento, torna qui e premi *Guarda foto* per riceverla 😏"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

# 👁 Invia pulsante per vedere la foto
def send_view_photo_button(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Guarda foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Pagamento ricevuto! Premi qui sotto per vedere la foto 👇",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

# 📷 Invia foto se autorizzato
def send_photo(chat_id):
    if user_payments.get(chat_id, {}).get('payment_pending') is False:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": PHOTO_URL}
        requests.post(url, data=payload)
    else:
        print(f"⚠️ Accesso non autorizzato alla foto per chat_id: {chat_id}")

# 🔁 IPN PayPal
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

# 🧠 Funzione Appwrite principale
async def main(context):
    req = context.req
    res = context.res

    try:
        content_type = req.headers.get("content-type", "")
        raw_body = req.body_raw if isinstance(req.body_raw, str) else req.body_raw.decode()

        # ✉️ IPN PayPal
        if "application/x-www-form-urlencoded" in content_type:
            handle_paypal_ipn(raw_body)
            return res.json({"status": "IPN processed"}, 200)

        # 🧩 JSON sicuro
        try:
            data = req.body if isinstance(req.body, dict) else json.loads(req.body)
        except Exception as e:
            print("❗ JSON parsing error:", str(e))
            return res.json({"status": "invalid json"}, 400)

        # 🔔 Chiamata manuale da Netlify
        if data.get("source") == "manual-return" and data.get("chat_id"):
            chat_id = str(data["chat_id"])
            print(f"✅ Notifica manuale ricevuta per chat_id={chat_id}")
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)
            return res.json({"status": "manual-return ok"}, 200)

        # 📬 Messaggi Telegram
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
        print("❗ Errore:", str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
