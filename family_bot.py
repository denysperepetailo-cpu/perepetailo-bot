import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
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
    return '', 204  # чтобы лишние 404 не было

# ===== HELPER ФУНКЦИИ =====
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Список покупок 🛒", callback_data='shopping')],
        [InlineKeyboardButton("Общий кошелёк $", callback_data='wallet')],
        [InlineKeyboardButton("Заметки 📋", callback_data='notes')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== КОМАНДА /START =====
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

# ===== CALLBACK ДЛЯ ВВОДА ДАННЫХ =====
async def callback_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in ALLOWED_USERS:
        await query.answer("❌ У тебя нет доступа.", show_alert=True)
        return
    await query.answer()

    state = context.user_data.get('state')
    text = query.message.text

    # ПОКУПКИ
    if query.data == 'add_shopping':
        await query.edit_message_text("Напиши название товара:")
        context.user_data['state'] = 'adding_shopping'
    elif query.data == 'show_shopping':
        items = shopping_table.all()
        if not items:
            await query.edit_message_text("Список пуст 🛒")
        else:
            msg = "\n".join([f"{i+1}. {x['item']}" for i, x in enumerate(items)])
            await query.edit_message_text(f"Список покупок:\n{msg}")
    elif query.data == 'del_shopping':
        items = shopping_table.all()
        if not items:
            await query.edit_message_text("Список пуст 🛒")
        else:
            msg = "\n".join([f"{i+1}. {x['item']}" for i, x in enumerate(items)])
            await query.edit_message_text(f"Напиши номер товара для удаления:\n{msg}")
            context.user_data['state'] = 'del_shopping'

    # КОШЕЛЁК
    elif query.data == 'show_wallet':
        items = wallet_table.all()
        balance = sum(x['amount'] if x['type']=='add' else -x['amount'] for x in items)
        if not items:
            await query.edit_message_text(f"Баланс: ${balance}\nИстория пустая")
        else:
            history = "\n".join([f"{x['time']} - {x['user']} {'внес' if x['type']=='add' else 'снял'} ${x['amount']}" for x in items])
            await query.edit_message_text(f"Баланс: ${balance}\nИстория:\n{history}")
    elif query.data == 'add_wallet':
        await query.edit_message_text("Введи сумму для внесения $:")
        context.user_data['state'] = 'adding_wallet'
    elif query.data == 'take_wallet':
        await query.edit_message_text("Введи сумму для снятия $:")
        context.user_data['state'] = 'taking_wallet'

    # ЗАМЕТКИ
    elif query.data == 'add_note':
        await query.edit_message_text("Напиши текст заметки:")
        context.user_data['state'] = 'adding_note'
    elif query.data == 'show_notes':
        items = notes_table.all()
        if not items:
            await query.edit_message_text("Нет заметок 📋")
        else:
            msg = "\n".join([f"{i+1}. {x['note']}" for i, x in enumerate(items)])
            await query.edit_message_text(f"Заметки:\n{msg}")
    elif query.data == 'del_note':
        items = notes_table.all()
        if not items:
            await query.edit_message_text("Нет заметок 📋")
        else:
            msg = "\n".join([f"{i+1}. {x['note']}" for i, x in enumerate(items)])
            await query.edit_message_text(f"Напиши номер заметки для удаления:\n{msg}")
            context.user_data['state'] = 'del_note'

# ===== RUN BOT =====
bot = ApplicationBuilder().token(TOKEN).build()
bot.add_handler(CommandHandler("start", start))
bot.add_handler(CallbackQueryHandler(button, pattern='^(shopping|wallet|notes|back)$'))
bot.add_handler(CallbackQueryHandler(callback_add, pattern='^(add_shopping|show_shopping|del_shopping|show_wallet|add_wallet|take_wallet|add_note|show_notes|del_note)$'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Слушаем порт {port} и ждём Telegram webhook...")
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    bot.run_polling()  # только для локальной проверки, webhook реально работает через Flask
