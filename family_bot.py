from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from tinydb import TinyDB, Query

# ====== НАСТРОЙКА ======
TOKEN = "8549280564:AAHowQlkn6ucbpvVV3CAvtPn_ufa6c_DXNc"
ALLOWED_USERS = [334637350, 663322435]  # только вы с женой
db = TinyDB('data.json')
shopping_table = db.table('shopping')
expenses_table = db.table('expenses')
notes_table = db.table('notes')

# ====== МЕНЮ ======
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Список покупок 🛒", callback_data='shopping')],
        [InlineKeyboardButton("Расходы 💰", callback_data='expenses')],
        [InlineKeyboardButton("Заметки 📋", callback_data='notes')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У тебя нет доступа к этому боту.")
        return
    await update.message.reply_text("Привет! Я твой семейный бот. Выбирай меню:", reply_markup=main_menu_keyboard())

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
    
    elif query.data == 'expenses':
        keyboard = [
            [InlineKeyboardButton("Добавить расход", callback_data='add_expense')],
            [InlineKeyboardButton("Показать расходы", callback_data='show_expenses')],
            [InlineKeyboardButton("Обнулить расходы", callback_data='reset_expenses')],
            [InlineKeyboardButton("Назад", callback_data='back')]
        ]
        await query.edit_message_text("Расходы:", reply_markup=InlineKeyboardMarkup(keyboard))
    
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

# ====== ДОБАВЛЕНИЕ И ПРОСМОТР ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У тебя нет доступа к этому боту.")
        return

    text = update.message.text
    state = context.user_data.get('state')

    if state == 'adding_shopping':
        shopping_table.insert({'item': text})
        await update.message.reply_text(f"✅ Товар добавлен: {text}")
        context.user_data['state'] = None
    elif state == 'adding_expense':
        try:
            amount = float(text)
            expenses_table.insert({'amount': amount})
            await update.message.reply_text(f"✅ Расход добавлен: {amount} грн")
        except:
            await update.message.reply_text("❌ Введи число!")
        context.user_data['state'] = None
    elif state == 'adding_note':
        notes_table.insert({'note': text})
        await update.message.reply_text(f"✅ Заметка добавлена: {text}")
        context.user_data['state'] = None
    elif state == 'del_shopping':
        items = shopping_table.all()
        if text.isdigit() and 0 < int(text) <= len(items):
            shopping_table.remove(doc_ids=[items[int(text)-1].doc_id])
            await update.message.reply_text("✅ Товар удалён")
        else:
            await update.message.reply_text("❌ Неверный номер")
        context.user_data['state'] = None
    elif state == 'del_note':
        notes = notes_table.all()
        if text.isdigit() and 0 < int(text) <= len(notes):
            notes_table.remove(doc_ids=[notes[int(text)-1].doc_id])
            await update.message.reply_text("✅ Заметка удалена")
        else:
            await update.message.reply_text("❌ Неверный номер")
        context.user_data['state'] = None

# ====== ОБРАБОТКА CALLBACK ДЛЯ ВВОДА ======
async def callback_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id not in ALLOWED_USERS:
        await query.answer("❌ У тебя нет доступа.", show_alert=True)
        return
    await query.answer()

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

    elif query.data == 'add_expense':
        await query.edit_message_text("Введи сумму расхода:")
        context.user_data['state'] = 'adding_expense'
    elif query.data == 'show_expenses':
        items = expenses_table.all()
        total = sum(x['amount'] for x in items)
        await query.edit_message_text(f"Сумма расходов: {total} грн")
    elif query.data == 'reset_expenses':
        expenses_table.truncate()
        await query.edit_message_text("✅ Расходы обнулены")

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
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern='^(shopping|expenses|notes|back)$'))
    app.add_handler(CallbackQueryHandler(callback_add, pattern='^(add_shopping|show_shopping|del_shopping|add_expense|show_expenses|reset_expenses|add_note|show_notes|del_note)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()
