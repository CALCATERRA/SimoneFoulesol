import os
import json
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases

# ENV VARS
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
COLLECTION_ID = os.environ["COLLECTION_ID"]
APPWRITE_PROJECT_ID = os.environ["APPWRITE_PROJECT_ID"]
APPWRITE_API_KEY = os.environ["APPWRITE_API_KEY"]
APPWRITE_ENDPOINT = os.environ["APPWRITE_ENDPOINT"]

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
]

def send_telegram_photo(chat_id, photo_url):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data={
        "chat_id": chat_id,
        "photo": photo_url
    })

def send_telegram_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)

def get_user_document(db, chat_id):
    result = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[
        f'equal("chat_id", "{chat_id}")'
    ])
    documents = result["documents"]
    return documents[0] if documents else None

async def main(context):
    req = context.req
    res = context.res

    try:
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
    except:
        return res.json({"error": "Invalid JSON"}, 400)

    chat_id = str(body.get("chat_id", ""))
    if not chat_id:
        return res.json({"error": "chat_id mancante"}, 400)

    try:
        # Setup Appwrite client
        client = Client()
        client.set_endpoint(APPWRITE_ENDPOINT)
        client.set_project(APPWRITE_PROJECT_ID)
        client.set_key(APPWRITE_API_KEY)
        db = Databases(client)

        # Trova documento utente
        doc = get_user_document(db, chat_id)
        if not doc:
            return res.json({"error": "Utente non trovato"}, 404)

        document_id = doc["$id"]
        progressivo = doc.get("progressivo", 0)

        if progressivo >= len(PHOTO_IDS):
            send_telegram_message(chat_id, "Hai già ricevuto tutte le foto disponibili.")
            return res.json({"status": "completo"}, 200)

        # Invia la foto
        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[progressivo]}"
        send_telegram_photo(chat_id, photo_url)

        # Aggiorna progressivo
        new_progressivo = progressivo + 1
        db.update_document(DATABASE_ID, COLLECTION_ID, document_id, {
            "progressivo": new_progressivo
        })

        # Invia nuovo bottone PayPal se ci sono ancora foto
        if new_progressivo < len(PHOTO_IDS):
            paypal_link = f"https://www.paypal.com/pay?chat_id={chat_id}"
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "☕ Offrimi un altro caffè", "url": paypal_link}]
                ]
            }
            send_telegram_message(chat_id, "Grazie ❤️ Vuoi vedere la prossima foto esclusiva?", reply_markup)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        print("Errore:", str(e))
        return res.json({"error": str(e)}, 500)
