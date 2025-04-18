import os
import json
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ENV VARS
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
COLLECTION_ID = os.environ["COLLECTION_ID"]
APPWRITE_PROJECT_ID = os.environ["APPWRITE_PROJECT_ID"]
APPWRITE_API_KEY = os.environ["APPWRITE_API_KEY"]
APPWRITE_ENDPOINT = os.environ["APPWRITE_ENDPOINT"]

bot = Bot(token=TELEGRAM_TOKEN)

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
]

# Appwrite client setup
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

def main(context):
    try:
        payload = json.loads(context.req.body)
        chat_id = str(payload.get("chat_id", ""))

        if not chat_id:
            return context.res.json({"error": "chat_id mancante"}, 400)

        # Recupera documento utente
        response = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[
            f'equal("chat_id", "{chat_id}")'
        ])
        documents = response["documents"]
        if not documents:
            return context.res.json({"error": "Utente non trovato"}, 404)

        doc = documents[0]
        document_id = doc["$id"]
        progressivo = doc.get("progressivo", 0)

        if progressivo >= len(PHOTO_IDS):
            bot.send_message(chat_id=chat_id, text="Hai già ricevuto tutte le foto disponibili.")
            return context.res.json({"status": "completo"})

        # Invia foto corrente
        photo_index = progressivo
        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[photo_index]}"
        bot.send_photo(chat_id=chat_id, photo=photo_url)

        # Aggiorna progressivo
        new_progressivo = progressivo + 1
        db.update_document(DATABASE_ID, COLLECTION_ID, document_id=document_id, data={
            "progressivo": new_progressivo
        })

        # Invia pulsante PayPal per prossima foto
        if new_progressivo < len(PHOTO_IDS):
            paypal_link = f"https://www.paypal.com/pay?chat_id={chat_id}"
            keyboard = [[InlineKeyboardButton("☕ Offrimi un altro caffè", url=paypal_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id=chat_id, text="Grazie ❤️ Vuoi vedere la prossima foto esclusiva?", reply_markup=reply_markup)

        return context.res.json({"status": "ok"})

    except Exception as e:
        print("Errore invio foto:", e)
        return context.res.json({"error": str(e)}, 500)
