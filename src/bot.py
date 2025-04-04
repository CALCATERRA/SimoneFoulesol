import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Vedi la foto", callback_data="photo")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Benvenuto! Clicca per vedere la foto esclusiva.",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "photo":
        await query.edit_message_text(text="Ecco la tua foto esclusiva!")
        with open("percorso/alla/foto.jpg", "rb") as photo:
            await context.bot.send_photo(chat_id=query.message.chat.id, photo=photo)

async def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Errore: TELEGRAM_TOKEN non trovato nelle variabili d'ambiente")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
