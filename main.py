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

# --- Таблица конверсии US → EU размеров (запасной вариант) ---
US_TO_EU_CONVERSION = {
    # Мужские размеры
    "5": "37", "5.5": "38", "6": "38.5", "6.5": "39", "7": "40",
    "7.5": "40.5", "8": "41", "8.5": "42", "9": "42.5", "9.5": "43",
    "10": "44", "10.5": "44.5", "11": "45", "11.5": "45.5", "12": "46",
    "12.5": "47", "13": "47.5", "14": "48.5",
    
    # Для значений с .0
    "5.0": "37", "6.0": "38.5", "7.0": "40", "8.0": "41", "9.0": "42.5",
    "10.0": "44", "11.0": "45", "12.0": "46", "13.0": "47.5",
    
    # Женские размеры
    "5W": "35.5", "5.5W": "36", "6W": "36.5", "6.5W": "37", "7W": "37.5",
    "7.5W": "38", "8W": "38.5", "8.5W": "39", "9W": "39.5", "9.5W": "40",
    "10W": "40.5", "10.5W": "41", "11W": "41.5"
}

# --- Функция для очистки размера от .0 ---
def clean_size(size_str):
    """Убирает .0 из размера, например 36.0 → 36"""
    if not size_str or size_str == "nan" or size_str == "":
        return ""
    
    clean_str = str(size_str).strip()
    
    # Убираем .0 в конце числа
    if clean_str.endswith('.0'):
        clean_str = clean_str[:-2]
    
    return clean_str

# --- Функция конверсии US → EU (запасной вариант) ---
def convert_us_to_eu(us_size):
    """Конвертирует US размер в EU размер (используется только если нет EU размера)"""
    if not us_size or us_size == "nan" or us_size == "":
        return ""
    
    us_clean = str(us_size).strip()
    
    # Сначала ищем точное совпадение
    if us_clean in US_TO_EU_CONVERSION:
        return clean_size(US_TO_EU_CONVERSION[us_clean])
    
    # Пробуем убрать .0 для целых чисел
    if us_clean.endswith('.0'):
        base_size = us_clean[:-2]
        if base_size in US_TO_EU_CONVERSION:
            return clean_size(US_TO_EU_CONVERSION[base_size])
    
    # Если размер не найден в таблице, возвращаем очищенный оригинальный
    return clean_size(us_clean)

# --- Функция получения EU размера ---
def get_eu_size(row):
    """Возвращает EU размер: сначала из колонки size EU, если нет - конвертирует из US"""
    # Пробуем получить EU размер из колонки size EU
    if 'size EU' in row:
        eu_size = str(row.get('size EU', '')).strip()
        if eu_size and eu_size != "nan" and eu_size != "":
            return clean_size(eu_size)
    
    # Если нет EU размера, конвертируем из US
    us_size = str(row.get('size US', '')).strip()
    if us_size and us_size != "nan" and us_size != "":
        return convert_us_to_eu(us_size)
    
    return ""

# --- Функция округления цены до тысяч ---
def format_price(price):
    """Округляет цену до тысяч и форматирует с пробелами"""
    try:
        rounded_price = round(float(price) / 1000) * 1000
        return f"{rounded_price:,.0f} ₸".replace(",", " ")
    except (ValueError, TypeError):
        return "0 ₸"

# --- Функция для работы с изображениями ---
def get_image_path(image_names):
    """Ищет изображение по имени из колонки image"""
    if (image_names is pd.NA or pd.isna(image_names) or not image_names or str(image_names).strip() == ""):
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    first_image_name = image_names_list[0]
    
    # Сначала ищем точное совпадение
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(IMAGES_PATH, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
    
    # Затем ищем частичное совпадение (начинается с)
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern_start = os.path.join(IMAGES_PATH, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    # Если ничего не нашли, используем fallback
    return os.path.join(IMAGES_PATH, "no_image.jpg")

def optimize_image_for_telegram(image_path, target_size=(800, 800)):
    try:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Сохраняем пропорции изображения
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Создаем новое изображение с белым фоном
            new_img = Image.new('RGB', target_size, (255, 255, 255))
            
            # Вычисляем позицию для центрирования
            x = (target_size[0] - img.size[0]) // 2
            y = (target_size[1] - img.size[1]) // 2
            
            # Вставляем изображение по центру
            new_img.paste(img, (x, y))
            
            buffer = io.BytesIO()
            new_img.save(buffer, format='JPEG', quality=90, optimize=True)
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")
    except Exception:
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
            with open(fallback, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")

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

# --- Функция получения EU размеров в наличии для товара ---
def get_available_eu_sizes_for_product(df, brand, model, color):
    """Возвращает EU размеры товара, которые есть в наличии"""
    try:
        product_rows = df[
            (df['brand'] == brand) & 
            (df['model_clean'] == model) & 
            (df['color'] == color)
        ]
        
        available_eu_sizes = []
        for _, row in product_rows.iterrows():
            in_stock = str(row.get('in stock', 'yes')).strip().lower()
            us_size = str(row['size US']).strip()
            
            # Проверяем наличие
            if us_size and us_size != "nan" and us_size != "" and in_stock == 'yes':
                # Получаем EU размер (из колонки или конвертируем)
                eu_size = get_eu_size(row)
                if eu_size and eu_size not in available_eu_sizes:
                    available_eu_sizes.append(eu_size)
        
        return sort_sizes(available_eu_sizes)
    except:
        return []

# --- Функция сортировки размеров ---
def sort_sizes(size_list):
    """Сортирует размеры правильно: числа по значению, строки по алфавиту"""
    numeric_sizes = []
    string_sizes = []
    
    for size in size_list:
        clean_size = str(size).strip()
        try:
            # Пробуем преобразовать в число
            base_num = float(clean_size)
            numeric_sizes.append((base_num, clean_size))
        except:
            string_sizes.append(clean_size)
    
    numeric_sizes.sort(key=lambda x: x[0])
    return [size[1] for size in numeric_sizes] + sorted(string_sizes)

# --- Функция получения доступных EU размеров для фильтра ---
def get_available_eu_sizes_for_filter(df):
    """Получает доступные EU размеры для фильтра"""
    in_stock_df = df[df.get('in stock', 'yes').str.lower() == 'yes']
    
    # Получаем EU размеры
    all_eu_sizes = []
    for _, row in in_stock_df.iterrows():
        us_size = str(row['size US']).strip()
        in_stock = str(row.get('in stock', 'yes')).strip().lower()
        
        if us_size and us_size != "nan" and us_size != "" and in_stock == 'yes':
            # Получаем EU размер (из колонки или конвертируем)
            eu_size = get_eu_size(row)
            if eu_size:
                all_eu_sizes.append(eu_size)
    
    # Убираем дубликаты и сортируем
    unique_eu_sizes = list(dict.fromkeys(all_eu_sizes))
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
            # Обрабатываем EU размеры, если колонка есть
            if 'size EU' in sheet_data.columns:
                sheet_data['size EU'] = sheet_data['size EU'].astype(str).str.strip()
            
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

available_eu_sizes = get_available_eu_sizes_for_filter(df)

# Фильтр по размеру EU
size_filter_eu = col3.selectbox("Размер (EU)", ["Все"] + available_eu_sizes)

gender_filter = col4.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col5.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()), key="color_filter")

filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]

# Фильтр по размеру EU
if size_filter_eu != "Все":
    # Фильтруем по EU размеру
    filtered_by_eu = []
    for idx, row in filtered_df.iterrows():
        us_size = str(row['size US']).strip()
        in_stock = str(row.get('in stock', 'yes')).strip().lower()
        
        if us_size and us_size != "nan" and us_size != "" and in_stock == 'yes':
            # Получаем EU размер для сравнения
            eu_size = get_eu_size(row)
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
                image_base64 = optimize_image_for_telegram(image_path, target_size=(800, 800))
                
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
                
                # Получаем EU размеры в наличии для этого товара
                available_eu_sizes = get_available_eu_sizes_for_product(
                    df, 
                    row['brand'], 
                    row['model_clean'], 
                    row['color']
                )
                
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
                
                # Форматируем EU размеры как в примере: "5.5 39 6.5 40 40.5 41 42 42.5 43"
                if available_eu_sizes:
                    eu_sizes_display = " ".join(available_eu_sizes)
                else:
                    eu_sizes_display = "Нет в наличии"
                
                # Карточка товара с увеличенным изображением
                st.markdown(f"""
                <div class="product-card">
                <div style='
                    border: 1px solid #e5e5e5;
                    border-radius: 12px 12px 0 0;
                    padding: 0;
                    background: #fff;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    height: 420px; /* Увеличили общую высоту карточки */
                    display: flex;
                    flex-direction: column;
                '>
                    <!-- Контейнер для изображения с фиксированной высотой -->
                    <div style='
                        height: 320px; /* УВЕЛИЧИЛИ ДО 320px для большего изображения */
                        width: 100%;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background: white;
                        overflow: hidden;
                        padding: 5px; /* Добавили небольшой внутренний отступ */
                    '>
                        <img src="data:image/jpeg;base64,{image_base64}"
                             style='
                                height: 95%; /* Занимает почти всю высоту контейнера */
                                max-width: 95%; /* Занимает почти всю ширину */
                                object-fit: contain; /* Показывает все изображение без обрезки */
                                display: block;
                             '>
                    </div>
                    <div style='
                        padding: 12px 15px 15px 15px; /* Уменьшили верхний отступ для компактности */
                        flex-grow: 1;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                    '>
                        <div>
                            <div style='font-size: 12px; color: #777; margin-bottom: 4px;'>{brand}</div>
                            <div style='font-size: 15px; font-weight: 600; color: #222; margin-bottom: 4px; line-height: 1.3;'>
                                {model} '{color}'
                            </div>
                            <div style='font-size: 11px; color: #666; margin-bottom: 5px;'>EU: {eu_sizes_display}</div>
                        </div>
                        <div style='font-size: 17px; font-weight: 700; color: #000; margin-top: auto;'>{price_formatted}</div>
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