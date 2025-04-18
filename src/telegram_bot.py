import os
import json
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

# Appwrite Client
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

def main(context):
    try:
        body = json.loads(context.req.body)
        context.res.send("OK", 200)  # ✅ Risponde subito per evitare timeout

        # Verifica che sia un messaggio valido
        if "message" not in body:
            return

        message = body["message"]
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")

        if text == "/start":
            handle_start(chat_id)

    except Exception as e:
        print("Errore telegram_bot.py:", e)
        context.res.send("Errore", 500)

def handle_start(chat_id):
    try:
        # Cerca utente nel database
        response = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[
            f'equal(\"chat_id\", \"{chat_id}\")'
        ])
        documents = response["documents"]

        if not documents:
            # Crea nuovo utente con progressivo 0
            db.create_document(DATABASE_ID, COLLECTION_ID, document_id="unique()", data={
                "chat_id": chat_id,
                "progressivo": 0
            })

        # Manda pulsante PayPal
        paypal_link = f"https://www.paypal.com/pay?chat_id={chat_id}"
        keyboard = [[InlineKeyboardButton("☕ Paga 0,99€ per iniziare", url=paypal_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.send_message(chat_id=chat_id, text="Clicca qui per iniziare il percorso esclusivo:", reply_markup=reply_markup)

    except Exception as e:
        print("Errore DB o Telegram:", e)
