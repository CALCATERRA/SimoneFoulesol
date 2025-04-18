import os
import json
import requests
from flask import Flask, request
from appwrite.client import Client
from appwrite.services.databases import Databases
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

app = Flask(__name__)

# ENV
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

@app.route("/", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    if "message" not in data:
        return "OK", 200

    message = data["message"]
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "")

    if text == "/start":
        handle_start(chat_id)
    return "OK", 200

def handle_start(chat_id):
    # Verifica se esiste già
    try:
        response = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[
            f'equal("chat_id", "{chat_id}")'
        ])
        documents = response["documents"]

        if documents:
            progressivo = documents[0]["progressivo"]
        else:
            db.create_document(DATABASE_ID, COLLECTION_ID, document_id="unique()", data={
                "chat_id": chat_id,
                "progressivo": 0
            })
            progressivo = 0
    except Exception as e:
        print("Errore DB:", e)
        return

    # Invio pulsante PayPal
    paypal_link = f"https://www.paypal.com/pay?chat_id={chat_id}"
    keyboard = [[InlineKeyboardButton("☕ Paga 0,99€ per iniziare", url=paypal_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=chat_id, text="Clicca qui per iniziare il percorso esclusivo:", reply_markup=reply_markup)
