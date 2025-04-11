import json
import os
import requests
from dotenv import load_dotenv
from paypal import get_paypal_token, create_payment_link

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEFAULT_PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"


def send_payment_link(chat_id, telegram_user_id, photo_number):
    token = get_paypal_token()
    if not token:
        print("❌ Impossibile ottenere il token paypal")
        return

    payment_url = create_payment_link(token, telegram_user_id, photo_number)
    if not payment_url:
        print("❌ Errore nella generazione del link di pagamento")
        return

    keyboard = {
        "inline_keyboard": [
            [{"text": f"Paga 0,99€ per la foto {photo_number}", "url": payment_url}],
            [{"text": "Ho pagato", "callback_data": f"paid_{photo_number}"}]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": (
            f"Per sbloccare la foto {photo_number}, clicca sul pulsante qui sotto per pagare con paypal.\n"
            f"Dopo il pagamento, torna qui e clicca su *Ho pagato* 😏"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, data=payload)
    print("send_payment_link:", response.status_code, response.text)


def send_photo(chat_id, photo_number):
    # Qui puoi dinamicamente cambiare URL se ogni foto è diversa
    # Esempio: se hai una lista su Appwrite, puoi indicizzare o generare il link dinamicamente
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    photo_url = DEFAULT_PHOTO_URL  # Puoi cambiare con link per photo_number
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": f"Ecco la tua foto {photo_number} 😘"
    }
    response = requests.post(url, data=payload)
    print("send_photo:", response.status_code, response.text)


# ✅ Compatibile Appwrite con gestione pagamento
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
            telegram_user_id = message["from"]["id"]

            print("Chat ID:", chat_id)
            print("Text:", text)

            user = message.get("from", {})
            print(f"Utente: {user.get('first_name', '')} {user.get('last_name', '')} (@{user.get('username', '')})")

            # /start oppure /start 3
            if text.startswith("/start"):
                try:
                    parts = text.split()
                    photo_number = int(parts[1]) if len(parts) > 1 else 1
                except Exception:
                    photo_number = 1

                send_payment_link(chat_id, telegram_user_id, photo_number)

        # Se è una callback del pulsante
        elif callback_query:
            chat_id = callback_query["message"]["chat"]["id"]
            data_value = callback_query.get("data")

            if data_value.startswith("paid_"):
                photo_number = int(data_value.split("_")[1])
                send_photo(chat_id, photo_number)

        return response.json({"status": "success"}, 200)

    except Exception as e:
        print("Errore:", str(e))
        return response.json({"status": "error", "message": str(e)}, 500)
