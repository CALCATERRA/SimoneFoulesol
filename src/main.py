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

# Funzione per creare il link di pagamento PayPal
def create_payment_link(amount):
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
            "return_url": "https://your-server.com/payment_success",  # URL di ritorno
            "cancel_url": "https://your-server.com/payment_cancel"   # URL di annullamento
        }
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        approval_url = next(link['href'] for link in response.json()['links'] if link['rel'] == 'approve')
        return approval_url
    else:
        raise Exception(f"Error creating PayPal payment link: {response.text}")

# Funzione per inviare il link di pagamento su Telegram
def send_payment_link(chat_id):
    payment_link = create_payment_link(0.99)  # Sostituisci con l'importo della foto
    user_payments[chat_id] = {'payment_pending': True}  # Salva lo stato del pagamento
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
    response = requests.post(url, data=payload)
    print("send_payment_link:", response.status_code, response.text)

# Funzione per inviare la foto su Telegram
def send_photo(chat_id):
    if user_payments.get(chat_id, {}).get('payment_pending', False):
        # Verifica se il pagamento è stato completato
        user_payments[chat_id]['payment_pending'] = False  # Imposta il pagamento come completato
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": PHOTO_URL
        }
        response = requests.post(url, data=payload)
        print("send_photo:", response.status_code, response.text)
    else:
        # Se non c'è un pagamento in sospeso, non inviare la foto
        print("Pagamento non completato, non invio la foto.")

# Funzione per gestire il ritorno del pagamento e verificare lo stato del pagamento
async def payment_success(context):
    request = context.req
    response = context.res
    
    # Ottieni i parametri di ritorno da PayPal
    payment_id = request.query_params.get('paymentId')
    payer_id = request.query_params.get('PayerID')

    try:
        # Verifica che il pagamento sia stato completato
        if payment_id and payer_id:
            # Verifica lo stato del pagamento tramite PayPal
            token = get_paypal_token()
            url = f"https://api.sandbox.paypal.com/v2/checkout/orders/{payment_id}"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            payment_response = requests.get(url, headers=headers)

            if payment_response.status_code == 200:
                payment_data = payment_response.json()
                if payment_data['status'] == 'COMPLETED':
                    # Imposta lo stato del pagamento come completato
                    chat_id = request.query_params.get('chat_id')
                    if chat_id:
                        user_payments[chat_id] = {'payment_pending': False}

                        # Invia foto all'utente
                        send_photo(chat_id)
                        return response.json({"status": "success", "message": "Pagamento completato, la foto è stata inviata!"}, 200)
                else:
                    return response.json({"status": "error", "message": "Pagamento non completato."}, 400)
            else:
                return response.json({"status": "error", "message": "Errore nel recupero dei dettagli del pagamento."}, 400)
        else:
            return response.json({"status": "error", "message": "Dati del pagamento non validi."}, 400)
    
    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, 500)

# Funzione principale che gestisce i messaggi e le callback
async def main(context):
    request = context.req
    response = context.res

    try:
        print("Ricevuto request:", request.method, request.body)

        data = request.body  # ✅ già un dict in Appwrite
        print("Parsed JSON:", data)

        message = data.get("message")
        callback_query = data.get("callback_query")

        # Se è un messaggio classico
        if message:
            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            print("Chat ID:", chat_id)
            print("Text:", text)

            user = message.get("from", {})
            print(f"Utente: {user.get('first_name', '')} {user.get('last_name', '')} (@{user.get('username', '')})")

            if text == "/start":
                send_payment_link(chat_id)

        # Se è una callback del pulsante
        elif callback_query:
            chat_id = callback_query["message"]["chat"]["id"]
            data_value = callback_query.get("data")

            if data_value == "photo":
                send_photo(chat_id)

        return response.json({"status": "success"}, 200)

    except Exception as e:
        print("Errore:", str(e))
        return response.json({"status": "error", "message": str(e)}, 500)
