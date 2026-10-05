import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# CONFIGURAÇÕES
# =========================

TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN não configurado no Render")


# =========================
# SERVIDOR DE SAÚDE DO RENDER
# =========================

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


# =========================
# COMANDO /START
# =========================

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
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Olá! Seja bem-vindo(a)!\n\n"
        "📸 Aqui você pode conferir nossas fotos disponíveis.\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=reply_markup
    )


# =========================
# COMANDO /CATALOGO
# =========================

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
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📸 CATÁLOGO\n\n"
        "🖼️ Foto Premium 01\n"
        "💰 Preço: R$ 29,90\n\n"
        "Clique abaixo para comprar:",
        reply_markup=reply_markup
    )


# =========================
# BOTÕES
# =========================

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
            ]
        ]

        await query.edit_message_text(
            "📸 CATÁLOGO\n\n"
            "🖼️ Foto Premium 01\n"
            "💰 Preço: R$ 29,90\n\n"
            "Clique em comprar para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "comprar_1":

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Continuar compra",
                    callback_data="pagamento"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Voltar",
                    callback_data="catalogo"
                )
            ]
        ]

        await query.edit_message_text(
            "🛒 COMPRA\n\n"
            "Produto: Foto Premium 01\n"
            "Valor: R$ 29,90\n\n"
            "O pagamento via PIX será configurado na próxima etapa.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "pagamento":

        await query.edit_message_text(
            "💳 PAGAMENTO\n\n"
            "Estamos preparando o pagamento via PIX.\n\n"
            "Na próxima etapa vamos conectar este botão ao Mercado Pago."
        )

    elif query.data == "suporte":

        await query.edit_message_text(
            "💬 SUPORTE\n\n"
            "Entre em contato com o suporte para receber ajuda."
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
            ]
        ]

        await query.edit_message_text(
            "🏠 MENU PRINCIPAL\n\n"
            "Escolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# INICIALIZAÇÃO
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catalogo", catalogo))

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("🤖 Bot iniciado!")

    app.run_polling()


if __name__ == "__main__":
    main()
