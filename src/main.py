import json
import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"


def send_inline_button(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Vedi la foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Benvenuto! Clicca per vedere la foto esclusiva😘",
        "reply_markup": json.dumps(keyboard)
    }
    response = requests.post(url, data=payload)
    print("send_inline_button:", response.status_code, response.text)


def send_photo(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": PHOTO_URL
    }
    response = requests.post(url, data=payload)
    print("send_photo:", response.status_code, response.text)


# ✅ Compatibile Appwrite con gestione /start ottimizzata
async def main(context):
    request = context.req
    response = context.res

    try:
        print("Ricevuto request:", request.method, request.body)

        data = request.body  # ✅ già un dict in Appwrite
        print("Parsed JSON:", data)

        message = data.get("message")
        callback_query = data.get("callback_query")

        # Se è un messaggio classico
        if message:
            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            print("Chat ID:", chat_id)
            print("Text:", text)

            # Log utente
            user = message.get("from", {})
            print(f"Utente: {user.get('first_name', '')} {user.get('last_name', '')} (@{user.get('username', '')})")

            if text == "/start":
                send_inline_button(chat_id)

        # Se è una callback del pulsante
        elif callback_query:
            chat_id = callback_query["message"]["chat"]["id"]
            data_value = callback_query.get("data")

            if data_value == "photo":
                send_photo(chat_id)

        return response.json({"status": "success"}, 200)

    except Exception as e:
        print("Errore:", str(e))
        return response.json({"status": "error", "message": str(e)}, 500)
