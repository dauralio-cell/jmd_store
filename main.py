import streamlit as st
import pandas as pd
import glob
import os
import re
import base64
from PIL import Image
import io
import time

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# Убираем ВСЕ отступы Streamlit
st.markdown("""
<style>
.main .block-container {
    padding-top: 0px;
    padding-bottom: 0px;
    padding-left: 0px;
    padding-right: 0px;
    max-width: 100%;
}
section.main > div:first-child {
    padding-top: 0px;
}
[data-testid="stVerticalBlock"] {
    gap: 0rem;
}

/* Стили для белой кнопки - контур как раньше, при наведении черный */
.stButton button {
    background-color: white !important;
    color: black !important;
    border: 2px solid #e5e5e5 !important; /* Серый контур как раньше */
    border-radius: 8px !important;
    padding: 10px 16px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    margin-top: 5px !important;
    margin-bottom: 5px !important;
}

.stButton button:hover {
    background-color: #f8f9fa !important;
    border-color: #000000 !important; /* ЧЕРНЫЙ контур при наведении */
    color: #000000 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

/* Дополнительные отступы для разделения карточек */
.product-card {
    margin-bottom: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# --- Инициализация корзины ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- Обложка и хедер ---
st.image("data/images/banner.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Кнопка корзины вверху ---
col1, col2, col3 = st.columns([1, 3, 1])
with col3:
    cart_count = len(st.session_state.cart)
    cart_text = f"Корзина ({cart_count})" if cart_count > 0 else "Корзина"
    if st.button(cart_text, use_container_width=True):
        st.switch_page("pages/3_Корзина.py")

# --- Пути и константы ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Функция округления цены до тысяч ---
def format_price(price):
    """Округляет цену до тысяч и форматирует с пробелами"""
    try:
        rounded_price = round(float(price) / 1000) * 1000
        return f"{rounded_price:,.0f} ₸".replace(",", " ")
    except (ValueError, TypeError):
        return "0 ₸"

# --- Функция проверки наличия товара ---
def is_product_in_stock(df, brand, model, color):
    """Проверяет, есть ли хотя бы один размер товара в наличии"""
    try:
        product_rows = df[
            (df['brand'] == brand) & 
            (df['model_clean'] == model) & 
            (df['color'] == color)
        ]
        
        for _, row in product_rows.iterrows():
            us_size = str(row['size US']).strip()
            in_stock = str(row.get('in stock', 'yes')).strip().lower()
            
            if us_size and us_size != "nan" and us_size != "" and in_stock == 'yes':
                return True
        
        return False
    except:
        return False

# --- Функция получения минимальной цены для товара ---
def get_min_price_for_product(df, brand, model, color):
    """Возвращает минимальную цену из доступных размеров товара"""
    try:
        # Сначала проверяем наличие
        if not is_product_in_stock(df, brand, model, color):
            return None
        
        # Находим все строки с этим товаром
        product_rows = df[
            (df['brand'] == brand) & 
            (df['model_clean'] == model) & 
            (df['color'] == color)
        ]
        
        min_price = None
        
        for _, row in product_rows.iterrows():
            us_size = str(row['size US']).strip()
            in_stock = str(row.get('in stock', 'yes')).strip().lower()
            price_str = str(row['price']).strip()
            
            # Проверяем наличие
            if us_size and us_size != "nan" and us_size != "" and in_stock == 'yes':
                try:
                    if price_str and price_str != "nan" and price_str != "":
                        price = float(price_str)
                        if min_price is None or price < min_price:
                            min_price = price
                except ValueError:
                    continue
        
        if min_price is None:
            return None
        
        # Округляем до тысяч
        return round(min_price / 1000) * 1000
    except Exception as e:
        return None

# --- Функция получения размеров в наличии для товара ---
def get_available_sizes_for_product(df, brand, model, color):
    """Возвращает размеры товара, которые есть в наличии"""
    try:
        product_rows = df[
            (df['brand'] == brand) & 
            (df['model_clean'] == model) & 
            (df['color'] == color)
        ]
        
        available_sizes = []
        for _, row in product_rows.iterrows():
            us_size = str(row['size US']).strip()
            in_stock = str(row.get('in stock', 'yes')).strip().lower()
            
            # Проверяем наличие
            if us_size and us_size != "nan" and us_size != "" and in_stock == 'yes':
                if us_size not in available_sizes:
                    available_sizes.append(us_size)
        
        return sort_sizes(available_sizes)
    except:
        return []

# --- Таблица конверсии размеров US ↔ EU ---
size_conversion = {
    "1": "34", "2": "35", "3": "36", "4": "37", "5": "38",
    "6": "39", "7": "40", "8": "41", "9": "42", "10": "43",
    "11": "44", "12": "45", "13": "46",
    "7.0": "40", "7.5": "40.5", "8.0": "41", "8.5": "42", 
    "9.0": "42.5", "9.5": "43", "10.0": "43.5", "10.5": "44",
    "11.0": "44.5", "11.5": "45", "12.0": "45.5", "12.5": "46"
}

def get_eu_sizes(us_sizes_str):
    """Конвертирует US размеры в EU размеры"""
    if not us_sizes_str or us_sizes_str == "":
        return ""
    
    us_sizes = [size.strip() for size in us_sizes_str.split(",")]
    eu_sizes = []
    
    for us_size in us_sizes:
        # Сначала ищем точное совпадение
        if us_size in size_conversion:
            eu_sizes.append(size_conversion[us_size])
        # Пробуем убрать .0 для целых чисел
        elif us_size.endswith('.0'):
            base_size = us_size[:-2]
            if base_size in size_conversion:
                eu_sizes.append(size_conversion[base_size])
        else:
            # Если не нашли, оставляем US размер
            eu_sizes.append(us_size)
    
    unique_eu_sizes = []
    for size in eu_sizes:
        if size not in unique_eu_sizes:
            unique_eu_sizes.append(size)
    return " ".join(unique_eu_sizes)

def sort_sizes(size_list):
    """Сортирует размеры правильно: числа по значению, строки по алфавиту"""
    numeric_sizes = []
    string_sizes = []
    
    for size in size_list:
        clean_size = str(size).strip()
        try:
            base_num = float(clean_size)
            numeric_sizes.append((base_num, clean_size))
        except:
            string_sizes.append(clean_size)
    
    numeric_sizes.sort(key=lambda x: x[0])
    return [size[1] for size in numeric_sizes] + sorted(string_sizes)

def get_available_sizes_for_filter(df):
    """Получает доступные US размеры для фильтра"""
    in_stock_df = df[df.get('in stock', 'yes').str.lower() == 'yes']
    all_sizes = in_stock_df["size US"].dropna().unique().tolist()
    filtered_sizes = []
    for size in all_sizes:
        clean_size = str(size).strip()
        if not clean_size or clean_size == "nan":
            continue
        try:
            base_num = float(clean_size)
            if 5 <= base_num <= 11:
                filtered_sizes.append(clean_size)
        except:
            continue
    unique_sizes = list(dict.fromkeys(filtered_sizes))
    return sort_sizes(unique_sizes)

def get_available_eu_sizes_for_filter(df):
    """Получает доступные EU размеры для фильтра"""
    in_stock_df = df[df.get('in stock', 'yes').str.lower() == 'yes']
    all_sizes = in_stock_df["size US"].dropna().unique().tolist()
    eu_sizes = []
    
    for size in all_sizes:
        clean_size = str(size).strip()
        if not clean_size or clean_size == "nan":
            continue
        
        # Конвертируем в EU размер
        if clean_size in size_conversion:
            eu_size = size_conversion[clean_size]
        elif clean_size.endswith('.0'):
            base_size = clean_size[:-2]
            eu_size = size_conversion.get(base_size, clean_size)
        else:
            eu_size = clean_size
        
        try:
            eu_num = float(eu_size)
            # Фильтруем по диапазону EU размеров (примерно 37-46)
            if 37 <= eu_num <= 46:
                eu_sizes.append(eu_size)
        except:
            continue
    
    unique_eu_sizes = list(dict.fromkeys(eu_sizes))
    return sort_sizes(unique_eu_sizes)

@st.cache_data(ttl=60)
def load_data():
    try:
        file_mtime = os.path.getmtime(CATALOG_PATH)
        st.sidebar.write(f"Файл обновлен: {time.ctime(file_mtime)}")
        all_sheets = pd.read_excel(CATALOG_PATH, sheet_name=None)
        processed_dfs = []
        for sheet_name, sheet_data in all_sheets.items():
            sheet_data = sheet_data.fillna("")
            sheet_data['brand'] = sheet_data['brand'].replace('', pd.NA).ffill()
            sheet_data['model'] = sheet_data['model'].replace('', pd.NA).ffill()
            sheet_data['gender'] = sheet_data['gender'].replace('', pd.NA).ffill()
            sheet_data['color'] = sheet_data['color'].replace('', pd.NA).ffill()
            sheet_data['image'] = sheet_data['image'].replace('', pd.NA)
            sheet_data['size US'] = sheet_data['size US'].astype(str).str.strip()
            sheet_data["model_clean"] = sheet_data["model"].apply(
                lambda x: re.sub(r'\([^)]*\)', '', str(x)).strip() if pd.notna(x) else ""
            )
            processed_dfs.append(sheet_data)
        df = pd.concat(processed_dfs, ignore_index=True)
        df = df[(df['brand'] != '') & (df['model_clean'] != '')]
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

df = load_data()

st.sidebar.write("ДИАГНОСТИКА:")
st.sidebar.write("Всего товаров:", len(df))
st.sidebar.write("Уникальные бренды:", df["brand"].nunique())
st.sidebar.write("Уникальные модели:", df["model_clean"].nunique())

# --- Фильтры ---
st.divider()
st.markdown("### Фильтр каталога")

col1, col2, col3, col4, col5 = st.columns(5)

brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
if brand_filter != "Все":
    brand_models = sorted(df[df["brand"] == brand_filter]["model_clean"].unique().tolist())
else:
    brand_models = sorted(df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + brand_models)
available_us_sizes = get_available_sizes_for_filter(df)
available_eu_sizes = get_available_eu_sizes_for_filter(df)

# Два фильтра размеров: US и EU
size_filter_us = col3.selectbox("Размер (US)", ["Все"] + available_us_sizes)
size_filter_eu = col4.selectbox("Размер (EU)", ["Все"] + available_eu_sizes)

gender_filter = col5.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col5.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()), key="color_filter")

filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]

# Фильтр по размеру US
if size_filter_us != "Все":
    filtered_df = filtered_df[filtered_df["size US"] == size_filter_us]

# Фильтр по размеру EU
if size_filter_eu != "Все":
    # Для фильтрации по EU размеру нужно конвертировать US в EU
    filtered_by_eu = []
    for idx, row in filtered_df.iterrows():
        us_size = str(row['size US']).strip()
        if us_size and us_size != "nan" and us_size != "":
            # Конвертируем US в EU
            if us_size in size_conversion:
                eu_size = size_conversion[us_size]
            elif us_size.endswith('.0'):
                base_size = us_size[:-2]
                eu_size = size_conversion.get(base_size, us_size)
            else:
                eu_size = us_size
            
            if eu_size == size_filter_eu:
                filtered_by_eu.append(idx)
    
    filtered_df = filtered_df.loc[filtered_by_eu]

# Фильтр по полу с учетом unisex
if gender_filter != "Все":
    if gender_filter == "women":
        filtered_df = filtered_df[filtered_df["gender"].isin(["women", "unisex"])]
    elif gender_filter == "men":
        filtered_df = filtered_df[filtered_df["gender"].isin(["men", "unisex"])]
    else:
        filtered_df = filtered_df[filtered_df["gender"] == gender_filter]

if color_filter != "Все":
    filtered_df = filtered_df[filtered_df["color"] == color_filter]

def has_any_size_in_stock(group):
    return any(
        str(row.get('in stock', 'yes')).strip().lower() == 'yes'
        for _, row in group.iterrows()
        if str(row['size US']).strip() and str(row['size US']).strip() != "nan"
    )

filtered_df = filtered_df.groupby(['brand', 'model_clean', 'color']).filter(has_any_size_in_stock)

st.divider()
st.markdown("## Каталог товаров")

if len(filtered_df) == 0:
    st.warning("Товары по выбранным фильтрам не найдены")
else:
    st.write(f"**Найдено товаров: {len(filtered_df)}**")

    def get_first_with_image(group):
        for _, row in group.iterrows():
            if row['image'] and pd.notna(row['image']) and str(row['image']).strip():
                return row
        return group.iloc[0]

    grouped_df = filtered_df.groupby(['brand', 'model_clean', 'color']).apply(get_first_with_image).reset_index(drop=True)

    # --- Отображение карточек товаров ---
    num_cols = 3
    rows = [grouped_df.iloc[i:i + num_cols] for i in range(0, len(grouped_df), num_cols)]

    for row_idx, row_df in enumerate(rows):
        cols = st.columns(num_cols)
        for col_idx, (_, row) in enumerate(row_df.iterrows()):
            col = cols[col_idx]
            with col:
                # Подготовка данных
                image_names = row["image"]
                image_path = get_image_path(image_names)
                image_base64 = optimize_image_for_telegram(image_path, target_size=(400, 400))
                
                # Проверяем наличие товара
                is_in_stock = is_product_in_stock(
                    df, 
                    row['brand'], 
                    row['model_clean'], 
                    row['color']
                )
                
                # Получаем минимальную цену для этого товара
                min_price = get_min_price_for_product(
                    df, 
                    row['brand'], 
                    row['model_clean'], 
                    row['color']
                )
                
                # Получаем размеры в наличии для этого товара
                available_sizes = get_available_sizes_for_product(
                    df, 
                    row['brand'], 
                    row['model_clean'], 
                    row['color']
                )
                
                # Конвертируем размеры в EU, если есть US размеры
                if available_sizes:
                    eu_sizes = get_eu_sizes(",".join(available_sizes))
                else:
                    eu_sizes = "Нет в наличии"
                
                # Форматирование данных
                if is_in_stock and min_price is not None:
                    price_formatted = f"от {int(min_price):,} ₸".replace(",", " ")
                elif is_in_stock:
                    price_formatted = "В наличии"  # если есть в наличии, но цена не найдена
                else:
                    price_formatted = "Нет в наличии"
                    
                brand = str(row['brand'])
                model = str(row['model_clean'])
                color = str(row['color'])
                
                # Карточка товара
                st.markdown(f"""
                <div class="product-card">
                <div style='
                    border: 1px solid #e5e5e5;
                    border-radius: 12px 12px 0 0;
                    padding: 0;
                    background: #fff;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                '>
                    <img src="data:image/jpeg;base64,{image_base64}"
                         style='
                            width: 100%;
                            height: 250px;
                            object-fit: contain;
                            display: block;
                            background: white;
                            padding: 10px;
                         '>
                    <div style='padding: 15px; padding-bottom: 20px;'>
                        <div style='font-size: 12px; color: #777; margin-bottom: 4px;'>{brand}</div>
                        <div style='font-size: 15px; font-weight: 600; color: #222; margin-bottom: 4px; line-height: 1.3;'>
                            {model} '{color}'
                        </div>
                        <div style='font-size: 11px; color: #666; margin-bottom: 8px;'>EU: {eu_sizes}</div>
                        <div style='font-size: 17px; font-weight: 700; color: #000;'>{price_formatted}</div>
                    </div>
                </div>
                
                <!-- Отдельный блок для кнопки -->
                <div style='
                    background: white;
                    border: 1px solid #e5e5e5;
                    border-top: none;
                    border-radius: 0 0 12px 12px;
                    padding: 10px;
                    margin-top: -1px;
                '>
                </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Кнопка "Подробнее" с серым контуром, при наведении - черным
                if st.button("Подробнее", 
                            key=f"details_{row_idx}_{col_idx}_{hash(str(row['brand'])+str(row['model_clean'])+str(row['color']))}", 
                            use_container_width=True):
                    st.session_state.product_data = dict(row)
                    st.switch_page("pages/2_Детали_товара.py")
                
                # Пространство между карточками
                st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# --- ФУТЕР ---
from components.documents import documents_footer
documents_footer()