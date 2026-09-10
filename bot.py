import os
import time
import requests
from flask import Flask, request

# =========================================================
# CONFIGURACIÓN
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])

# Precio del curso en Telegram Stars
PRICE_STARS = 1500

# Identificador interno del producto
PAYLOAD = "curso_videos_ia_29"

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# Guarda temporalmente los pagos procesados mientras el servidor está activo.
# Más adelante podemos añadir una base de datos para hacerlo permanente.
processed_payments = set()


# =========================================================
# FUNCIÓN PARA LLAMAR A TELEGRAM
# =========================================================

def telegram(method, data=None):
    try:
        response = requests.post(
            f"{API}/{method}",
            json=data or {},
            timeout=30
        )

        return response.json()

    except Exception as e:
        print(f"Error Telegram API ({method}): {e}")
        return {
            "ok": False,
            "error": str(e)
        }


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando correctamente", 200


# =========================================================
# WEBHOOK
# =========================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    update = request.get_json(silent=True)

    if not update:
        return "OK", 200

    print("Update recibido:", update)

    # =====================================================
    # MENSAJES
    # =====================================================

    if "message" in update:

        message = update["message"]
        chat_id = message["chat"]["id"]

        # =================================================
        # /START
        # =================================================

        if message.get("text", "").startswith("/start"):

            telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🎬 <b>CURSO: CREA VÍDEOS CON IA</b>\n\n"

                        "Aprende desde cero a crear y recrear "
                        "vídeos con IA de una forma sencilla.\n\n"

                        "🔥 <b>¿Qué aprenderás?</b>\n\n"
                        "✅ Método paso a paso\n"
                        "✅ Sin experiencia previa\n"
                        "✅ Herramientas online\n"
                        "✅ Sin programas complicados\n"
                        "✅ Creación de vídeos con IA\n"
                        "✅ Proceso sencillo y práctico\n\n"

                        "💰 <b>Precio de lanzamiento: 1.500 Stars</b>\n\n"

                        "Pulsa el botón para obtener acceso "
                        "al curso."
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

        # =================================================
        # /TERMS
        # =================================================

        elif message.get("text", "").startswith("/terms"):

            telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "📄 <b>TÉRMINOS DEL CURSO</b>\n\n"
                        "Al realizar la compra aceptas los términos "
                        "del servicio y las condiciones de acceso "
                        "al contenido digital del curso.\n\n"
                        "El acceso se proporciona mediante un enlace "
                        "privado al canal del curso después de "
                        "confirmarse el pago.\n\n"
                        "Para cualquier problema con el pago o el "
                        "acceso, utiliza /paysupport."
                    ),
                    "parse_mode": "HTML"
                }
            )

        # =================================================
        # /PAYSUPPORT
        # =================================================

        elif message.get("text", "").startswith("/paysupport"):

            telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": (
                        "🆘 <b>SOPORTE DE PAGO</b>\n\n"
                        "Si has realizado el pago y no has recibido "
                        "el acceso al curso, contacta con el "
                        "administrador del bot indicando el problema "
                        "y, si es posible, tu comprobante de pago."
                    ),
                    "parse_mode": "HTML"
                }
            )

        # =================================================
        # PAGO CONFIRMADO
        # =================================================

        if "successful_payment" in message:

            payment = message["successful_payment"]

            user_id = message["from"]["id"]

            # Datos del pago
            payment_id = payment.get(
                "telegram_payment_charge_id"
            )

            payload = payment.get("invoice_payload")

            total_amount = payment.get("total_amount")

            print(
                f"Pago recibido | "
                f"user_id={user_id} | "
                f"payment_id={payment_id} | "
                f"payload={payload} | "
                f"amount={total_amount}"
            )

            # =================================================
            # COMPROBACIONES DE SEGURIDAD
            # =================================================

            # Comprobar que el pago corresponde a nuestro curso
            if payload != PAYLOAD:

                print("Pago rechazado: payload incorrecto")

                telegram(
                    "sendMessage",
                    {
                        "chat_id": user_id,
                        "text": (
                            "⚠️ Se ha recibido un pago con un "
                            "producto no reconocido. Contacta "
                            "con soporte."
                        )
                    }
                )

                return "OK", 200

            # Comprobar cantidad
            if total_amount != PRICE_STARS:

                print("Pago rechazado: cantidad incorrecta")

                telegram(
                    "sendMessage",
                    {
                        "chat_id": user_id,
                        "text": (
                            "⚠️ El importe del pago no coincide "
                            "con el precio del curso. Contacta "
                            "con soporte."
                        )
                    }
                )

                return "OK", 200

            # =================================================
            # EVITAR PROCESAR EL MISMO PAGO DOS VECES
            # =================================================

            if payment_id in processed_payments:

                print("Pago ya procesado:", payment_id)

                return "OK", 200

            processed_payments.add(payment_id)

            # =================================================
            # CREAR ENLACE PRIVADO DE UN SOLO USO
            # =================================================

            result = telegram(
                "createChatInviteLink",
                {
                    "chat_id": CHANNEL_ID,

                    # Solo puede utilizarlo una persona
                    "member_limit": 1,

                    # El enlace caduca en 24 horas
                    "expire_date": int(time.time()) + 86400
                }
            )

            # =================================================
            # SI TELEGRAM CREA EL ENLACE
            # =================================================

            if result.get("ok"):

                invite_link = result["result"]["invite_link"]

                telegram(
                    "sendMessage",
                    {
                        "chat_id": user_id,
                        "text": (
                            "🎉 <b>¡PAGO COMPLETADO!</b>\n\n"
                            "¡Gracias por comprar el curso! 🚀\n\n"
                            "Tu acceso al curso está listo.\n\n"
                            "👇 <b>Pulsa el botón para entrar:</b>"
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

                print(
                    f"Acceso creado correctamente para "
                    f"user_id={user_id}"
                )

            # =================================================
            # SI NO PUEDE CREAR EL ENLACE
            # =================================================

            else:

                print(
                    "ERROR creando enlace:",
                    result
                )

                telegram(
                    "sendMessage",
                    {
                        "chat_id": user_id,
                        "text": (
                            "✅ <b>Pago recibido correctamente.</b>\n\n"
                            "Sin embargo, ha ocurrido un problema "
                            "generando tu enlace de acceso.\n\n"
                            "No vuelvas a pagar.\n"
                            "Contacta con soporte para recibir "
                            "tu acceso."
                        ),
                        "parse_mode": "HTML"
                    }
                )

    # =====================================================
    # BOTÓN COMPRAR
    # =====================================================

    if "callback_query" in update:

        callback = update["callback_query"]

        chat_id = callback["message"]["chat"]["id"]

        # Quitar el estado de "cargando" del botón
        telegram(
            "answerCallbackQuery",
            {
                "callback_query_id": callback["id"]
            }
        )

        # =================================================
        # COMPRAR CURSO
        # =================================================

        if callback["data"] == "buy_course":

            result = telegram(
                "sendInvoice",
                {
                    "chat_id": chat_id,

                    "title": "Curso de Vídeos con IA",

                    "description": (
                        "Curso completo para aprender "
                        "a crear vídeos con IA paso a paso."
                    ),

                    # Identificador interno del producto
                    "payload": PAYLOAD,

                    # Telegram Stars
                    "currency": "XTR",

                    "prices": [
                        {
                            "label": "Curso de Vídeos con IA",
                            "amount": PRICE_STARS
                        }
                    ]
                }
            )

            print("Resultado sendInvoice:", result)

    # =====================================================
    # PRE-CHECKOUT
    # =====================================================

    if "pre_checkout_query" in update:

        query = update["pre_checkout_query"]

        print(
            "Pre-checkout recibido:",
            query.get("id")
        )

        telegram(
            "answerPreCheckoutQuery",
            {
                "pre_checkout_query_id": query["id"],
                "ok": True
            }
        )

    return "OK", 200


# =========================================================
# ARRANCAR SERVIDOR
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
