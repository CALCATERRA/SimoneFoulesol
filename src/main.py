import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Recupera il token del bot dalle variabili d'ambiente
TOKEN = os.getenv('TELEGRAM_TOKEN')
PHOTO_PATH = Path("percorso/alla/foto.jpg")  # Cambia con il percorso corretto

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Vedi la foto", callback_data='photo')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Benvenuto! Clicca per vedere la foto esclusiva.',
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'photo':
        if PHOTO_PATH.exists():
            await query.edit_message_text(text="Ecco la tua foto esclusiva!")
            with open(PHOTO_PATH, 'rb') as photo:
                await context.bot.send_photo(chat_id=query.message.chat.id, photo=photo)
        else:
            await query.edit_message_text(text="Errore: foto non trovata.")

async def main() -> None:
    if TOKEN is None:
        print("Errore: il token non è stato trovato nelle variabili d'ambiente!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot avviato.")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
