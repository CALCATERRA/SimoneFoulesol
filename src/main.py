import json
import os
import requests

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Lista dei 100 ID di Google Drive
PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG", "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc", "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"  # ...continua fino a 100...
]

def send_photo_and_next_payment(chat_id: str, step: int):
    if step < len(PHOTO_IDS):
        # Manda foto step (0-based)
        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[step]}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data={
            "chat_id": chat_id,
            "photo": photo_url
        })

        # Manda pulsante (step+1)a se esiste
        if step + 1 < len(PHOTO_IDS):
            next_step = step + 1
            payment_link = f"https://paypal.me/SimonFoulesol?country.x=IT&locale.x=it_IT"
            keyboard = {
                "inline_keyboard": [[{
                    "text": f"💳 Paga 0,99€ per la foto {next_step + 1}",
                    "url": payment_link
                }]]
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                "chat_id": chat_id,
                "text": f"Per ricevere la prossima foto {next_step + 1}, effettua il pagamento👇",
                "reply_markup": json.dumps(keyboard)
            })
        else:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                "chat_id": chat_id,
                "text": "🎉 Hai visto tutte le foto disponibili! Grazie di cuore per il supporto. ❤️"
            })

def send_view_button(chat_id: str, step: int):
    keyboard = {
        "inline_keyboard": [[{
            "text": f"📸 Guarda foto {step}",
            "callback_data": f"{step}b"
        }]]
    }
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
        "chat_id": chat_id,
        "text": "❤️ Pagamento ricevuto! Premi per vedere la tua foto 👇",
        "reply_markup": json.dumps(keyboard)
    })

async def main(context):
    req = context.req
    res = context.res

    try:
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)

        # ➤ Richiamo manuale da index.html
        if body.get("source") == "manual-return" and body.get("chat_id") and body.get("step") is not None:
            chat_id = str(body["chat_id"])
            step = int(body["step"])
            send_view_button(chat_id, step)
            return res.json({"status": f"manual-return ok step {step}"}, 200)

        # ➤ Callback Telegram
        if "callback_query" in body:
            callback = body["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            data = callback.get("data", "")

            if data.endswith("b"):
                step_str = data[:-1]
                if step_str.isdigit():
                    step = int(step_str)
                    send_photo_and_next_payment(chat_id, step)
                    return res.json({"status": f"photo {step} ok"}, 200)

        # ➤ Comando /start
        if "message" in body:
            msg = body["message"]
            chat_id = str(msg["chat"]["id"])
            if msg.get("text") == "/start":
                keyboard = {
                    "inline_keyboard": [[{
                        "text": "💳 Paga 0,99€ per la foto 1",
                        "url": "https://paypal.me/SimonFoulesol?country.x=IT&locale.x=it_IT"
                    }]]
                }
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                    "chat_id": chat_id,
                    "text": "Benvenuto! Premi per acquistare la prima foto esclusiva:",
                    "reply_markup": json.dumps(keyboard)
                })

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        print("❗ Errore:", str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
