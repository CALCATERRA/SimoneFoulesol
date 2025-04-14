import json
import os
import requests

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"

# Stato utenti in memoria (volatile)
user_payments = {}

# Crea ordine PayPal
def create_payment_link(chat_id, amount):
    PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
    PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
    
    # Ottieni access token PayPal
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    token_res = requests.post(
        "https://api.sandbox.paypal.com/v1/oauth2/token",
        auth=auth,
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"}
    )
    token_res.raise_for_status()
    access_token = token_res.json()["access_token"]

    # Crea ordine
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "EUR", "value": str(amount)},
            "custom_id": str(chat_id)
        }],
        "application_context": {
            "return_url": f"https://calcaterra.github.io/paypal-return/paypal-return.html?chat_id={chat_id}",
            "cancel_url": "https://t.me/FoulesolExclusive_bot"
        }
    }

    order_res = requests.post(
        "https://api.sandbox.paypal.com/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=order_data
    )
    order_res.raise_for_status()
    approve_link = next(link["href"] for link in order_res.json()["links"] if link["rel"] == "approve")
    return approve_link

# Manda link PayPal su Telegram
def send_payment_link(chat_id):
    payment_link = create_payment_link(chat_id, 0.99)
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

# Invia la foto
def send_photo(chat_id):
    if user_payments.get(chat_id, {}).get('payment_pending') is False:
        print(f"✅ Invio foto a {chat_id}")
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": PHOTO_URL}
        requests.post(url, data=payload)
    else:
        print(f"⚠️ Tentativo di accesso alla foto non autorizzato da {chat_id}")

# Entry point Appwrite
async def main(context):
    req = context.req
    res = context.res

    try:
        data = req.body
        message = data.get("message")
        callback = data.get("callback_query")

        # 🔔 Notifica da return_url GitHub
        if data.get("source") == "paypal-return":
            chat_id = data.get("chat_id")
            print(f"🔔 Ritorno da GitHub per chat_id={chat_id}")
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)
            return res.json({"status": "notified"}, 200)

        # ✅ Gestione click da pagina HTML post-pagamento
        if data.get("source") == "manual-return" and "chat_id" in data:
            chat_id = str(data["chat_id"])
            print(f"🖱️ Click manual-return per chat_id={chat_id}")
            user_payments[chat_id] = {'payment_pending': False}
            send_view_photo_button(chat_id)
            return res.json({"status": "manual return ok"}, 200)

        # Comando /start
        if message:
            chat_id = str(message["chat"]["id"])
            if message.get("text") == "/start":
                send_payment_link(chat_id)

        # Callback "Guarda foto"
        elif callback:
            chat_id = str(callback["message"]["chat"]["id"])
            if callback.get("data") == "photo":
                send_photo(chat_id)

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        print("❗ Errore:", str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
