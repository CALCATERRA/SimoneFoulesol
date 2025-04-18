import os
import json
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases

# ENV
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
COLLECTION_ID = os.environ["COLLECTION_ID"]
APPWRITE_PROJECT_ID = os.environ["APPWRITE_PROJECT_ID"]
APPWRITE_API_KEY = os.environ["APPWRITE_API_KEY"]
APPWRITE_ENDPOINT = os.environ["APPWRITE_ENDPOINT"]

# Costanti
PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
]

# Appwrite client
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

def main(context):
    try:
        body = json.loads(context.req.body)
        chat_id = str(body.get("chat_id", ""))
        if not chat_id:
            context.res.send(json.dumps({"error": "chat_id mancante"}), 400)
            return  # 🔹 Return obbligatorio dopo send

        context.res.send(json.dumps({"status": "ricevuto"}), 200)  # Risposta immediata
        return  # 🔹 Return obbligatorio dopo send

        # ⚠️ Questo non verrà mai eseguito a causa del return sopra
        process_photo_send(chat_id)

    except Exception as e:
        print("Errore iniziale:", e)
        context.res.send(json.dumps({"error": str(e)}), 500)
        return  # 🔹 Return obbligatorio dopo send

def process_photo_send(chat_id):
    try:
        # Estrai documento utente
        res = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[
            f'equal("chat_id", "{chat_id}")'
        ])
        docs = res["documents"]
        if not docs:
            print("Utente non trovato.")
            return

        doc = docs[0]
        document_id = doc["$id"]
        progressivo = doc.get("progressivo", 0)

        if progressivo >= len(PHOTO_IDS):
            send_message(chat_id, "Hai già ricevuto tutte le foto disponibili.")
            return

        # Invia la foto
        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[progressivo]}"
        send_photo(chat_id, photo_url)

        # Aggiorna progressivo
        db.update_document(DATABASE_ID, COLLECTION_ID, document_id=document_id, data={
            "progressivo": progressivo + 1
        })

        # Invia bottone per prossima foto
        if progressivo + 1 < len(PHOTO_IDS):
            paypal_url = f"https://www.paypal.com/pay?chat_id={chat_id}"
            button_text = "☕ Offrimi un altro caffè"
            message = "Grazie ❤️ Vuoi vedere la prossima foto esclusiva?"
            send_button(chat_id, message, button_text, paypal_url)

    except Exception as e:
        print("Errore invio/processo:", e)

# 🔹 Funzioni Telegram base (via HTTP)
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_photo(chat_id, photo_url):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
        json={"chat_id": chat_id, "photo": photo_url}
    )

def send_button(chat_id, message, button_text, url):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "reply_markup": {
                "inline_keyboard": [[{"text": button_text, "url": url}]]
            }
        }
    )
