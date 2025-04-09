import json
import os
import requests

# Inserisci il tuo TOKEN Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Usa variabile d'ambiente
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"

def handler(request, response):
    try:
        # Parsing del corpo della richiesta
        data = json.loads(request.body)
        
        # Verifica che sia un messaggio di tipo "callback_query" o "message"
        message = data.get("message") or data.get("callback_query", {}).get("message")
        if not message:
            return response.send({"status": "error", "message": "No message found in the request"}, 400)

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # Gestione comandi
        if text == "/start":
            send_message(chat_id, "Benvenuto! Clicca per vedere la foto esclusiva.")
            send_inline_button(chat_id)
        
        # Gestione callback
        elif data.get("callback_query", {}).get("data") == "photo":
            send_message(chat_id, "Ecco la tua foto esclusiva!")
            send_photo(chat_id)

        return response.send({"status": "success"}, 200)
    
    except Exception as e:
        return response.send({"status": "error", "message": str(e)}, 500)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, data=payload)

def send_inline_button(chat_id):
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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": PHOTO_URL
    }
    requests.post(url, data=payload)

# ✅ Funzione richiesta da Appwrite
main = handler
