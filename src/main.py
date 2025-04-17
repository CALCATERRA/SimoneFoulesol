import json
import os
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
DATABASE_ID = os.environ.get("DATABASE_ID")
COLLECTION_ID = os.environ.get("COLLECTION_ID")

# Debug: stampa variabili per capire cosa manca
context.log("🔧 TELEGRAM_TOKEN:", "✅" if TELEGRAM_TOKEN else "❌ MANCANTE")
context.log("🔧 PAYPAL_CLIENT_ID:", "✅" if PAYPAL_CLIENT_ID else "❌ MANCANTE")
context.log("🔧 PAYPAL_SECRET:", "✅" if PAYPAL_SECRET else "❌ MANCANTE")
context.log("🔧 DATABASE_ID:", "✅" if DATABASE_ID else "❌ MANCANTE")
context.log("🔧 COLLECTION_ID:", "✅" if COLLECTION_ID else "❌ MANCANTE")
context.log("🔧 APPWRITE_ENDPOINT:", os.environ.get("APPWRITE_ENDPOINT") or "❌ MANCANTE")
context.log("🔧 APPWRITE_PROJECT_ID:", os.environ.get("APPWRITE_PROJECT_ID") or "❌ MANCANTE")
context.log("🔧 APPWRITE_API_KEY:", "✅" if os.environ.get("APPWRITE_API_KEY") else "❌ MANCANTE")

# Lista dei 100 ID di Google Drive
PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG", "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc", "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"  # ...continua fino a 100...
]

# Inizializzazione del client Appwrite
client = Client()
client.set_endpoint(os.environ.get("APPWRITE_ENDPOINT")).set_project(os.environ.get("APPWRITE_PROJECT_ID")).set_key(os.environ.get("APPWRITE_API_KEY"))
databases = Databases(client)

def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    res.raise_for_status()
    return res.json()['access_token']

def create_payment_link(chat_id, amount):
    token = get_paypal_token()
    url = "https://api.sandbox.paypal.com/v2/checkout/orders"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "EUR", "value": str(amount)},
            "custom_id": str(chat_id)
        }],
        "application_context": {
            "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
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
    
    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except Exception as e:
        print("❗ Errore durante il recupero dei dati dell'utente:", str(e))
        user_data = None

    if not user_data:
        databases.create_document(DATABASE_ID, COLLECTION_ID, chat_id, {"payment_pending": True, "photo_index": 0})
    else:
        user_data["payment_pending"] = True
        databases.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
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
    requests.post(url, data=payload)

def send_view_photo_button(chat_id):
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "📸 Guarda foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "❤️ Pagamento ricevuto! Premi per vedere la tua foto 👇",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

def send_photo(chat_id):
    if not chat_id:
        return
    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except Exception as e:
        print("❗ Errore durante il recupero dei dati dell'utente:", str(e))
        return

    if not user_data:
        print(f"❗ Nessun dato trovato per chat_id={chat_id}")
        return

    index = user_data.get('photo_index', 0)

    if index < len(PHOTO_IDS):
        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[index]}"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": photo_url}
        requests.post(url, data=payload)

        user_data['photo_index'] = index + 1
        user_data['payment_pending'] = None
        databases.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)

        if index + 1 < len(PHOTO_IDS):
            send_payment_link(chat_id)
        else:
            final_msg = {
                "chat_id": chat_id,
                "text": "🎉 Hai visto tutte le foto disponibili! Grazie di cuore per il supporto. ❤️"
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=final_msg)
    else:
        print(f"✅ Tutte le foto già inviate a chat_id={chat_id}")

async def main(context):
    req = context.req
    res = context.res

    try:
        content_type = req.headers.get("content-type", "")
        raw_body = req.body_raw if isinstance(req.body_raw, str) else req.body_raw.decode()

        try:
            data = req.body if isinstance(req.body, dict) else json.loads(req.body)
        except Exception as e:
            context.error("❗ JSON parsing error: " + str(e))
            return res.json({"status": "invalid json"}, 400)

        # Richiamo da Netlify dopo pagamento
        if data.get("source") == "manual-return":
            chat_id = data.get("chat_id")
            if chat_id:
                chat_id = str(chat_id)
                try:
                    user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
                    user_data['payment_pending'] = False
                    databases.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)
                    context.log(f"✅ Manual return completato per chat_id={chat_id}")
                    send_view_photo_button(chat_id)
                    return res.json({"status": "manual-return ok"}, 200)
                except Exception as e:
                    context.error("❗ Errore durante manual-return: " + str(e))
                    return res.json({"status": "manual-return error"}, 500)
            else:
                context.error("❗ chat_id mancante nel manual-return")
                return res.json({"status": "missing chat_id"}, 400)

        # Gestione messaggi Telegram
        message = data.get("message")
        callback = data.get("callback_query")

        if message:
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            if chat_id and text == "/start":
                chat_id = str(chat_id)
                context.log(f"📨 /start ricevuto da {chat_id}")
                send_payment_link(chat_id)

        elif callback:
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            data_callback = callback.get("data", "")
            if chat_id and data_callback == "photo":
                chat_id = str(chat_id)
                context.log(f"📸 Callback photo da {chat_id}")
                send_photo(chat_id)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        context.error("❗ Errore generale: " + str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
