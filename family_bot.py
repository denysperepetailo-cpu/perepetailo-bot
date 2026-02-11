import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from tinydb import TinyDB
from datetime import datetime

# ===== НАСТРОЙКА =====
TOKEN = "8549280564:AAHowQlkn6ucbpvVV3CAvtPn_ufa6c_DXNc"
ALLOWED_USERS = [334637350, 663322435]

db = TinyDB('data.json')
shopping_table = db.table('shopping')
wallet_table = db.table('wallet')
notes_table = db.table('notes')

# ===== FLASK ДЛЯ RENDER =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Бот запущен!"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    bot.update_queue.put(update)
    return "OK", 200

@app.route('/favicon.ico')
def favicon():
    return '', 204

# ===== HELPERS =====
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Список покупок 🛒", callback_data='shopping')],
        [InlineKeyboardButton("Общий кошелёк $", callback_data='wallet')],
        [InlineKeyboardButton("Заметки 📋", callback_data='notes')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== /START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У тебя нет доступа.")
        return
    await update.message.reply_text("Привет! Выбирай меню:", reply_markup=main_menu_keyboard())

# ===== CALLBACK ДЛЯ КНОПОК =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in ALLOWED_USERS:
        await query.answer("❌ У тебя нет доступа.", show_alert=True)
        return
    await query.answer()
    data = query.data

    if data == 'shopping':
        keyboard = [
            [InlineKeyboardButton("Добавить товар", callback_data='add_shopping')],
            [InlineKeyboardButton("Показать список", callback_data='show_shopping')],
            [InlineKeyboardButton("Удалить товар", callback_data='del_shopping')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Список покупок:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'wallet':
        keyboard = [
            [InlineKeyboardButton("Посмотреть баланс", callback_data='show_wallet')],
            [InlineKeyboardButton("Внести $", callback_data='add_wallet')],
            [InlineKeyboardButton("Снять $", callback_data='take_wallet')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Общий кошелёк $:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'notes':
        keyboard = [
            [InlineKeyboardButton("Добавить заметку", callback_data='add_note')],
            [InlineKeyboardButton("Показать заметки", callback_data='show_notes')],
            [InlineKeyboardButton("Удалить заметку", callback_data='del_note')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Заметки:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'back':
        await query.edit_message_text("Главное меню:", reply_markup=main_menu_keyboard())

# ===== RUN BOT =====
bot = ApplicationBuilder().token(TOKEN).build()
bot.add_handler(CommandHandler("start", start))
bot.add_handler(CallbackQueryHandler(button, pattern='^(shopping|wallet|notes|back)$'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Слушаем порт {port} и ждём Telegram webhook...")
    app.run(host="0.0.0.0", port=port)
