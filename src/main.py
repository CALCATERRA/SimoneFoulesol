import json
import os
import requests
import traceback

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")

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
            "inline_keyboard": [[
                {
                    "text": f"💳 Paga {prezzo_str}€ per la foto {step + 1}",
                    "url": payment_link
                }
            ]]
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": chat_id,
            "text": f"Per ricevere la foto {step + 1}, effettua il pagamento 👇",
            "reply_markup": json.dumps(keyboard)
        })

        # Subito dopo, invia anche il pulsante "✅ Ho pagato"
        callback_data = json.dumps({"action": "verify_payment", "step": step})
        keyboard2 = {
            "inline_keyboard": [[
                {
                    "text": "✅ Ho pagato",
                    "callback_data": callback_data
                }
            ]]
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": chat_id,
            "text": "Dopo il pagamento, premi il pulsante qui sotto per ricevere la foto ⬇️",
            "reply_markup": json.dumps(keyboard2)
        })

def main(context):
    try:
        req = context.req
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
        print("📥 Corpo ricevuto:", body)

        # Caso messaggio /start
        if "message" in body:
            msg = body["message"]
            chat_id = str(msg["chat"]["id"])
            if msg.get("text") == "/start":
                print(f"👋 /start ricevuto da chat_id={chat_id}")
                send_payment_button(chat_id, 0)
                return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "ok"})}

        # Gestione click pulsante "✅ Ho pagato"
        if "callback_query" in body:
            query = body["callback_query"]
            chat_id = str(query["message"]["chat"]["id"])
            data = json.loads(query.get("data", "{}"))

            if data.get("action") == "verify_payment":
                step = data.get("step", 0)
                # Qui notify.py dovrebbe essere richiamato (via webhook, funzione, ecc.)
                print(f"📨 Utente ha cliccato 'Ho pagato' per step {step}.")
                # Notifica all’utente
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                    "chat_id": chat_id,
                    "text": "Perfetto! Sto controllando il pagamento... 🔍"
                })
                # Qui potresti chiamare notify.py via HTTP o altro metodo
                # Oppure sarà notify.py stesso a chiamare Appwrite come fa già

                return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "ok"})}

        # Conferma da notify.py (dopo lettura della mail)
        if "chat_id" in body and "step" in body:
            token = body.get("secret_token")
            if token != SECRET_TOKEN:
                print("❌ Token segreto mancante o errato.")
                return {"statusCode": 401, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "error", "message": "Unauthorized"})}

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

            return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "ok"})}

        # Nessuna azione specifica
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "ok"})}

    except Exception as e:
        print("❗ Errore:", str(e))
        traceback.print_exc()
        return {"statusCode": 500, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"status": "error", "message": str(e)})}
