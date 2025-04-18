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
PAYPAL_CLIENT_ID = os.environ["PAYPAL_CLIENT_ID"]
PAYPAL_SECRET = os.environ["PAYPAL_SECRET"]

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

        if "message" not in body:
            return context.res.empty()

        message = body["message"]
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")

        if text == "/start":
            handle_start(chat_id)

        return context.res.empty()  # 🔚 chiusura corretta

    except Exception as e:
        print("Errore telegram_bot.py:", e)
        return context.res.send("Errore", 500)

def handle_start(chat_id):
    try:
        # Controlla se l'utente esiste
        response = db.list_documents(DATABASE_ID, COLLECTION_ID, queries=[
            f'equal("chat_id", "{chat_id}")'
        ])
        documents = response["documents"]

        if not documents:
            # Crea nuovo documento con progressivo 0
            db.create_document(DATABASE_ID, COLLECTION_ID, document_id="unique()", data={
                "chat_id": chat_id,
                "progressivo": 0
            })

        # Invia pulsante PayPal
        paypal_link = f"https://www.paypal.com/pay?chat_id={chat_id}&client_id={PAYPAL_CLIENT_ID}"
        message = "Clicca qui per iniziare il percorso esclusivo:"
        button_text = "☕ Paga 0,99€ per iniziare"
        send_button(chat_id, message, button_text, paypal_link)

    except Exception as e:
        print("Errore DB o invio messaggio:", e)

# 🔹 Funzione per inviare messaggi con bottone
def send_button(chat_id, text, button_text, url):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "reply_markup": {
                "inline_keyboard": [[{"text": button_text, "url": url}]]
            }
        }
    )
