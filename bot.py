import os
import time
import requests
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])

# Precio de lanzamiento
PRICE_STARS = 1500

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)


def telegram(method, data=None):
    response = requests.post(
        f"{API}/{method}",
        json=data or {},
        timeout=30
    )
    return response.json()


@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200


@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(silent=True)

    if not update:
        return "OK", 200

    # =========================
    # /start
    # =========================

    if "message" in update:

        message = update["message"]
        chat_id = message["chat"]["id"]

        if message.get("text", "").startswith("/start"):

            telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🎬 <b>CURSO: CREA VÍDEOS CON IA</b>\n\n"
                        "Aprende desde cero a crear vídeos "
                        "con IA de una forma sencilla.\n\n"
                        "🔥 Método paso a paso\n"
                        "✅ Sin experiencia\n"
                        "✅ Sin programas complicados\n"
                        "✅ Herramientas online\n"
                        "✅ Método para generar sin gastar dinero\n\n"
                        "💰 <b>Precio: 1.500 Stars</b>\n\n"
                        "Pulsa el botón para comprar."
                    ),
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "🛒 COMPRAR CURSO",
                                    "callback_data": "buy_course"
                                }
                            ]
                        ]
                    }
                }
            )

    # =========================
    # BOTÓN COMPRAR
    # =========================

    if "callback_query" in update:

        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]

        telegram(
            "answerCallbackQuery",
            {
                "callback_query_id": callback["id"]
            }
        )

        if callback["data"] == "buy_course":

            telegram(
                "sendInvoice",
                {
                    "chat_id": chat_id,
                    "title": "Curso de Vídeos con IA",
                    "description": (
                        "Curso completo para aprender "
                        "a crear vídeos con IA."
                    ),
                    "payload": "curso_videos_ia_29",
                    "currency": "XTR",
                    "prices": [
                        {
                            "label": "Curso de Vídeos con IA",
                            "amount": PRICE_STARS
                        }
                    ]
                }
            )

    # =========================
    # PRE-CHECKOUT
    # =========================

    if "pre_checkout_query" in update:

        query = update["pre_checkout_query"]

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id": query["id"],
                "ok": True
            }
        )

    # =========================
    # PAGO CONFIRMADO
    # =========================

    if "message" in update:

        message = update["message"]

        if "successful_payment" in message:

            user_id = message["from"]["id"]

            result = telegram(
                "createChatInviteLink",
                {
                    "chat_id": CHANNEL_ID,
                    "member_limit": 1,
                    "expire_date": int(time.time()) + 86400
                }
            )

            if result.get("ok"):

                invite_link = result["result"]["invite_link"]

                telegram(
                    "sendMessage",
                    {
                        "chat_id": user_id,
                        "text": (
                            "🎉 <b>¡PAGO COMPLETADO!</b>\n\n"
                            "Tu acceso al curso está listo.\n\n"
                            "👇 Pulsa aquí para entrar:"
                        ),
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "🎬 ENTRAR AL CURSO",
                                        "url": invite_link
                                    }
                                ]
                            ]
                        }
                    }
                )

            else:

                telegram(
                    "sendMessage",
                    {
                        "chat_id": user_id,
                        "text": (
                            "✅ Pago recibido.\n\n"
                            "Ha habido un problema generando "
                            "tu enlace de acceso. Contacta con soporte."
                        )
                    }
                )

    return "OK", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
