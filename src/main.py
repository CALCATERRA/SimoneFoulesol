import json
import os
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases

# Config
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
PAYPAL_CLIENT_ID = os.environ["PAYPAL_CLIENT_ID"]
PAYPAL_SECRET    = os.environ["PAYPAL_SECRET"]
DATABASE_ID      = os.environ["DATABASE_ID"]
COLLECTION_ID    = os.environ["COLLECTION_ID"]

# Lista semplificata (metti qui i 100 ID reali)
PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu",
    # ... fino a 100 ...
]

# Inizializza Appwrite
client = Client()\
    .set_endpoint(os.environ["APPWRITE_ENDPOINT"])\
    .set_project(os.environ["APPWRITE_PROJECT_ID"])\
    .set_key(os.environ["APPWRITE_API_KEY"])
db = Databases(client)

def get_paypal_token():
    res = requests.post(
        "https://api.sandbox.paypal.com/v1/oauth2/token",
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    )
    res.raise_for_status()
    return res.json()["access_token"]

def create_payment_link(chat_id, amount=0.99):
    token = get_paypal_token()
    res = requests.post(
        "https://api.sandbox.paypal.com/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": "EUR", "value": str(amount)},
                "custom_id": str(chat_id)
            }],
            "application_context": {
                "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
                "cancel_url": "https://t.me/FoulesolExclusive_bot"
            }
        }
    )
    res.raise_for_status()
    return next(l["href"] for l in res.json()["links"] if l["rel"] == "approve")

def send_payment_link(chat_id):
    # recupera o crea stato utente
    try:
        user = db.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except:
        user = None

    if user is None:
        db.create_document(DATABASE_ID, COLLECTION_ID, chat_id, {
            "photo_index": 0,
            "payment_pending": True
        })
    else:
        # se è già in attesa, non rimandare un altro link
        if user.get("payment_pending", False):
            return
        db.update_document(DATABASE_ID, COLLECTION_ID, chat_id, {
            "photo_index": user["photo_index"],
            "payment_pending": True
        })

    link = create_payment_link(chat_id)
    payload = {
        "chat_id": chat_id,
        "text":     "☕ Offrimi un caffè su PayPal e ricevi la prossima foto esclusiva. Dopo il pagamento, torna qui!",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{"text": "💳 Paga 0,99€ per la prossima foto", "url": link}]
            ]
        })
    }
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)

def send_view_photo_button(chat_id):
    # solo se era in attesa
    try:
        user = db.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except:
        return

    if not user.get("payment_pending", False):
        return

    # segna come ricevuto
    db.update_document(DATABASE_ID, COLLECTION_ID, chat_id, {
        "photo_index": user["photo_index"],
        "payment_pending": False
    })

    payload = {
        "chat_id": chat_id,
        "text":     "❤️ Pagamento ricevuto! Premi per vedere la tua foto 👇",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{"text": "📸 Guarda foto", "callback_data": "photo"}]
            ]
        })
    }
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)

def send_photo(chat_id):
    # recupera stato
    try:
        user = db.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except:
        return

    idx = user.get("photo_index", 0)
    if idx >= len(PHOTO_IDS):
        # terminato
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": chat_id,
                "text":    "🎉 Hai visto tutte le foto! Grazie di cuore. ❤️"
            }
        )
        return

    # invia immagine
    photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[idx]}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
        data={"chat_id": chat_id, "photo": photo_url}
    )

    # aggiorna indice e invia link successivo
    db.update_document(DATABASE_ID, COLLECTION_ID, chat_id, {
        "photo_index": idx + 1,
        "payment_pending": False
    })

    # manda subito il prossimo invito a pagare (se ne rimangono)
    if idx + 1 < len(PHOTO_IDS):
        send_payment_link(chat_id)

async def main(context):
    req  = context.req
    res  = context.res

    # estrai JSON
    try:
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
    except Exception as e:
        context.error("❗ JSON parsing: " + str(e))
        return res.json({"status":"bad json"}, 400)

    # manual return da pagina HTML
    if body.get("source") == "manual-return" and "chat_id" in body:
        send_view_photo_button(str(body["chat_id"]))
        return res.json({"status":"manual-return ok"}, 200)

    # messaggi Telegram
    if "message" in body:
        msg = body["message"]
        if msg.get("text") == "/start":
            send_payment_link(str(msg["chat"]["id"]))
    elif "callback_query" in body:
        cb = body["callback_query"]
        if cb.get("data") == "photo":
            send_photo(str(cb["message"]["chat"]["id"]))

    return res.json({"status":"ok"}, 200)
