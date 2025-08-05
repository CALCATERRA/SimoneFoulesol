import json
import os
import requests
import traceback

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
]

PREZZI = [1.99 - i * 0.01 for i in range(len(PHOTO_IDS))]

def create_payment_link(chat_id, step):
    prezzo = PREZZI[step]
    prezzo_str = f"{prezzo:.2f}"
    # Passo anche amount per controllo importo preciso
    return f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}&step={step}&amount={prezzo_str}"

def send_photo(chat_id, step):
    photo_id = PHOTO_IDS[step]
    photo_url = f"https://drive.google.com/uc?export=view&id={photo_id}"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data={
        "chat_id": chat_id,
        "photo": photo_url
    })

def send_payment_button(chat_id, step):
    if step < len(PHOTO_IDS):
        payment_link = create_payment_link(chat_id, step)
        prezzo_str = f"{PREZZI[step]:.2f}"
        keyboard = {
            "inline_keyboard": [[{
                "text": f"💳 Paga {prezzo_str}€ per la foto {step + 1}",
                "url": payment_link
            }]]
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": chat_id,
            "text": f"Per ricevere la foto {step + 1}, effettua il pagamento 👇",
            "reply_markup": json.dumps(keyboard)
        })

def main(context):
    req = context.req
    res = context.res

    try:
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
        print("📥 Corpo ricevuto:", body)

        # Caso messaggio Telegram
        if "message" in body:
            msg = body["message"]
            chat_id = str(msg["chat"]["id"])
            if msg.get("text") == "/start":
                print(f"👋 /start ricevuto da chat_id={chat_id}")
                send_payment_button(chat_id, 0)
                return res.json({"status": "ok"}, 200)

        # Conferma pagamento da Netlify (notify.py)
        if "chat_id" in body and "step" in body:
            chat_id = body["chat_id"]
            step = int(body["step"])
            print(f"✅ Pagamento confermato. Invio foto {step + 1} a chat_id={chat_id}")
            send_photo(chat_id, step)

            next_step = step + 1
            if next_step < len(PHOTO_IDS):
                send_payment_button(chat_id, next_step)
            else:
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                    "chat_id": chat_id,
                    "text": "🎉 Hai visto tutte le foto disponibili! Grazie di cuore per il supporto. ❤️"
                })

            return res.json({"status": "ok"}, 200)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        print("❗ Errore:", str(e))
        traceback.print_exc()
        return res.json({"status": "error", "message": str(e)}, 500)
