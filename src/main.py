import json
import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# In memoria, utile per test
user_payments = {}

# Recupera access token PayPal
def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    return response.json()['access_token']

# Crea ordine PayPal
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
                },
                "custom_id": str(chat_id)
            }
        ],
        "application_context": {
            "return_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        approval_url = next(link['href'] for link in response.json()['links'] if link['rel'] == 'approve')
        order_id = response.json()["id"]
        user_payments[chat_id] = {
            'payment_pending': True,
            'order_id': order_id
        }
        return approval_url
    else:
        raise Exception(f"Errore creazione pagamento PayPal: {response.text}")

# Invia il link di pagamento
def send_payment_link(chat_id):
    payment_link = create_payment_link(chat_id, 0.99)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Paga 0,99€ con PayPal", "url": payment_link}],
            [{"text": "Guarda foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Clicca sul bottone per pagare con PayPal. Dopo il pagamento, premi *Guarda foto* per riceverla.",
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

# Invia la foto se il pagamento è valido
def send_photo(chat_id):
    order_info = user_payments.get(chat_id)
    if not order_info:
        send_text(chat_id, "Nessun pagamento trovato. Premi /start per iniziare.")
        return

    order_id = order_info.get("order_id")
    if not order_id:
        send_text(chat_id, "Errore interno: ID pagamento mancante.")
        return

    token = get_paypal_token()
    url = f"https://api.sandbox.paypal.com/v2/checkout/orders/{order_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        status = response.json().get("status")
        if status == "COMPLETED":
            user_payments[chat_id]['payment_pending'] = False
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data={
                "chat_id": chat_id,
                "photo": PHOTO_URL
            })
        else:
            send_text(chat_id, "Pagamento non ancora completato. Riprova tra qualche secondo.")
    else:
        send_text(chat_id, f"Errore verifica pagamento: {response.text}")

# Invia un semplice testo
def send_text(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
        "chat_id": chat_id,
        "text": text
    })

# Entrypoint principale
async def main(context):
    request = context.req
    response = context.res

    try:
        data = request.body
        message = data.get("message")
        callback_query = data.get("callback_query")

        if message:
            chat_id = str(message["chat"]["id"])
            if message.get("text") == "/start":
                send_payment_link(chat_id)

        elif callback_query:
            chat_id = str(callback_query["message"]["chat"]["id"])
            data_value = callback_query.get("data")
            if data_value == "photo":
                send_photo(chat_id)

        return response.json({"status": "ok"}, 200)

    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)
