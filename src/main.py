import json
import os
import requests

# Configurazione variabili
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# Per tracciare lo stato del pagamento
user_payments = {}

# Funzione per ottenere il token di PayPal
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
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error getting PayPal token: {response.text}")

# Funzione per gestire la notifica IPN di PayPal
def handle_ipn(request_data):
    # Verifica che la notifica IPN sia valida
    if request_data.get('payment_status') == 'Completed':
        chat_id = request_data.get('custom_id')
        if chat_id and chat_id in user_payments:
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)
            return {"status": "success", "message": "Pagamento completato, premi per vedere la foto"}
    return {"status": "error", "message": "Pagamento non completato"}

# Funzione per inviare il link di pagamento a PayPal
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

# Funzione per inviare il pulsante per visualizzare la foto
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

# Funzione per inviare la foto su Telegram
def send_photo(chat_id):
    if user_payments.get(chat_id, {}).get('payment_pending', False) is False:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": PHOTO_URL
        }
        requests.post(url, data=payload)
    else:
        print("Pagamento non completato, non invio la foto.")

# Gestisce ritorno pagamento da PayPal (callback per IPN)
async def payment_success(context):
    request = context.req
    response = context.res
    try:
        request_data = request.body
        result = handle_ipn(request_data)  # Gestisci la risposta IPN
        return response.json(result, 200)
    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)

# Funzione principale che gestisce i messaggi e le callback
async def main(context):
    request = context.req
    response = context.res

    try:
        data = request.body
        message = data.get("message")
        callback_query = data.get("callback_query")

        if message:
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            if text == "/start":
                send_payment_link(chat_id)

        elif callback_query:
            chat_id = str(callback_query["message"]["chat"]["id"])
            data_value = callback_query.get("data")
            if data_value == "photo":
                send_photo(chat_id)

        return response.json({"status": "success"}, 200)

    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)
