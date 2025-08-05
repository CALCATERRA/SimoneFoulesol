import json
import os
import requests
import traceback

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

PHOTO_IDS = [
    "10dgQq9LgVgWfZcl97jJPxsJbr1DBrxyG", "11uKOYNTCu1bDoetyKfPtRLMTqsYPKKEc", "13--pJBJ1uyyO36ChfraQ2aVQfKecWtfr",
    "135lkGQNvf_T4CwtRH-Pu2sG7n30iV1Cu", "13C9nmhhttFf4nGKv2Z7iGl_WQsX1tr5p", "13D-2yT79oc0J3caET2hMgYr6drcufRVf",
    "144z0h5yA1IT0oarnl3uEXrRPHEC5y26z", "14slr2Igrc2GsmhT-9RAffg-Pg4ttLOXN", "15pXSsTF8ayrjl_ua9smZUvCDHfhTH8Gu",
    "16nV4JMazZcvIdCMxEpBSaYgFXXJpD0C6", "173_9MtHcaYuUmrf7pUCP_J0qVZ3zucGW", "17fnrSdj3r94DZ2ig0DQx92RA3A-EPhVZ",
    "18Snl6xhNJVzm9QRZ0b05R6Hgr_iZhubt", "18aw4EFlGpvyD3IwiFjZvT-NYFvBnvQZB", "197d6bBgWJoUJkUZq8-tgO46T9_5ZzvId",
    "19_Gfl5Gek47ZbWdr0C9MRNBwtakMWA3v", "19oO3GZSLtoj4hfGPA9c13qT2RjjCApoh", "1AQezum9yf_hZH9BSmZpnPY3VBZacYMFc",
    "1AkFCZP52mv4OfCmcZw7gOEZAmN7294YG", "1ArUOwM2g4NJSPSYdm5ka4FXbXcnic7mQ", "1AygvOSgMjp4yESjitaxBDOZDCURuBu0I",
    "1Ayim8ueGrrT2dM0QYL2oJPx6b6nIoO1A", "1BWUdiyGLhf1vfIKb4ACmtjNdt8DIbPDI", "1CLEbKTwuc6hHigmrpZ1Z8TJcHnqs2i1p",
    "1Cd06_I7bDuG4PX5y1E_KOxpGRNlU26nU", "1Cp7EfOWlmxyUcs9TsGfK7SoFzHOtmtEW", "1Db3UYjZbWIAuaAZmw_dn1ox2d9ssau4i",
    "1E4DVZI9xH9TrxGZW0OoIrVtI5i-o2q8P", "1FICBA7_-_shpM1OOxHeWZLTq8xd98Skx", "1Fr8xSoSbSDo-PYk8AVbCuu6j2-SoODzQ",
    "1GKSv88L0wohipW7IPTZx_eEstELGz2ZX", "1Htv9eTIH2vga7u6YnILSagXPlUkHqbf6", "1IIPY4zNiqtEcuwCyT1DYGalXGTw2qPzj",
    "1IZDw-R3or0QdHdw6NK-RC96z7Db-x22J", "1JcQo9bXSW3M_-yEx7UI5zYY5s7f-rK_M", "1Ke1kKjXd0_-uLoSMgRdsOhPRVHq4B2uF",
    "1LSLpALr7JsiJrM9vvpCgq2hAzMQqNE5h", "1MKODOZju_udYk4AIzfpgemFfxdK7y3hh", "1MZ4u_bjQ8dcaGlXUXLajxYrI1Q4G-c73",
    "1MlQ4XWy-PM_q4yAFXdYUWgu57sRxkKbj", "1MnS1InGQtK_i1bQfiYIlHNDMwzwV3KBJ", "1Mrpm1KmAvKUeqD8HTN5JJNuFHIEkMrjv",
    "1N2fSsvrPoYX4osvZfHGctoCsA41WYf_-", "1NP9b7qN0NsqLRBtzHIB8tV3Z_5Mk-pfa", "1Ng3i_ARIq_TZE5UP0-2Uv9JUAykjILJI",
    "1NwwC2lwDb6f0E1O6BK2AR4cbIlTiRLqw", "1Onabvg_gkbwZHsXpuO2IoXbpym572wRt", "1P3LKMuJD_r2euM4EXqsmcLyu3YsRgXHu",
    "1Pe3sIR3EXQ2EZrBpC9Fn_pnqm7FhgMlP", "1QElyZgf0sjVTPiquplujG05YDps3_PU8", "1RILKcI4T0cYpNv__X_OozViOqDUclPi3",
    "1SAn75nZ-QxYIOY3aq7q95zdFdLhc8Kij", "1Slmu8EmYZKY01L_66RkIsyi1shDNMOsZ", "1TCbhrklZkQK_4un1gPHtWD9gBg6qJh0K",
    "1Ta85U2Rl3m4he3UBCF6dKgELUB6AwszT", "1TfoGL29JH5Tc9OvGClJ21hufF_PUjTYh", "1UYrEChlnP9AG8xDGtZawBOyh4Ej3-SXQ",
    "1UeYuPrK-9GgoGt1u9sEQnMLF9eImy258", "1Vcg2RpplXTS347-jx5zQQ6-qp_Brezf5", "1VlzmJaXz5GmeSbhE9ECbCLXXNGlw89bQ",
    "1X-UThDxJa1oSpM8SnA60h1BtaGp1erGJ", "1XyM0OvWrX3V9aMIyx45_KnsbzJ747Stl", "1YCxmh2iZglgXWBy_dEqQD0Za102M8Bc9",
    "1YbVp5encf57at09iIPlD-Dk5h7Buzo1T", "1_Etlf6Qm640MEkKiY4DYgXsmIDYC0iGv", "1_Hudkm_GPn2FnplvLrj_Dq2IuNHkBoFk",
    "1_wy0exNenyNggROQsmKN9vOQkghqDVuK", "1aZUSBIn4416tELHD89MXyclWoJZgBMFc", "1ar7ntit15aswzYWHJlyfURLz84A2idkU",
    "1bV5-mWGzB5MA0Ava7Jnsq11j_mE188VK", "1b_Anl37Bp8v-1Z928_hrH2MI2FbGa9-l", "1cI3Gh9ycwFp76NJ3QXVtf1Rh2SYHZnQq",
    "1cJHx3rvpBZ6_HI9a4xXX6OaR53qSzbE7", "1dzQLOlpRFcCCOpFK-EEtK20VAmZlqmeS", "1hJpOLPazX-JNS36ROWFhJLHfGA4Wi2mK",
    "1iDihKenRgbR336Mm15Ec-L302MrjfyT8", "1itzI1yy1HCPBH0mRfADJ9mA7XMz2ocB0", "1jG6608oC7XhJpXcRPakST8_Nk_CLaAaL",
    "1k_vW2PjB5Votl-wimVk9axQ9tK1WkHij", "1muvfhJa5lKLzb5UcXa6AsRi9IhzsUvd_", "1nZnkqJe9GNpbp1IHXzpl4b4IRbx5QAk-",
    "1nmQFV1Xyy7G23fwXtmAlJmkft97euAeR", "1oN_mI-rHySEHCY3JOUlBlYehXO4MkpM5", "1pU7wh5DoSlqHEpOb7TVBQp9rP6UhIvf7",
    "1pYsk5tVtb9spr9ALe14yTnE1yI8Pv3k0", "1qDL-6tU-dprdCToznJG5OlXKFD4VJ_5I", "1qr0eRguO9xlbaqGpy97OFxSR-fiVtjc1",
    "1s2-Um9sAbWyg8uuGIFFnjiOev5XTXA6T", "1s5XUFOIACFNApAu9E8XMSGW83xAX0Do7", "1sPOaAP1gwOPci3DHdfVMXIT3EIp60j8a",
    "1sTMKg9vcPoxyPAeT9s6VHKxHtsZ4fxgo", "1saroTmDSZ53HqwkWUEFduAn5JElPjaxp", "1sbaiJhmmftGXOEJCtwZkk_3DPmx0d2gV",
    "1tH9tT2orgaCHVxUNLO9tLqTmghl9I3-7", "1uVufHiRXAN8JP06uozZZ1eqpdYyggErR", "1ujvW1-dIbrS9CuoDgD_ak_0myboppNlP",
    "1wD-Rnu5Zn3josWavRwxWOk5aLRAPkUCV", "1wfNSsxqjieJ5-Kmjt_okqKF6D8xuG3MZ", "1zdwWUhC5PGnN7MJdrFJeZEq1SbE0Q1Pm",
    "1znUIP8-3OvipOZwKG-Nl9Jan6wRfQicD"

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

async def main(context):
    req = context.req
    res = context.res

    try:
        body = req.body if isinstance(req.body, dict) else json.loads(req.body)
        print("📥 Corpo ricevuto:", body)

        # Messaggio Telegram
        if "message" in body:
            msg = body["message"]
            chat_id = str(msg["chat"]["id"])
            if msg.get("text") == "/start":
                print(f"👋 /start ricevuto da chat_id={chat_id}")
                send_payment_button(chat_id, 0)
                return res.json({"status": "ok"}, 200)

        # Callback da Netlify
        if "query" in req.params:
            params = req.params["query"]
            chat_id = params.get("chat_id")
            step_str = params.get("step")

            if not chat_id or not step_str:
                return res.json({"status": "error", "message": "Parametri mancanti"}, 400)

            step = int(step_str)
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
