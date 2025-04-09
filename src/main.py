import json
import os
import requests

# Inserisci il tuo TOKEN Telegram
TELEGRAM_TOKEN = '8146014311:AAHADlhNP95XhlXEQshyIsWCnrRNpigRnAY'
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"

def handler(request, response):
    # Parsing del corpo della richiesta
    data = json.loads(request.body)
    
    # Verifica che sia un messaggio di tipo "callback_query" o "message"
    if "message" in data:
        message = data["message"]
    elif "callback_query" in data:
        message = data["callback_query"]["message"]
    
    if not message:
        return response.send({"status": "error", "message": "No message found in the request"}, 400)

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Gestisci il comando /start
    if text == "/start":
        # Costruisci il messaggio con il pulsante "Vedi la foto"
        send_message(chat_id, "Benvenuto! Clicca per vedere la foto esclusiva.")
        send_inline_button(chat_id)
    # Gestisci la risposta al pulsante
    elif "callback_query" in data and data["callback_query"]["data"] == "photo":
        send_message(chat_id, "Ecco la tua foto esclusiva!")
        send_photo(chat_id)

    return response.send({"status": "success"}, 200)


def send_message(chat_id, text):
    """Invia un messaggio al canale Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, data=payload)


def send_inline_button(chat_id):
    """Invia un pulsante Inline a Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Vedi la foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Benvenuto! Clicca per vedere la foto esclusiva.",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)


def send_photo(chat_id):
    """Invia la foto usando il link di Appwrite"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": PHOTO_URL
    }
    requests.post(url, data=payload)
