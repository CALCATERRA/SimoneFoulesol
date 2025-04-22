async def main(context):
    req = context.req
    res = context.res

    # STEP BASE - parsing del corpo della richiesta
    try:
        data = req.body if isinstance(req.body, dict) else json.loads(req.body)
        print("✅ JSON ricevuto correttamente")
    except Exception as e:
        print("❌ Errore parsing JSON:", str(e))
        return res.json({"status": "invalid json", "error": str(e)}, 400)

    # Estrai chat_id da message o callback (comune a tutti i test)
    chat_id = None
    if "message" in data:
        chat_id = str(data["message"].get("chat", {}).get("id"))
    elif "callback_query" in data:
        chat_id = str(data["callback_query"].get("message", {}).get("chat", {}).get("id"))
    if not chat_id:
        return res.json({"status": "no chat_id"}, 400)

    # ------------------------------------------
    # FASE 1: TEST TELEGRAM
    # ------------------------------------------
    try:
        print("📤 Invio messaggio Telegram test...")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": "🧪 Test Telegram OK"}
        )
        return res.json({"status": "fase-1-telegram-ok"}, 200)
    except Exception as e:
        print("❌ Telegram error:", str(e))
        return res.json({"status": "fase-1-telegram-error", "message": str(e)}, 500)

    # ------------------------------------------
    # FASE 2: TEST PAYPAL TOKEN
    # ------------------------------------------
    # try:
    #     print("🔐 Ottieni token PayPal...")
    #     token = get_paypal_token()
    #     print("✅ Token ottenuto:", token[:10] + "...")
    #     return res.json({"status": "fase-2-paypal-ok"}, 200)
    # except Exception as e:
    #     print("❌ PayPal error:", str(e))
    #     return res.json({"status": "fase-2-paypal-error", "message": str(e)}, 500)

    # ------------------------------------------
    # FASE 3: TEST CREAZIONE LINK PAYPAL
    # ------------------------------------------
    # try:
    #     print("💳 Creo link pagamento PayPal...")
    #     payment_link = create_payment_link(chat_id, 0.99)
    #     print("✅ Link creato:", payment_link)
    #     return res.json({"status": "fase-3-create-link-ok", "link": payment_link}, 200)
    # except Exception as e:
    #     print("❌ Errore creazione link:", str(e))
    #     return res.json({"status": "fase-3-create-link-error", "message": str(e)}, 500)

    # ------------------------------------------
    # FASE 4: TEST APPWRITE CLIENT E GET DOCUMENT
    # ------------------------------------------
    # try:
    #     print("📦 Inizializzo client Appwrite...")
    #     databases = init_appwrite_client()
    #     print("🔍 Recupero documento utente...")
    #     user_data = databases.get_document(DATABASE_ID, COLLECTION_ID, chat_id)
    #     print("✅ Dati utente trovati:", user_data)
    #     return res.json({"status": "fase-4-appwrite-ok", "user_data": user_data}, 200)
    # except Exception as e:
    #     print("❌ Errore Appwrite:", str(e))
    #     return res.json({"status": "fase-4-appwrite-error", "message": str(e)}, 500)

    # ------------------------------------------
    # FASE 5: TEST INVIO FOTO (FAKE)
    # ------------------------------------------
    # try:
    #     photo_url = "https://drive.google.com/uc?export=view&id=" + PHOTO_IDS[0]
    #     requests.post(
    #         f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
    #         data={"chat_id": chat_id, "photo": photo_url}
    #     )
    #     return res.json({"status": "fase-5-send-photo-ok"}, 200)
    # except Exception as e:
    #     print("❌ Errore invio foto:", str(e))
    #     return res.json({"status": "fase-5-send-photo-error", "message": str(e)}, 500)

    return res.json({"status": "done?"}, 200)
