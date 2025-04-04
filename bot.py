import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

# Recupera il token del bot dalle variabili d'ambiente
TOKEN = os.getenv('TELEGRAM_TOKEN')

def start(update: Update, context: CallbackContext) -> None:
    # Risposta iniziale con pulsante
    keyboard = [
        [InlineKeyboardButton("Vedi la foto", callback_data='photo')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Benvenuto! Clicca per vedere la foto esclusiva.', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'photo':
        # Invio la foto
        query.edit_message_text(text="Ecco la tua foto esclusiva!")
        context.bot.send_photo(chat_id=query.message.chat_id, photo=open('percorso/alla/foto.jpg', 'rb'))

def main():
    # Controlla che il token sia stato trovato
    if TOKEN is None:
        print("Errore: il token non è stato trovato nelle variabili d'ambiente!")
        return

    # Configura il bot
    updater = Updater(TOKEN)

    # Aggiungi i comandi
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # Avvia il bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
