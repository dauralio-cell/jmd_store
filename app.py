from flask import Flask, render_template, request, url_for
import pandas as pd
import re, math, os

app = Flask(__name__, static_folder='static', template_folder='templates')

# path to excel (automatically loaded)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'catalog.xlsx')

def parse_gender(name):
    name_l = name.lower()
    if any(x in name_l for x in ('women', 'woman', 'wmn', 'wmns', 'lady', 'girl')):
        return 'women'
    if any(x in name_l for x in ('men', 'man', 'mns', 'male', 'boy')):
        return 'men'
    return 'unisex'

def parse_size(name):
    # try to find a size at the end or near the end: look for numbers like 8, 8.5, 42, 42.5
    m = re.search(r'(\d{1,2}(?:[\.,]\d)?)\s*$', name)
    if m:
        return m.group(1).replace(',', '.')
    # fallback: search any size-like token
    m2 = re.search(r'(\d{1,2}(?:[\.,]\d)?)', name)
    if m2:
        return m2.group(1).replace(',', '.')
    return ''

def load_products():
    df = pd.read_excel(EXCEL_PATH, header=None)
    # Убедимся, что есть хотя бы 3 колонки
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
            import re
            s = re.sub(r'[^0-9.,]', '', str(price_raw))
            s = s.replace(',', '.')
            try:
                price = float(s) if s else float('nan')
            except:
                price = float('nan')

        # Если цена не число — ставим 0
        if pd.isna(price):
            price_val = 0.0
        else:
            price_val = float(price)

        size = parse_size(name)
        gender = parse_gender(name)

        # Безопасный расчёт цены со скидкой
        if price_val and price_val > 0:
            display_price = int(math.ceil(price_val * 0.85))
        else:
            display_price = 0

        products.append({
            'name': name or 'Без названия',
            'brand': brand or 'Unknown',
            'price': int(price_val) if price_val else 0,
            'display_price': display_price,
            'size': size,
            'gender': gender,
            'image': '/static/images/placeholder.svg'
        })

    return products

@app.route('/')
def index():
    products = load_products()
    # build filter options
    brands = sorted({p['brand'] for p in products if p['brand']})
    sizes = sorted({p['size'] for p in products if p['size']}, key=lambda x: float(x) if x and x.replace('.', '', 1).isdigit() else 999)
    genders = sorted({p['gender'] for p in products if p['gender']})

    # get filters from query
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
