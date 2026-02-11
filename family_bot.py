# family_bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from collections import defaultdict
import asyncio

# ================== НАСТРОЙКИ ==================
TOKEN = "8549280564:AAHowQlkn6ucbpvVV3CAvtPn_ufa6c_DXNc"
USER_IDS = {
    "me": 334637350,
    "wife": 663322435
}

# ================== ЛОГИ ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# ================== ХРАНЕНИЕ ДАННЫХ ==================
wallet = defaultdict(float)
purchases = []
notes = []

# ================== КНОПКИ ==================
main_menu_buttons = [
    [InlineKeyboardButton("💰 Кошелёк", callback_data="wallet")],
    [InlineKeyboardButton("🛒 Список покупок", callback_data="shopping")],
    [InlineKeyboardButton("📝 Заметки", callback_data="notes")],
]

# ================== ФУНКЦИИ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in USER_IDS.values():
        await update.message.reply_text("Доступ запрещен.")
        return
    await update.message.reply_text(
        "Привет! Это семейный бот.\nВыберите раздел:", 
        reply_markup=InlineKeyboardMarkup(main_menu_buttons)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "wallet":
        text = "💰 Кошелёк:\n"
        for user, amount in wallet.items():
            name = "Я" if user == USER_IDS["me"] else "Жена"
            text += f"{name}: ${amount:.2f}\n"
        text += "\nВведите командой /add [сумма] для внесения денег или /take [сумма] для списания."
        await query.edit_message_text(text)

    elif query.data == "shopping":
        text = "🛒 Список покупок:\n"
        if purchases:
            for i, item in enumerate(purchases, 1):
                text += f"{i}. {item}\n"
        else:
            text += "Список пуст."
        text += "\nДобавить: /buy [название]"
        await query.edit_message_text(text)

    elif query.data == "notes":
        text = "📝 Заметки:\n"
        if notes:
            for i, note in enumerate(notes, 1):
                text += f"{i}. {note}\n"
        else:
            text += "Заметок нет."
        text += "\nДобавить: /note [текст]"
        await query.edit_message_text(text)

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /add [сумма]")
        return

    user = update.effective_user.id
    wallet[user] += amount
    await update.message.reply_text(f"Добавлено ${amount:.2f} к вашему кошельку.")

async def take_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Использование: /take [сумма]")
        return

    user = update.effective_user.id
    wallet[user] -= amount
    await update.message.reply_text(f"Списано ${amount:.2f} с вашего кошелька.")

async def add_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = " ".join(context.args)
    if not item:
        await update.message.reply_text("Использование: /buy [название]")
        return
    purchases.append(item)
    await update.message.reply_text(f"Добавлено в покупки: {item}")

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = " ".join(context.args)
    if not note:
        await update.message.reply_text("Использование: /note [текст]")
        return
    notes.append(note)
    await update.message.reply_text(f"Заметка добавлена: {note}")

# ================== ЗАПУСК ==================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_money))
    app.add_handler(CommandHandler("take", take_money))
    app.add_handler(CommandHandler("buy", add_purchase))
    app.add_handler(CommandHandler("note", add_note))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Слушаем порт 10000...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
