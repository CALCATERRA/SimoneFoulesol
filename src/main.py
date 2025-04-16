import json
import requests
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_IDS = [  # Metti qui tutti i tuoi 100 ID
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    # ... aggiungi altri ...
]

user_states = {}  # Stato in RAM

def handle(event, context):
    body = json.loads(event.get("body", "{}"))

    if "message" in body:
        chat_id = body["message"]["chat"]["id"]
        text = body["message"].get("text", "")

        if text == "/start":
            user_states[chat_id] = {"photo_index": 0}
            send_photo(chat_id)

    elif "queryStringParameters" in event:
        # Questo viene chiamato da Netlify dopo pagamento
        chat_id = int(event["queryStringParameters"].get("chat_id", ""))
        if chat_id:
            user_states.setdefault(chat_id, {"photo_index": 0})
            user_states[chat_id]["photo_index"] += 1
            send_photo(chat_id)

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "ok"})
    }

def send_photo(chat_id):
    state = user_states.get(chat_id, {})
    index = state.get("photo_index", 0)

    if index < len(PHOTO_IDS):
        photo_id = PHOTO_IDS[index]
        photo_url = f"https://drive.google.com/uc?export=view&id={photo_id}"
        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": photo_url}
        requests.post(send_url, data=payload)

        # Messaggio con cuoricini
        msg_text = "❤️‍🔥 Goditi questa foto esclusiva! ❤️‍🔥"
        msg_payload = {"chat_id": chat_id, "text": msg_text}
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=msg_payload)

        # Pulsante PayPal per la prossima foto
        if index + 1 < len(PHOTO_IDS):
            paypal_link = f"https://paypal.me/SimonFoulesol?chat_id={chat_id}"
            button_payload = {
                "chat_id": chat_id,
                "text": "🔥 Vuoi vedere la prossima foto? 🔥",
                "reply_markup": json.dumps({
                    "inline_keyboard": [[
                        {
                            "text": "Paga per la prossima foto 💳",
                            "url": paypal_link
                        }
                    ]]
                })
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=button_payload)
        else:
            # Ultima foto inviata
            final_msg = {
                "chat_id": chat_id,
                "text": "🎉 Hai visto tutte le foto disponibili! Grazie! ❤️"
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=final_msg)
