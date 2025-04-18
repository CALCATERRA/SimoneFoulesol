import os
import json
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ENV VARS
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
PAYPAL_CLIENT_ID = os.environ["PAYPAL_CLIENT_ID"]
PAYPAL_SECRET = os.environ["PAYPAL_SECRET"]
DATABASE_ID = os.environ["DATABASE_ID"]
COLLECTION_ID = os.environ["COLLECTION_ID"]
APPWRITE_PROJECT_ID = os.environ["APPWRITE_PROJECT_ID"]
APPWRITE_API_KEY = os.environ["APPWRITE_API_KEY"]
APPWRITE_ENDPOINT = os.environ["APPWRITE_ENDPOINT"]
NETLIFY_BASE_URL = os.environ["NETLIFY_BASE_URL"]  # Questo è l'URL base di Netlify

bot = Bot(token=TELEGRAM_TOKEN)

# Appwrite client setup
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

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
        "purchase_units": [{
            "amount": {"currency_code": "EUR", "value": str(amount)},
            "custom_id": str(chat_id)
        }],
        "application_context": {
            "return_url": f"{NETLIFY_BASE_URL}/?chat_id={chat_id}",
            "cancel_url": "https://t.me/FoulesolExclusive_bot"
        }
    }
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return next(link['href'] for link in res.json()['links'] if link['rel'] == 'approve')

def send_payment_link(chat_id):
    if not chat_id:
        return
    payment_link = create_payment_link(chat_id, 0.99)

    # Recupera documento utente
    try:
        user_data = db.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except:
        user_data = None

    if not user_data:
        db.create_document(DATABASE_ID, COLLECTION_ID, chat_id, {"photo_index": 0})

    keyboard = {
        "inline_keyboard": [
            [{"text": "💳 Paga 0,99€ per la prossima foto", "url": payment_link}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "☕ Offrimi un caffè su PayPal e ricevi la prossima foto esclusiva. Dopo il pagamento, torna qui!",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)

def send_photo(chat_id):
    try:
        user_data = db.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except Exception as e:
        return

    photo_index = user_data.get("photo_index", 0)

    # Se non ci sono foto da inviare
    if photo_index >= len(PHOTO_IDS):
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": chat_id,
            "text": "🎉 Hai visto tutte le foto disponibili! Grazie di cuore per il supporto. ❤️"
        })
        return

    # Invia foto (gestita da send_photo.py)
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": "Foto inviata! Premi il pulsante sotto per la prossima foto."}
    )

    # Aggiorna progressivo
    user_data["photo_index"] = photo_index + 1
    db.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)

    # Invia il pulsante PayPal per la prossima donazione
    send_payment_link(chat_id)

def handle_notify(data):
    chat_id = str(data.get("chat_id", ""))

    if not chat_id:
        return {"error": "chat_id mancante"}, 400

    try:
        # Recupera documento utente
        response = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[f'equal("chat_id", "{chat_id}")'])
        documents = response["documents"]
        if not documents:
            return {"error": "Utente non trovato"}, 404

        doc = documents[0]
        document_id = doc["$id"]
        progressivo = doc.get("progressivo", 0)

        if progressivo >= len(PHOTO_IDS):
            bot.send_message(chat_id=chat_id, text="Hai già ricevuto tutte le foto disponibili.")
            return {"status": "completo"}, 200

        # Invia messaggio di avanzamento
        bot.send_message(chat_id=chat_id, text="Foto inviata! Premi il pulsante per vedere la prossima.")

        # Aggiorna progressivo
        new_progressivo = progressivo + 1
        db.update_document(DATABASE_ID, COLLECTION_ID, document_id=document_id, data={"progressivo": new_progressivo})

        # Invia pulsante PayPal per prossima foto
        if new_progressivo < len(PHOTO_IDS):
            paypal_link = f"https://www.paypal.com/pay?chat_id={chat_id}"
            keyboard = [[InlineKeyboardButton("☕ Offrimi un altro caffè", url=paypal_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id=chat_id, text="Grazie ❤️ Vuoi vedere la prossima foto esclusiva?", reply_markup=reply_markup)

        return {"status": "ok"}, 200

    except Exception as e:
        print("Errore invio foto:", e)
        return {"error": str(e)}, 500

