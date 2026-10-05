import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MERCADOPAGO_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN não configurado")

if not MERCADOPAGO_ACCESS_TOKEN:
    raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurado")


# -------------------------
# Servidor para o Render
# -------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot online!")

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


threading.Thread(
    target=start_health_server,
    daemon=True
).start()


# -------------------------
# Menu inicial
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📸 Ver catálogo",
                callback_data="catalogo"
            )
        ],
        [
            InlineKeyboardButton(
                "💬 Suporte",
                callback_data="suporte"
            )
        ],
    ]

    await update.message.reply_text(
        "👋 Olá! Seja bem-vindo(a)!\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------------
# Catálogo
# -------------------------

async def catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 Comprar — R$ 29,90",
                callback_data="comprar_1"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Voltar",
                callback_data="inicio"
            )
        ],
    ]

    await update.message.reply_text(
        "📸 CATÁLOGO\n\n"
        "🖼️ Foto Premium 01\n"
        "💰 Valor: R$ 29,90\n\n"
        "Clique abaixo para comprar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------------
# Criar PIX Mercado Pago
# -------------------------

async def criar_pix():

    url = "https://api.mercadopago.com/v1/payments"

    headers = {
        "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }

    data = {
        "transaction_amount": 29.90,
        "description": "Foto Premium 01",
        "payment_method_id": "pix",
        "payer": {
            "email": "cliente@example.com"
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.post(
            url,
            headers=headers,
            json=data
        )

    if response.status_code not in (200, 201):

        print("Erro Mercado Pago:")
        print(response.status_code)
        print(response.text)

        return None

    return response.json()


# -------------------------
# Botões
# -------------------------

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "catalogo":

        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 Comprar — R$ 29,90",
                    callback_data="comprar_1"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Voltar",
                    callback_data="inicio"
                )
            ],
        ]

        await query.edit_message_text(
            "📸 CATÁLOGO\n\n"
            "🖼️ Foto Premium 01\n"
            "💰 Valor: R$ 29,90\n\n"
            "Clique em comprar:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "comprar_1":

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Gerar PIX",
                    callback_data="pagamento"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Voltar",
                    callback_data="catalogo"
                )
            ],
        ]

        await query.edit_message_text(
            "🛒 COMPRA\n\n"
            "Produto: Foto Premium 01\n"
            "Valor: R$ 29,90\n\n"
            "Clique abaixo para gerar o PIX.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "pagamento":

        await query.edit_message_text(
            "⏳ Gerando seu PIX..."
        )

        payment = await criar_pix()

        if not payment:

            await query.edit_message_text(
                "❌ Não foi possível gerar o PIX agora.\n\n"
                "Verifique a configuração do Mercado Pago."
            )

            return

        point_of_interaction = payment.get(
            "point_of_interaction",
            {}
        )

        transaction_data = point_of_interaction.get(
            "transaction_data",
            {}
        )

        qr_code = transaction_data.get(
            "qr_code"
        )

        qr_code_base64 = transaction_data.get(
            "qr_code_base64"
        )

        if not qr_code:

            await query.edit_message_text(
                "❌ O Mercado Pago não retornou o código PIX.\n\n"
                f"ID do pagamento: {payment.get('id')}"
            )

            return

        await query.edit_message_text(
            "✅ PIX GERADO!\n\n"
            "💰 Valor: R$ 29,90\n\n"
            "📋 Copie o código PIX abaixo e faça o pagamento:\n\n"
            f"`{qr_code}`\n\n"
            "Depois que o pagamento for confirmado, "
            "vamos configurar a entrega automática da foto.",
            parse_mode="Markdown"
        )

        if qr_code_base64:
            print("QR Code PIX recebido do Mercado Pago.")

    elif query.data == "suporte":

        await query.edit_message_text(
            "💬 SUPORTE\n\n"
            "Entre em contato para receber ajuda."
        )

    elif query.data == "inicio":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📸 Ver catálogo",
                    callback_data="catalogo"
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 Suporte",
                    callback_data="suporte"
                )
            ],
        ]

        await query.edit_message_text(
            "🏠 MENU PRINCIPAL\n\n"
            "Escolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# -------------------------
# Inicialização
# -------------------------

def main():

    app = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("catalogo", catalogo)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("🤖 Bot iniciado!")

    app.run_polling()


if __name__ == "__main__":
    main()
