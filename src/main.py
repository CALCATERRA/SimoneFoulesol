import json
import os
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
DATABASE_ID = os.environ.get("DATABASE_ID")
COLLECTION_ID = os.environ.get("COLLECTION_ID")
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
]

def init_appwrite_client():
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    return Databases(client)

def get_paypal_token(context):
    context.log("[get_paypal_token] Richiesta token PayPal...")
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {"grant_type": "client_credentials"}
    try:
        res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
        res.raise_for_status()
        context.log("[get_paypal_token] Token ottenuto con successo.")
        return res.json()['access_token']
    except Exception as e:
        context.error(f"[get_paypal_token] Errore: {e}")
        raise

def create_payment_link(chat_id, amount, context):
    context.log(f"[create_payment_link] Creazione link pagamento per chat_id={chat_id}...")
    token = get_paypal_token(context)
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
            "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
            "cancel_url": "https://t.me/FoulesolExclusive_bot"
        }
    }
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()
        approval_link = next(link['href'] for link in res.json()['links'] if link['rel'] == 'approve')
        context.log(f"[create_payment_link] Link approvazione creato: {approval_link}")
        return approval_link
    except Exception as e:
        context.error(f"[create_payment_link] Errore: {e}")
        raise

def send_payment_link(chat_id, databases, context):
    context.log(f"[send_payment_link] Avvio per chat_id={chat_id}")
    if not chat_id:
        context.error("[send_payment_link] Chat ID mancante.")
        return
    try:
        payment_link = create_payment_link(chat_id, 0.99, context)
    except Exception as e:
        context.error(f"[send_payment_link] Errore creazione link PayPal: {e}")
        return

    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, str(chat_id))
        context.log(f"[send_payment_link] Documento utente esistente: {user_data}")
    except Exception as e:
        context.error(f"[send_payment_link] Documento non trovato. Errore: {e}")
        try:
            databases.create_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                document_id=str(chat_id),
                data={"photo_index": 0}
            )
            context.log("[send_payment_link] Documento creato.")
        except Exception as e:
            context.error(f"[send_payment_link] Errore creazione documento: {e}")
            return

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
    try:
        response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)
        context.log(f"[send_payment_link] Messaggio Telegram inviato. Status: {response.status_code}")
    except Exception as e:
        context.error(f"[send_payment_link] Errore invio messaggio Telegram: {e}")

# Il resto della funzione `main` (incluso send_photo e send_view_photo_button) non cambia a livello di logging, 
# ma se vuoi li aggiorno tutti allo stesso stile.
# Fammi sapere se vuoi anche il resto del file aggiornato con context.log/error, oppure solo questa parte.

async def main(context):
    req = context.req
    res = context.res

    context.log("[main] Funzione avviata.")
    databases = init_appwrite_client()

    try:
        data = req.body if isinstance(req.body, dict) else json.loads(req.body)
        context.log(f"[main] Dati ricevuti: {data}")
    except Exception as e:
        context.error(f"[main] Errore parsing JSON: {e}")
        return res.json({"status": "invalid json"}, 400)

    if data.get("source") == "manual-return":
        chat_id = str(data.get("chat_id"))
        context.log(f"[main] Callback manual-return per chat_id={chat_id}")
        if chat_id:
            try:
                user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
                photo_index = user_data.get("photo_index", 0)
                send_view_photo_button(chat_id, photo_index + 1)
                return res.json({"status": "manual-return ok"}, 200)
            except Exception as e:
                context.error(f"[main] Errore manual-return: {e}")
                return res.json({"status": "manual-return error", "message": str(e)}, 500)
        else:
            context.error("[main] chat_id mancante in manual-return.")
            return res.json({"status": "missing chat_id"}, 400)

    message = data.get("message")
    callback = data.get("callback_query")

    if message:
        chat_id = str(message.get("chat", {}).get("id"))
        text = message.get("text", "")
        context.log(f"[main] Messaggio ricevuto da chat_id={chat_id}, testo={text}")
        if chat_id and text == "/start":
            send_payment_link(chat_id, databases, context)

    elif callback:
        chat_id = str(callback.get("message", {}).get("chat", {}).get("id"))
        callback_id = callback.get("id")
        callback_data = callback.get("data", "")
        context.log(f"[main] Callback ricevuto da chat_id={chat_id}, data={callback_data}")

        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                data={"callback_query_id": callback_id}
            )
        except Exception as e:
            context.error(f"[main] Errore risposta callback query: {e}")

        if chat_id and callback_data == "photo":
            send_photo(chat_id, databases)
            return res.json({"status": "photo sent"}, 200)

    context.log("[main] Fine esecuzione normale.")
    return res.json({"status": "ok"}, 200)
