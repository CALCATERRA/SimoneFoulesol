import json
import os
import requests

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"

# Stato utenti
user_payments = {}

# Manda link PayPal su Telegram
def send_payment_link(chat_id):
    payment_link = (
        f"https://www.sandbox.paypal.com/checkoutnow?amount=0.99"
        f"&currency=EUR"
        f"&custom={chat_id}"
        f"&return=https://calcaterra.github.io/paypal-return/paypal-return.html?chat_id={chat_id}"
        f"&cancel_return=https://t.me/FoulesolExclusive_bot"
    )
    user_payments[chat_id] = {'payment_pending': True}
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Paga 0,99€ con PayPal", "url": payment_link}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": (
            "Ciao 😘 clicca sul pulsante per offrirmi un caffè su PayPal. "
            "Dopo il pagamento, torna qui e premi *Guarda foto* per riceverla 😏"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

# Mostra pulsante "Guarda foto"
def send_view_photo_button(chat_id):
    print(f"📸 Invio pulsante 'Guarda foto' a {chat_id}")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Guarda foto", "callback_data": "photo"}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Pagamento ricevuto! Premi qui sotto per vedere la foto 👇",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

# Invia foto all'utente
def send_photo(chat_id):
    if user_payments.get(chat_id, {}).get('payment_pending') is False:
        print(f"✅ Invio foto a {chat_id}")
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": PHOTO_URL
        }
        requests.post(url, data=payload)
    else:
        print(f"⚠️ Tentativo di accesso alla foto non autorizzato da {chat_id}")

# Funzione principale Appwrite
async def main(context):
    req = context.req
    res = context.res

    try:
        data = req.body
        message = data.get("message")
        callback = data.get("callback_query")

        # 🔁 Ritorno da GitHub dopo pagamento
        if data.get("source") == "paypal-return":
            chat_id = data.get("chat_id")
            print(f"🔔 Notifica ritorno da GitHub per chat_id={chat_id}")
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)
            return res.json({"status": "notified"}, 200)

        if message:
            chat_id = str(message["chat"]["id"])
            if message.get("text") == "/start":
                send_payment_link(chat_id)

        elif callback:
            chat_id = str(callback["message"]["chat"]["id"])
            if callback.get("data") == "photo":
                send_photo(chat_id)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        print("❗ Errore:", str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
