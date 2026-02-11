import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from tinydb import TinyDB
from datetime import datetime

# ====== НАСТРОЙКА ======
TOKEN = "8549280564:AAHowQlkn6ucbpvVV3CAvtPn_ufa6c_DXNc"
ALLOWED_USERS = [334637350, 663322435]  # только вы с женой

db = TinyDB('data.json')
shopping_table = db.table('shopping')
wallet_table = db.table('wallet')
notes_table = db.table('notes')

# ====== FLASK ДЛЯ RENDER ======
app = Flask(__name__)

@app.route("/")
def home():
    return "Бот запущен и работает!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ====== МЕНЮ ======
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Список покупок 🛒", callback_data='shopping')],
        [InlineKeyboardButton("Общий кошелёк $", callback_data='wallet')],
        [InlineKeyboardButton("Заметки 📋", callback_data='notes')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У тебя нет доступа к этому боту.")
        return
    await update.message.reply_text("Привет! Выбирай меню:", reply_markup=main_menu_keyboard())

# ====== CALLBACK ======
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id not in ALLOWED_USERS:
        await query.answer("❌ У тебя нет доступа.", show_alert=True)
        return
    await query.answer()

    if query.data == 'shopping':
        keyboard = [
            [InlineKeyboardButton("Добавить товар", callback_data='add_shopping')],
            [InlineKeyboardButton("Показать список", callback_data='show_shopping')],
            [InlineKeyboardButton("Удалить товар", callback_data='del_shopping')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Список покупок:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'wallet':
        keyboard = [
            [InlineKeyboardButton("Посмотреть баланс", callback_data='show_wallet')],
            [InlineKeyboardButton("Внести $", callback_data='add_wallet')],
            [InlineKeyboardButton("Снять $", callback_data='take_wallet')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Общий кошелёк $:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'notes':
        keyboard = [
            [InlineKeyboardButton("Добавить заметку", callback_data='add_note')],
            [InlineKeyboardButton("Показать заметки", callback_data='show_notes')],
            [InlineKeyboardButton("Удалить заметку", callback_data='del_note')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Заметки:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'back':
        await query.edit_message_text("Главное меню:", reply_markup=main_menu_keyboard())

# ====== ОБРАБОТКА ВВОДА ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У тебя нет доступа к боту.")
        return

    text = update.message.text
    state = context.user_data.get('state')

    # ===== ПОКУПКИ =====
    if state == 'adding_shopping':
        shopping_table.insert({'item': text})
        await update.message.reply_text(f"✅ Товар добавлен: {text}")
        context.user_data['state'] = None
    elif state == 'del_shopping':
        items = shopping_table.all()
        if text.isdigit() and 0 < int(text) <= len(items):
            shopping_table.remove(doc_ids=[items[int(text)-1].doc_id])
            await update.message.reply_text("✅ Товар удалён")
        else:
            await update.message.reply_text("❌ Неверный номер")
        context.user_data['state'] = None

    # ===== КОШЕЛЁК $ =====
    elif state == 'adding_wallet':
        try:
            amount = float(text)
            wallet_table.insert({
                'type': 'add',
                'amount': amount,
                'user': update.effective_user.first_name,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            await update.message.reply_text(f"✅ Внесено ${amount}")
        except:
            await update.message.reply_text("❌ Введи число!")
        context.user_data['state'] = None

    elif state == 'taking_wallet':
        try:
            amount = float(text)
            wallet_table.insert({
                'type': 'take',
                'amount': amount,
                'user': update.effective_user.first_name,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            await update.message.reply_text(f"✅ Снято ${amount}")
        except:
            await update.message.reply_text("❌ Введи число!")
        context.user_data['state'] = None

    # ===== ЗАМЕТКИ =====
    elif state == 'adding_note':
        notes_table.insert({'note': text})
        await update.message.reply_text(f"✅ Заметка добавлена: {text}")
        context.user_data['state'] = None
    elif state == 'del_note':
        items = notes_table.all()
        if text.isdigit() and 0 < int(text) <= len(items):
            notes_table.remove(doc_ids=[items[int(text)-1].doc_id])
            await update.message.reply_text("✅ Заметка удалена")
        else:
            await update.message.reply_text("❌ Неверный номер")
        context.user_data['state'] = None

# ====== CALLBACK ДЛЯ ВВОДА ======
async def callback_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id not in ALLOWED_USERS:
        await query.answer("❌ У тебя нет доступа.", show_alert=True)
        return
    await query.answer()

    # ===== ПОКУПКИ =====
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

    # ===== КОШЕЛЁК $ =====
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

    # ===== ЗАМЕТКИ =====
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

# ====== ЗАПУСК ======
if __name__ == '__main__':
    Thread(target=run_flask).start()  # HTTP сервер для Render
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button, pattern='^(shopping|wallet|notes|back)$'))
    app_bot.add_handler(CallbackQueryHandler(callback_add, pattern='^(add_shopping|show_shopping|del_shopping|show_wallet|add_wallet|take_wallet|add_note|show_notes|del_note)$'))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app_bot.run_polling()
