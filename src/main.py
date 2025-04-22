# main.py

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
    try:
        print("[init_appwrite_client] Inizializzazione client Appwrite.")
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        return Databases(client)
    except Exception as e:
        print(f"[init_appwrite_client] Errore: {e}")
        raise RuntimeError("Errore inizializzazione client Appwrite")

def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    try:
        print("[get_paypal_token] Richiesta token PayPal...")
        res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
        res.raise_for_status()
        token = res.json().get('access_token')
        if not token:
            raise ValueError("Token PayPal mancante nella risposta.")
        print("[get_paypal_token] Token ottenuto con successo.")
        return token
    except requests.RequestException as e:
        print(f"[get_paypal_token] Richiesta fallita: {e}")
        raise
    except Exception as e:
        print(f"[get_paypal_token] Errore generico: {e}")
        raise

def create_payment_link(chat_id, amount):
    try:
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
                "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
                "cancel_url": "https://t.me/FoulesolExclusive_bot"
            }
        }
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()
        approval_link = next(link['href'] for link in res.json().get('links', []) if link['rel'] == 'approve')
        print(f"[create_payment_link] Link approvazione creato: {approval_link}")
        return approval_link
    except (requests.RequestException, KeyError, StopIteration) as e:
        print(f"[create_payment_link] Errore creazione link: {e}")
        raise

def send_payment_link(chat_id, databases):
    if not chat_id:
        print("[send_payment_link] Chat ID mancante.")
        return

    try:
        payment_link = create_payment_link(chat_id, 0.99)
    except Exception as e:
        print(f"[send_payment_link] Errore PayPal: {e}")
        return

    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, str(chat_id))
        print(f"[send_payment_link] Documento utente esistente.")
    except Exception as e:
        print(f"[send_payment_link] Documento non trovato. Provo a crearne uno. Errore: {e}")
        try:
            databases.create_document(DATABASE_ID, COLLECTION_ID, str(chat_id), {"photo_index": 0})
            print("[send_payment_link] Documento creato.")
        except Exception as ce:
            print(f"[send_payment_link] Errore creazione documento: {ce}")
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
        response.raise_for_status()
        print("[send_payment_link] Messaggio Telegram inviato con successo.")
    except requests.RequestException as e:
        print(f"[send_payment_link] Errore invio messaggio Telegram: {e}")

def send_view_photo_button(chat_id, photo_number):
    try:
        keyboard = {
            "inline_keyboard": [
                [{"text": f"📸 Guarda foto {photo_number}", "callback_data": "photo"}]
            ]
        }
        payload = {
            "chat_id": chat_id,
            "text": "❤️ Pagamento ricevuto! Premi per vedere la tua foto 👇",
            "reply_markup": json.dumps(keyboard)
        }
        res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"[send_view_photo_button] Errore invio bottone: {e}")

def send_photo(chat_id, databases):
    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, str(chat_id))
        photo_index = user_data.get("photo_index", 0)
        print(f"[send_photo] Indice foto corrente: {photo_index}")

        if photo_index >= len(PHOTO_IDS):
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                "chat_id": chat_id,
                "text": "🎉 Hai visto tutte le foto disponibili! Grazie di cuore per il supporto. ❤️"
            })
            return

        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[photo_index]}"
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            data={"chat_id": chat_id, "photo": photo_url}
        )

        user_data["photo_index"] = photo_index + 1
        databases.update_document(DATABASE_ID, COLLECTION_ID, str(chat_id), user_data)
        print(f"[send_photo] Aggiornato photo_index a {photo_index + 1}")

        if photo_index + 1 < len(PHOTO_IDS):
            send_payment_link(chat_id, databases)

    except Exception as e:
        print(f"[send_photo] Errore invio o aggiornamento foto: {e}")

async def main(context):
    req = context.req
    res = context.res
    print("[main] Funzione avviata.")

    try:
        databases = init_appwrite_client()
    except Exception as e:
        return res.json({"status": "error", "message": str(e)}, 500)

    try:
        data = req.body if isinstance(req.body, dict) else json.loads(req.body)
        print(f"[main] Dati ricevuti: {data}")
    except Exception as e:
        print(f"[main] Errore parsing JSON: {e}")
        return res.json({"status": "invalid json", "message": str(e)}, 400)

    if data.get("source") == "manual-return":
        chat_id = str(data.get("chat_id"))
        if not chat_id:
            return res.json({"status": "missing chat_id"}, 400)

        try:
            user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
            photo_index = user_data.get("photo_index", 0)
            send_view_photo_button(chat_id, photo_index + 1)
            return res.json({"status": "manual-return ok"}, 200)
        except Exception as e:
            print(f"[main] Errore manual-return: {e}")
            return res.json({"status": "manual-return error", "message": str(e)}, 500)

    message = data.get("message")
    callback = data.get("callback_query")

    if message:
        chat_id = str(message.get("chat", {}).get("id"))
        text = message.get("text", "")
        if chat_id and text == "/start":
            send_payment_link(chat_id, databases)

    elif callback:
        chat_id = str(callback.get("message", {}).get("chat", {}).get("id"))
        callback_id = callback.get("id")
        callback_data = callback.get("data", "")

        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
                data={"callback_query_id": callback_id}
            )
        except Exception as e:
            print(f"[main] Errore callback query: {e}")

        if chat_id and callback_data == "photo":
            send_photo(chat_id, databases)
            return res.json({"status": "photo sent"}, 200)

    print("[main] Fine esecuzione normale.")
    return res.json({"status": "ok"}, 200)
