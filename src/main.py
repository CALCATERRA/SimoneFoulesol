import json
import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, data=payload)
    print("send_message:", response.status_code, response.text)


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


# ✅ Compatibile Appwrite con fix JSON body
async def main(context):
    request = context.req
    response = context.res

    try:
        print("Ricevuto request:", request.method, request.body)

        data = request.body  # ✅ già un dict
        print("Parsed JSON:", data)

        message = data.get("message") or data.get("callback_query", {}).get("message")
        if not message:
            print("Nessun messaggio trovato.")
            return response.json({"status": "error", "message": "No message found"}, 400)

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        print("Chat ID:", chat_id)
        print("Text:", text)

        if text == "/start":
            send_message(chat_id, "Benvenuto! Clicca per vedere la foto esclusiva.")
            send_inline_button(chat_id)
        elif data.get("callback_query", {}).get("data") == "photo":
            send_message(chat_id, "Ecco la tua foto esclusiva!")
            send_photo(chat_id)

        return response.json({"status": "success"}, 200)

    except Exception as e:
        print("Errore:", str(e))
        return response.json({"status": "error", "message": str(e)}, 500)
