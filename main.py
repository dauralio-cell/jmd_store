from flask import Flask, render_template, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd
import re, math, os

# 🔹 Настройки
BOT_TOKEN = "8436596875:AAGvAemmT1ESKk7dflMbTbjzz_n49LRckEc"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__, static_folder='static', template_folder='templates')

# ======= Excel каталог =======
EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'catalog.xlsx')

def parse_gender(name):
    name_l = name.lower()
    if any(x in name_l for x in ('women', 'woman', 'wmn', 'lady', 'girl')):
        return 'women'
    if any(x in name_l for x in ('men', 'man', 'mns', 'male', 'boy')):
        return 'men'
    return 'unisex'

def parse_size(name):
    m = re.search(r'(\d{1,2}(?:[\.,]\d)?)\s*$', name)
    if m:
        return m.group(1).replace(',', '.')
    m2 = re.search(r'(\d{1,2}(?:[\.,]\d)?)', name)
    if m2:
        return m2.group(1).replace(',', '.')
    return ''

def load_products():
    df = pd.read_excel(EXCEL_PATH, header=None)
    for i in range(3 - df.shape[1]):
        df[i] = ''
    df = df[[0, 1, 2]]
    df.columns = ['name', 'brand', 'price_raw']
    products = []

    for _, row in df.iterrows():
        name = str(row['name']).strip()
        brand = str(row['brand']).strip() if not pd.isna(row['brand']) else ''
        price_raw = row['price_raw']

        try:
            price = float(price_raw)
        except Exception:
            s = re.sub(r'[^0-9.,]', '', str(price_raw))
            s = s.replace(',', '.')
            price = float(s) if s else 0

        size = parse_size(name)
        gender = parse_gender(name)
        display_price = int(math.ceil(price * 0.85)) if price else 0

        products.append({
            'name': name or 'Без названия',
            'brand': brand or 'Unknown',
            'price': int(price),
            'display_price': display_price,
            'size': size,
            'gender': gender,
            'image': '/static/images/placeholder.svg'
        })
    return products

# ======= Flask web =======
@app.route('/')
def index():
    products = load_products()
    brands = sorted({p['brand'] for p in products if p['brand']})
    sizes = sorted({p['size'] for p in products if p['size']})
    genders = sorted({p['gender'] for p in products if p['gender']})

    brand = request.args.get('brand', '').strip()
    gender = request.args.get('gender', '').strip()
    size = request.args.get('size', '').strip()

    filtered = products
    if brand:
        filtered = [p for p in filtered if p['brand'].lower() == brand.lower()]
    if gender:
        filtered = [p for p in filtered if p['gender'].lower() == gender.lower()]
    if size:
        filtered = [p for p in filtered if p['size'] == size]

    return render_template('index.html',
                           products=filtered,
                           brands=brands,
                           sizes=sizes,
                           genders=genders,
                           selected_brand=brand,
                           selected_gender=gender,
                           selected_size=size)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/setwebhook")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://jmd-store.onrender.com/" + BOT_TOKEN)
    return "Webhook установлен успешно ✅", 200

# ======= Telegram Bot =======
@bot.message_handler(commands=['start'])
def cmd_start(message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Открыть каталог", url="https://jmd-store.onrender.com"))
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Добро пожаловать в магазин DENE.\n"
        f"Нажми, чтобы открыть каталог 👇",
        reply_markup=kb
    )

# ======= Запуск =======
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
