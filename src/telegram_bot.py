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

        # 🔹 Ottiene access token PayPal
        auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials"}

        token_response = requests.post(
            "https://api-m.paypal.com/v1/oauth2/token",
            auth=auth,
            headers=headers,
            data=data
        )
        access_token = token_response.json()["access_token"]

        # 🔹 Crea ordine PayPal
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "EUR",
                    "value": "0.99"
                }
            }],
            "application_context": {
                "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
                "cancel_url": "https://t.me/FoulesolExclusive_bot"
            }
        }

        order_response = requests.post(
            "https://api-m.paypal.com/v2/checkout/orders",
            headers=headers,
            json=order_data
        )
        order_json = order_response.json()
        approval_url = next(link["href"] for link in order_json["links"] if link["rel"] == "approve")

        # 🔹 Invia pulsante PayPal con URL reale
        message = "Clicca qui per iniziare il percorso esclusivo:"
        button_text = "☕ Paga 0,99€ per iniziare"
        send_button(chat_id, message, button_text, approval_url)

    except Exception as e:
        print("Errore DB o PayPal:", e)

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
