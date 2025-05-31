import json
import os
import requests
import traceback

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
BOT_USERNAME = "FoulesolExclusive_bot"
PREZZO_EURO = "1.99"
NETLIFY_BASE_URL = "https://comfy-mermaid-9cebbf.netlify.app"
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG",
    "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc",
    "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu"
]

def get_paypal_token():
    url = "https://api.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET))
    res.raise_for_status()
    return res.json()["access_token"]

def capture_order(order_id: str):
    token = get_paypal_token()
    url = f"https://api.paypal.com/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    res = requests.post(url, headers=headers)
    res.raise_for_status()
    return res.json()

def create_payment_link(chat_id: str, step: int):
    token = get_paypal_token()
    url = "https://api.paypal.com/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    return_url = f"{NETLIFY_BASE_URL}/?chat_id={chat_id}&step={step}"
    cancel_url = f"https://t.me/{BOT_USERNAME}"
    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": f"photo{step}",
            "amount": {
                "currency_code": "EUR",
                "value": PREZZO_EURO
            },
            "custom_id": f"{chat_id}:{step}"
        }],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()
        return next(link["href"] for link in res.json()["links"] if link["rel"] == "approve")
    except Exception as e:
        print("❗ Errore durante la creazione del pagamento PayPal:")
        print("Headers:", headers)
        print("Payload JSON:", json.dumps(data, indent=2))
        print("Risposta PayPal:", res.text)
        raise

def send_photo_and_next_payment(chat_id: str, step: int):
    if step < len(PHOTO_IDS):
        photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[step]}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data={
            "chat_id": chat_id,
            "photo": photo_url
        })

        if step + 1 < len(PHOTO_IDS):
            next_step = step + 1
            payment_link = create_payment_link(chat_id, next_step)
            keyboard = {
                "inline_keyboard": [[{
                    "text": f"💳 Paga {PREZZO_EURO}€ per la foto {next_step + 1}",
                    "url": payment_link
                }]]
            }
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                "chat_id": chat_id,
                "text": f"Spero ti piaccia 😏, per ricevere la foto {next_step + 1}, ti chiedo un altro piccolo contributo 😘 👇",
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
            "text": f"📸 Guarda foto {step + 1}",
            "callback_data": f"{step}b"
        }]]
    }
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
        "chat_id": chat_id,
        "text": "❤️ Pagamento ricevuto! Premi per vedere la tua foto 😏 👇",
        "reply_markup": json.dumps(keyboard)
    })

async def main(context):
    req = context.req
    res = context.res

    try:
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
        context.log("➡️ Corpo richiesta ricevuta:", body)

        # ➤ Richiamo manuale da Netlify (dopo pagamento)
        if body.get("source") == "manual-return" and body.get("chat_id") and body.get("step") is not None:
            chat_id = str(body["chat_id"])
            step = int(body["step"])
            send_view_button(chat_id, step)
            return res.json({"status": f"manual-return ok step {step}"}, 200)

        # ➤ Webhook da PayPal
        if body.get("event_type") == "CHECKOUT.ORDER.APPROVED":
            order_id = body["resource"]["id"]
            pu = body["resource"]["purchase_units"][0]
            custom_id = pu.get("custom_id", "")
            context.log("✔️ Webhook approvato per order_id:", order_id)

            if ":" in custom_id:
                chat_id, step = custom_id.split(":")
                step = int(step)
                capture_result = capture_order(order_id)
                context.log("📦 Ordine catturato:", capture_result)
                send_view_button(chat_id, step)
                return res.json({"status": f"Captured order {order_id} and sent photo button"}, 200)

        # ➤ Callback Telegram (bottone "Guarda foto")
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
                step = 0
                payment_link = create_payment_link(chat_id, step)
                keyboard = {
                    "inline_keyboard": [[{
                        "text": "💳 Paga 1,99€ per la foto 1",
                        "url": payment_link
                    }]]
                }
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
                    "chat_id": chat_id,
                    "text": "Benvenuto 😘 Premi qui sotto per acquistare e ricevere la prima foto esclusiva 👇:",
                    "reply_markup": json.dumps(keyboard)
                })

        return res.json({"status": "ok"}, 200)

    except Exception as e:
        context.error("❗ Errore:", str(e))
        context.error("🔍 Traceback:", traceback.format_exc())
        return res.json({"status": "error", "message": str(e)}, 500)
