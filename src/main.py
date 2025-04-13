import json
import os
import requests

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# Stato utente (nota: in memoria, non persiste su Appwrite)
user_payments = {}

# Ottieni token PayPal
def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    response.raise_for_status()
    return response.json()['access_token']

# Crea link PayPal con redirect verso funzione Appwrite
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
                "amount": {
                    "currency_code": "EUR",
                    "value": str(amount)
                }
            }
        ],
        "application_context": {
            "return_url": f"https://cloud.appwrite.io/v1/functions/67f6d345003e6da67d40/executions?chat_id={chat_id}",
            "cancel_url": f"https://cloud.appwrite.io/v1/functions/67f6d345003e6da67d40/executions?cancelled=true&chat_id={chat_id}"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    approval_url = next(link['href'] for link in response.json()['links'] if link['rel'] == 'approve')
    return approval_url

# Invia link pagamento
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
            "Ciao😘 per visualizzare la foto esclusiva, clicca sul pulsante qui sotto per un caffè su PayPal. "
            "Dopo il pagamento, torna qui e premi *Guarda foto* per ricevere la foto😏"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

# Pulsante per guardare la foto
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

# Invia la foto
def send_photo(chat_id):
    if user_payments.get(chat_id, {}).get('payment_pending') is False:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": PHOTO_URL
        }
        requests.post(url, data=payload)
    else:
        print(f"⚠️ Pagamento non completato per chat_id {chat_id}")

# Entry point per Appwrite
async def main(context):
    request = context.req
    response = context.res

    try:
        # PAYPAL REDIRECT?
        query = request.query_params
        if "paymentId" in query and "PayerID" in query:
            payment_id = query["paymentId"]
            payer_id = query["PayerID"]
            chat_id = query.get("chat_id")

            token = get_paypal_token()
            order_url = f"https://api.sandbox.paypal.com/v2/checkout/orders/{payment_id}"
            headers = {"Authorization": f"Bearer {token}"}
            payment_response = requests.get(order_url, headers=headers)

            if payment_response.status_code == 200:
                payment_data = payment_response.json()
                if payment_data.get("status") == "COMPLETED" and chat_id:
                    user_payments[chat_id] = {'payment_pending': False}
                    send_view_photo_button(chat_id)
                    return response.json({"status": "success", "message": "Pagamento ricevuto"}, 200)
                else:
                    return response.json({"status": "incomplete", "message": "Pagamento non completato"}, 400)
            else:
                return response.json({"status": "error", "message": "Errore nella verifica pagamento"}, 400)

        # TELEGRAM MESSAGGIO NORMALE
        body = request.body
        message = body.get("message")
        callback_query = body.get("callback_query")

        if message:
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            if text == "/start":
                send_payment_link(chat_id)

        elif callback_query:
            chat_id = str(callback_query["message"]["chat"]["id"])
            if callback_query.get("data") == "photo":
                send_photo(chat_id)

        return response.json({"status": "ok"}, 200)

    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)
