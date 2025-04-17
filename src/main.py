import json
import os
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")
DATABASE_ID = os.environ.get("DATABASE_ID")
COLLECTION_ID = os.environ.get("COLLECTION_ID")
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG", "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc", "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
    # ...continua...
]

def log_env(context):
    context.log("🔧 TELEGRAM_TOKEN:", "✅" if TELEGRAM_TOKEN else "❌")
    context.log("🔧 PAYPAL_CLIENT_ID:", "✅" if PAYPAL_CLIENT_ID else "❌")
    context.log("🔧 PAYPAL_SECRET:", "✅" if PAYPAL_SECRET else "❌")
    context.log("🔧 DATABASE_ID:", "✅" if DATABASE_ID else "❌")
    context.log("🔧 COLLECTION_ID:", "✅" if COLLECTION_ID else "❌")
    context.log("🔧 APPWRITE_ENDPOINT:", APPWRITE_ENDPOINT or "❌")
    context.log("🔧 APPWRITE_PROJECT_ID:", APPWRITE_PROJECT_ID or "❌")
    context.log("🔧 APPWRITE_API_KEY:", "✅" if APPWRITE_API_KEY else "❌")

def init_appwrite_client():
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    return Databases(client)

def get_paypal_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    res.raise_for_status()
    return res.json()['access_token']

def create_payment_link(chat_id, amount):
    token = get_paypal_token()
    url = "https://api.sandbox.paypal.com/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
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
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return next(link['href'] for link in res.json()['links'] if link['rel'] == 'approve')

def send_payment_link(chat_id, databases, context):
    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except:
        user_data = None

    # Previene doppio invio se già in attesa pagamento
    if user_data and user_data.get("payment_pending") == True:
        context.log("⚠️ Link già inviato, skip.")
        return

    payment_link = create_payment_link(chat_id, 0.99)

    if not user_data:
        databases.create_document(DATABASE_ID, COLLECTION_ID, chat_id, {
            "payment_pending": True,
            "photo_index": 0
        })
    else:
        user_data["payment_pending"] = True
        databases.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [[
            {"text": "💳 Paga 0,99€ per la prossima foto", "url": payment_link}
        ]]
    }
    payload = {
        "chat_id": chat_id,
        "text": "☕ Offrimi un caffè su PayPal e ricevi la prossima foto esclusiva. Dopo il pagamento, torna qui!",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

def send_view_photo_button(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [[
            {"text": "📸 Guarda foto", "callback_data": "photo"}
        ]]
    }
    payload = {
        "chat_id": chat_id,
        "text": "❤️ Pagamento ricevuto! Premi per vedere la tua foto 👇",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

def send_photo(chat_id, databases):
    try:
        user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    except:
        return

    index = user_data.get("photo_index", 0)
    if index >= len(PHOTO_IDS):
        return

    photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[index]}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
        data={"chat_id": chat_id, "photo": photo_url}
    )

    user_data['photo_index'] = index + 1
    user_data['payment_pending'] = None
    databases.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)

    if index + 1 < len(PHOTO_IDS):
        send_payment_link(chat_id, databases, context=None)
    else:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": chat_id,
            "text": "🎉 Hai visto tutte le foto disponibili! Grazie di cuore per il supporto. ❤️"
        })

async def main(context):
    req = context.req
    res = context.res
    try:
        log_env(context)
        databases = init_appwrite_client()

        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
        message = body.get("message")
        callback = body.get("callback_query")

        if body.get("source") == "manual-return":
            chat_id = str(body.get("chat_id"))
            if chat_id:
                try:
                    user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
                    user_data["payment_pending"] = False
                    databases.update_document(DATABASE_ID, COLLECTION_ID, chat_id, user_data)
                    send_view_photo_button(chat_id)
                    return res.json({"status": "manual-return ok"}, 200)
                except Exception as e:
                    context.error("❗ manual-return fail: " + str(e))
                    return res.json({"status": "error"}, 500)
            return res.json({"status": "missing chat_id"}, 400)

        if message:
            chat_id = str(message.get("chat", {}).get("id"))
            text = message.get("text", "")
            if chat_id and text == "/start":
                # Risposta immediata a Telegram
                res.json({"status": "ok"}, 200)
                send_payment_link(chat_id, databases, context)
                return

        if callback:
            chat_id = str(callback.get("message", {}).get("chat", {}).get("id"))
            if chat_id and callback.get("data") == "photo":
                res.json({"status": "ok"}, 200)
                send_photo(chat_id, databases)
                return

        return res.json({"status": "no-action"}, 200)

    except Exception as e:
        context.error("❗ Errore generale: " + str(e))
        return res.json({"status": "error", "message": str(e)}, 500)
