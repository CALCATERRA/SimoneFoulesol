import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Recupera il token del bot dalle variabili d'ambiente
TOKEN = os.getenv('TELEGRAM_TOKEN') or 'INSERISCI_IL_TUO_TOKEN_QUI'

# URL della foto su Appwrite
PHOTO_URL = "https://cloud.appwrite.io/v1/storage/buckets/67f694430030364ac183/files/67f694ed0029e4957b1c/view?project=67f037f300060437d16d&mode=admin"

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
        await query.edit_message_text(text="Ecco la tua foto esclusiva!")
        await context.bot.send_photo(chat_id=query.message.chat.id, photo=PHOTO_URL)

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
