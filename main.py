from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, get_all_products, add_product

# 🔹 Настройки
BOT_TOKEN = "8436596875:AAGvAemmT1ESKk7dflMbTbjzz_n49LRckEc"
WEBHOOK_URL = f"https://jmd-store.onrender.com/{BOT_TOKEN}"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===================================================
# Flask — сайт и вебхук
# ===================================================
@app.route("/")
def home():
    return "Добро пожаловать в магазин DENE! 🛍"

@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/setwebhook")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    return f"Webhook установлен успешно ✅\n{WEBHOOK_URL}", 200

# ===================================================
# Telegram Bot
# ===================================================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Открыть каталог", callback_data="catalog"))
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Добро пожаловать в магазин DENE.\n"
        f"Выбери действие ниже 👇",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data == "catalog")
def show_catalog(call):
    products = [
        ("Nike Air Force 1", "65 000 тг", "Размеры 40–45, белые"),
        ("Adidas Yeezy Boost 350", "90 000 тг", "Размеры 39–44, серые"),
        ("New Balance 550", "75 000 тг", "Размеры 40–45, бело-зеленые")
    ]

    bot.send_message(call.message.chat.id, "👟 Каталог DENE:\n")

    for name, price, info in products:
        text = f"🏷 {name}\n💰 Цена: {price}\n📏 {info}"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛒 Заказать", callback_data=f"order_{name}"))
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def order_product(call):
    product_name = call.data.replace("order_", "")
    bot.send_message(call.message.chat.id, f"✅ Товар «{product_name}» добавлен в корзину (тест).")

# ===================================================
# Запуск
# ===================================================
if __name__ == "__main__":
    init_db()
    print("✅ База данных готова")
    app.run(host="0.0.0.0", port=5000)