import json
import os
import requests

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")

# Lista dei 100 ID di Google Drive
photo_ids = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG", "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc", "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu", "13C9nmhhttFf4nGKv2Z7iGl_WQsX1tr5p", "13D-2yT79oc0J3caET2hMgYr6drcufRVf",
    "144z0h5yA1IT0oarnl3uEXrRPHEC5y26z", "14slr2Igrc2GsmhT-9RAffg-Pg4ttLOXN", "14vcSGnxzUtd9kEi-pCqY5h3Is6y25LdK",
    "15ZyrWNW6LZuk3dojWo4WRxOCu_dgYV63", "15eBAgDjMRkkEto1Odgr6YoVEIRbHFLVB", "15kjS-DKMcFLo3H1cNYFKuPSqAGxuKMsp",
    "15o_m-JxH5nm6b9iHcHk_F48A98vDB7Od", "16w-wR9Ln_pQvRk-kVd8dSrfAgNntwZl2", "17Dfxj_HA6C9DCfYja0MEeUOjU02Ev-VI",
    "17FcREgyQie0gGQTPzxYvXXvB2iJJGOzQ", "17LHpO9C1qaBUaUhtdtq-Ry8iR8vT_5C3", "17NrIhfLFDNNJ7Ef-SNnKqetYcqnlzFug",
    "17a1s3TiFg59Zy04PqPHh7Xmz8Lhrcnqv", "17uqG3KYHJZtB8bl7nYqzA9snri9_tZ6b", "18VX_gW05gco1tcuFgyS1ptcgdBdHhH4v",
    "18zX2ETIdWE2v17mo1oeXQQkU1lf1B2j9", "1ABrA-UGW5tVCtDWqB5t2QK6kKM_BD_W9", "1Ahs6kzUJKDtuPOJvEpofnDk5aYPWiY7g",
    "1AnZVGqC-cYOjj4C-HOEICxoR9fB4J-w-", "1AxIjXnlERBMpU7tThlRzYJ_aMGq7ygcq", "1B44fuVdr3myTHLJeM2bX5j1F5dA_70zr",
    "1BQe_yNDlfJ3CxuEDheUpEo8IGI1TxzRs", "1BRDcXBxT8tyDg9ozV3EiZJ-tqz2J0eA2", "1Bz38wEbZ02ZBLlkcL3-TDb49T3TfZkpJ",
    "1CWRj7FeG5smcvRx6GIn95OaaiDFWwru-", "1CzMPT1CHHTqjAx_sPyaA0i-F6ICR8ipW", "1DFijX2Zq1MI8k4c3QgQOjZ2ZWmhnK2FN",
    "1DsSY92AUJfMl9vLgETbRP_zBTEtEN3Gh", "1DwjTLUYTJpdxvyrAwlGLo_gFCv9n-FZz", "1Dyr1hTL4H8q5lQiwIpq2L60ZaPxOhmIq",
    "1E8GSsf6mhQgBi01fjRY_aFnJTiQHH5zP", "1E9c2mn96B3FdfUtjKnTx6sRM-JK5sScc", "1EGBpAXx2ZRUfRFDZki5cOJoUAgjs3pTx",
    "1EVuJwHndXyaDTehmJZ2ONrzK0rJ0CHPv", "1EY3rSVEsm59Qo9z_VbAf4bpaK8_FitAG", "1EZ0ktOvAyMYvGnUAKZK_wg3R-RsHaNF3",
    "1EYpK4vwR8wJxZX1zTuS6L5YXsfr87GBD", "1Ehz3hZ3l-tNPGnwnqClO7sVfI9BJ3Dfb", "1EjDttbRC4So-xLBk8kdNnHQzAi8r2Vkp",
    "1EpnjkwWRBWiX9eOa7ETDf7gV9p6aF_wz", "1F-2zm0JfKHPHGc2AdYI3etGIEbwku_vy", "1F3z2PLUXf0LMy-Zc__CgP2WyEtodKg5Z",
    "1FHEu2vPU0FupxYZ8dIYrhKvhkpIEyFvA", "1FJCHHzIsr3izkJSvCdY6mYVPzMT6QtbC", "1FNNIkdf5PyR2QQZeuHWTJovIpjWprctD",
    "1FYslzMpuqSP4Fhxu5OKvP1aevTTpyWSN", "1FZFngKTz3yhrxXb4YubJGhrcBtWm8NqZ", "1FdODfKk9MD2H3a3PvOEx1E2Ub3RP-VPi",
    "1FoHR_2tx07zEM5HRiNh3MJrguCB2DQFh", "1FqYo4ylgLgTYGNeYvJp6FE4UBb53HJ0D", "1G7LTqkVItH3z-ydBhWbrqP9GlBmtwS8F",
    "1GADmPFiw3rN8uxMYtExxtgZerjSvDtuJ", "1GR3zK8J1uRJX2hdA2gmRSpWYUgUpLgSK", "1GTNkJ0FeZo16iVPOlZZUX_zM4_oDNbwQ",
    "1GW2UbzMC2SvvzAItt14RSN3TVby5FPnM", "1GcODwyTUGt_XCP67xY9RnBLiw7lPUvA2", "1GjR8YuHfYDZ6KO4y9BoqGXEIlpndqETj",
    "1Gp7eDMEXHQ1GlHhKD-9L6cS-lYgik2bw", "1GzTwjaAHjEEMvYAOaBuYyN_4Tx6XHuh9", "1H4oNHEHTJu5B-hHFcKJd6jEQV-uLIM09",
    "1HDMjcGS3rmuY0gMCLJPjy6OelHjAx7Zx", "1HMvVjaMB62YljF4IqUI3T9miUTWw3aeF", "1HZ3Z3MccNL3DPQlptujK0YDeOG7gtPvz",
    "1HaLDdr6TQ6FF9G7bfjXNsWXRw_MhEIdw", "1HfxsRO65yXWpKE0O-v8D9T4IJ_N9v62k", "1HhNB_jU1eRk3IkIv5zUMtOqQ7DVRMsD0",
    "1Hp82sUVZqJSJPIgEpeILJpNgTnn_dWtr", "1I0fcyKHs6bh6ekc9AA-cdn10sNKHiW4K", "1I1AgytVR7rRBv6RyaPPXxfWYbdNTAy9C",
    "1I3iOb-rlVSKQhTbrnQvHaMG3t-KF23mH", "1IADiNSfMH6f7WcMs9fW2VJqL8ldKAYpM", "1IApZgEu_ogE9dEi7a9cv8-L3MI1SYTTV",
    "1IH3zHFfHyOQ6z4xX0fjQ7LgL95D7yyY6", "1ISPR1Q-hvTb0w7TZ1y4PBJULaUgqzRaW", "1IWjNNEb2xMReab8IF8PK_djc4KHoEgjf",
    "1IcyO7qxgscMFue9vW63eUi2e7d7pNGsY", "1IgaMtuFC4KHQUlgVGTyGIEYc5M65d1kH", "1IqNx_sLND5PCN7KOD1h63Mvt7DAKlgn5",
    "1IqufQKvUAFJCIbMs1VVDeKn0A99THTnk", "1J-pVZix6HhncYy0AewLG_nuTR6m0EPDo", "1J1uNxtVVu2gB7ipYVfN9_O5ES_uoU4Ho",
    "1J8VNNWovNu2ioVpqlSwut5Chg0ivEKn6", "1JZbOMJpTG2uhEN3Z4Ds_1XfPSsT8klo0", "1JjbdWpbnb1_Xe8V_OXOP_WxZBvSKAqN1",
    "1JlmIVdThwJcUoiD39O-mPtnL3Y0dE9JH", "1JxmtSCrkx_1DM-bOgvNEzWY-y1SYJGva", "1K5UwptdcVbSx20JqJMB96-w3HDkoJzr4",
    "1Kf_aRw3asreQL6fgDSEWTU4YBEtn7J8m", "1KljIHm-vJ-xXGEGFJ2UYcb13Qh3YMTt5", "1Krcy3C8TND06_pvQ-4UJ8XMPOo52UEgG",
    "1KyG3EL7V6Dk0R-9XAiFa6iWrVxVUXNOz", "1L10rQtbZuTuOKFvV9AvULfMGshtmLADk", "1LAFsZMnAmv5K1qEyzLS8YGxTtPlIMYYl",
    "1LRgq3vo0XomX48OV2e8VY3mYiHkAnGBF", "1LhFkZzW7v80I_j_HcL3xADw6ttfZ9A7U", "1LuQqPP3taWOM52zCPpy-zmAorAigJNVm",
    "1M_G2shNjVliByv3T_Wb-ZxetIn7tIhO2", "1M4tfp3IMQhATcDO4vC_8uMJ5KKz7-ytp", "1MXcIKq9RIy9j0mRC1Rtb2xFDwISuMiCu",
    "1MiYjcdJyiQGZg6OQkgZDFYHHE4Ur9NHW", "1MwWeptOMhC1LRTkW-x3NpyGDhB65umUZ", "1N6Ylii27vopkN2sGi2yAuPq7D4zvIKgc",
    "1NBBR41eKeSk7mHLrz7u03Wl0koyVtYkU", "1NgYSc7nYDbNPMZ6v0GllSEfK9XYlAVWg", "1O0bqEiYjlZjEbqQ6sHFSOwfhViN_sij1",
    "1znUIP8-3OvipOZwKG-Nl9Jan6wRfQicD"
]

# Stato utenti
user_payments = {}

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
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "EUR", "value": str(amount)},
            "custom_id": str(chat_id),
            "notify_url": "https://67fd01767b6cc3ff6cc6.appwrite.global/v1/functions/67fd0175002fa4a735c4/executions"
        }],
        "application_context": {
            "return_url": f"https://comfy-mermaid-9cebbf.netlify.app/?chat_id={chat_id}",
            "cancel_url": "https://t.me/FoulesolExclusive_bot"
        }
    }
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return next(link['href'] for link in res.json()['links'] if link['rel'] == 'approve')

def send_payment_link(chat_id):
    payment_link = create_payment_link(chat_id, 0.99)
    user_payments[chat_id] = {
        'payment_pending': True,
        'photo_index': user_payments.get(chat_id, {}).get('photo_index', 0)
    }
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "Paga 0,99€ con PayPal", "url": payment_link}]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": (
            "Clicca sul pulsante per offrirmi un caffè su PayPal. "
            "Dopo il pagamento, torna qui e premi *Guarda foto* per riceverla."
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, data=payload)

def send_view_photo_button(chat_id):
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

def send_photo(chat_id):
    user_state = user_payments.get(chat_id, {})
    if user_state.get('payment_pending') is False:
        index = user_state.get('photo_index', 0)
        if index < len(PHOTO_IDS):
            photo_url = f"https://drive.google.com/uc?export=view&id={PHOTO_IDS[index]}"
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            payload = {"chat_id": chat_id, "photo": photo_url}
            requests.post(url, data=payload)

            # Incrementa per la prossima volta
            user_payments[chat_id]['photo_index'] = index + 1
            user_payments[chat_id]['payment_pending'] = None
        else:
            print(f"✅ Fine foto per chat_id={chat_id}")
    else:
        print(f"⚠️ Accesso non autorizzato alla foto per chat_id: {chat_id}")

def handle_paypal_ipn(request_data):
    verify_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    verify_payload = 'cmd=_notify-validate&' + request_data
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(verify_url, headers=headers, data=verify_payload)

    if res.text == "VERIFIED":
        ipn = dict(x.split('=') for x in request_data.split('&') if '=' in x)
        payment_status = ipn.get("payment_status")
        chat_id = ipn.get("custom")

        if payment_status == "Completed" and chat_id:
            current_index = user_payments.get(chat_id, {}).get('photo_index', 0)
            if current_index < len(PHOTO_IDS):
                user_payments[chat_id] = {
                    'payment_pending': False,
                    'photo_index': current_index
                }
                send_view_photo_button(chat_id)

async def main(context):
    req = context.req
    res = context.res

    try:
        content_type = req.headers.get("content-type", "")
        raw_body = req.body_raw if isinstance(req.body_raw, str) else req.body_raw.decode()

        if "application/x-www-form-urlencoded" in content_type:
            handle_paypal_ipn(raw_body)
            return res.json({"status": "IPN processed"}, 200)

        try:
            data = req.body if isinstance(req.body, dict) else json.loads(req.body)
        except Exception as e:
            print("❗ JSON parsing error:", str(e))
            return res.json({"status": "invalid json"}, 400)

        if data.get("source") == "manual-return" and data.get("chat_id"):
            chat_id = str(data["chat_id"])
            current_index = user_payments.get(chat_id, {}).get('photo_index', 0)
            user_payments[chat_id] = {
                'payment_pending': False,
                'photo_index': current_index
            }
            send_view_photo_button(chat_id)
            return res.json({"status": "manual-return ok"}, 200)

        message = data.get("message")
        callback = data.get("callback_query")

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
