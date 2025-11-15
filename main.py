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

# --- Обложка и хедер как было ---
st.image("data/images/banner.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Кнопка корзины вверху ---
col1, col2, col3 = st.columns([1, 3, 1])
with col3:
    cart_count = len(st.session_state.cart) if 'cart' in st.session_state else 0
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
    if st.button(cart_text, use_container_width=True):
        st.switch_page("pages/3_Корзина.py")

# --- Пути и константы ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Функции для работы с изображениями ---
def optimize_image_for_telegram(image_path, target_size=(300, 300)):
    """Оптимизирует изображение для Telegram"""
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Ресайзим сохраняя пропорции
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Сохраняем в буфер с оптимизацией
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            return base64.b64encode(buffer.read()).decode("utf-8")
            
    except Exception as e:
        # Fallback на оригинальное изображение
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
            with open(fallback, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")

def get_image_path(image_names):
    """Ищет изображение по имени из колонки image (берет первое изображение из списка)"""
    if (image_names is pd.NA or 
        pd.isna(image_names) or 
        not image_names or 
        str(image_names).strip() == ""):
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    first_image_name = image_names_list[0]
    
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(IMAGES_PATH, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        
        pattern_start = os.path.join(IMAGES_PATH, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    return os.path.join(IMAGES_PATH, "no_image.jpg")

# --- Таблица конверсии размеров US ↔ EU ---
size_conversion = {
    "1": "34", "2": "35", "3": "36", "4": "37", "5": "38",
    "6": "39", "7": "40", "8": "41", "9": "42", "10": "43",
    "11": "44", "12": "45", "13": "46",
    # Добавляем дробные размеры
    "7.0": "40", "7.5": "40.5", "8.0": "41", "8.5": "42", 
    "9.0": "42.5", "9.5": "43", "10.0": "43.5", "10.5": "44",
    "11.0": "44.5", "11.5": "45", "12.0": "45.5", "12.5": "46"
}

# --- Функция для получения EU размеров ---
def get_eu_sizes(us_sizes_str):
    """Конвертирует US размеры в EU размеры"""
    if not us_sizes_str or us_sizes_str == "":
        return ""
    
    us_sizes = [size.strip() for size in us_sizes_str.split(",")]
    eu_sizes = []
    
    for us_size in us_sizes:
        # Ищем точное соответствие в таблице конверсии
        eu_size = size_conversion.get(us_size, "")
        if not eu_size:
            # Если точного соответствия нет, пробуем найти ближайший целый размер
            base_size = us_size.split('.')[0]  # Берем целую часть
            eu_size = size_conversion.get(base_size, us_size)  # Если не нашли, оставляем US размер
        eu_sizes.append(eu_size)
    
    # Убираем дубликаты EU размеров
    unique_eu_sizes = []
    for size in eu_sizes:
        if size not in unique_eu_sizes:
            unique_eu_sizes.append(size)
    
    return ", ".join(unique_eu_sizes)

# --- Функция сортировки размеров ---
def sort_sizes(size_list):
    """Сортирует размеры правильно"""
    numeric_sizes = []
    string_sizes = []
    
    for size in size_list:
        clean_size = str(size).strip()
        # Пытаемся извлечь числовое значение для сортировки
        try:
            # Для дробных размеров
            if '.' in clean_size:
                base_num = float(clean_size)
            else:
                base_num = float(clean_size)
            numeric_sizes.append((base_num, clean_size))
        except:
            string_sizes.append(clean_size)
    
    # Сортируем по числовому значению
    numeric_sizes.sort(key=lambda x: x[0])
    
    # Возвращаем оригинальные строки в отсортированном порядке
    result = [size[1] for size in numeric_sizes] + sorted(string_sizes)
    return result

# --- Функция для получения доступных размеров в фильтре ---
def get_available_sizes_for_filter(df):
    """Получает размеры для фильтра с учетом диапазона 5-11 US"""
    # Фильтруем только товары в наличии
    in_stock_df = df[df.get('in stock', 'yes').str.lower() == 'yes']
    
    # Получаем все уникальные размеры
    all_sizes = in_stock_df["size US"].dropna().unique().tolist()
    
    # Фильтруем по диапазону 5-11 US (включая дробные)
    filtered_sizes = []
    for size in all_sizes:
        clean_size = str(size).strip()
        if not clean_size or clean_size == "nan":
            continue
            
        try:
            # Для дробных размеров
            if '.' in clean_size:
                base_num = float(clean_size)
            else:
                base_num = float(clean_size)
            
            # ВКЛЮЧАЕМ размер 11 (5-11 включительно)
            if 5 <= base_num <= 11:
                filtered_sizes.append(clean_size)
        except:
            # Если не число, пропускаем
            continue
    
    # Убираем дубликаты и сортируем
    unique_sizes = list(dict.fromkeys(filtered_sizes))  # Убираем дубликаты сохраняя порядок
    return sort_sizes(unique_sizes)

# --- Загрузка и обработка данных ---
@st.cache_data(ttl=60)  # Обновлять каждую минуту
def load_data():
    try:
        # Добавляем проверку времени изменения файла
        file_mtime = os.path.getmtime(CATALOG_PATH)
        st.sidebar.write(f"Файл обновлен: {time.ctime(file_mtime)}")
        
        # Читаем все листы Excel файла
        all_sheets = pd.read_excel(CATALOG_PATH, sheet_name=None)
        
        # Обрабатываем каждый лист и объединяем
        processed_dfs = []
        
        for sheet_name, sheet_data in all_sheets.items():
            # Заполняем пропущенные значения в ключевых колонках
            sheet_data = sheet_data.fillna("")
            
            # Заполняем данные для бренда и модели
            sheet_data['brand'] = sheet_data['brand'].replace('', pd.NA).ffill()
            sheet_data['model'] = sheet_data['model'].replace('', pd.NA).ffill()
            sheet_data['gender'] = sheet_data['gender'].replace('', pd.NA).ffill()
            
            # Для цвета используем заполнение, но не для изображений
            sheet_data['color'] = sheet_data['color'].replace('', pd.NA).ffill()
            
            # Изображения оставляем как есть - не заполняем!
            sheet_data['image'] = sheet_data['image'].replace('', pd.NA)
            
            # Преобразуем размеры в строки и убираем лишние пробелы
            sheet_data['size US'] = sheet_data['size US'].astype(str).str.strip()
            
            # Очищаем название модели (убираем артикулы в скобках)
            sheet_data["model_clean"] = sheet_data["model"].apply(
                lambda x: re.sub(r'\([^)]*\)', '', str(x)).strip() if pd.notna(x) else ""
            )
            
            processed_dfs.append(sheet_data)
        
        # Объединяем все листы
        df = pd.concat(processed_dfs, ignore_index=True)
        
        # Убираем строки без модели или бренда
        df = df[(df['brand'] != '') & (df['model_clean'] != '')]
        
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

# --- ЗАГРУЗКА ДАННЫХ ---
df = load_data()

# --- ДИАГНОСТИКА ---
st.sidebar.write("ДИАГНОСТИКА:")
st.sidebar.write("Всего товаров:", len(df))
st.sidebar.write("Уникальные бренды:", df["brand"].nunique())
st.sidebar.write("Уникальные модели:", df["model_clean"].nunique())

# --- Улучшенные фильтры ---
st.divider()
st.markdown("### Фильтр каталога")

col1, col2, col3, col4, col5 = st.columns(5)

# Бренд
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))

# Модель (зависит от бренда)
if brand_filter != "Все":
    brand_models = sorted(df[df["brand"] == brand_filter]["model_clean"].unique().tolist())
else:
    brand_models = sorted(df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + brand_models)

# Размеры - US 5-11 (ВКЛЮЧАЯ 11) без дубликатов
available_sizes = get_available_sizes_for_filter(df)
size_filter = col3.selectbox("Размер (US)", ["Все"] + available_sizes)

# Пол
gender_filter = col4.selectbox("Пол", ["Все", "men", "women", "unisex"])

# Цвет
color_filter = col5.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()))

# --- Применяем фильтры ---
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
if size_filter != "Все":
    # При фильтрации используем точное соответствие (включая дробные размеры)
    filtered_df = filtered_df[filtered_df["size US"] == size_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if color_filter != "Все":
    filtered_df = filtered_df[filtered_df["color"] == color_filter]

# ФИЛЬТР ПО НАЛИЧИЮ - показываем только товары, у которых есть хотя бы один размер в наличии
def has_any_size_in_stock(group):
    """Проверяет, есть ли хотя бы один размер в наличии для группы товаров"""
    return any(
        str(row.get('in stock', 'yes')).strip().lower() == 'yes'
        for _, row in group.iterrows()
        if str(row['size US']).strip() and str(row['size US']).strip() != "nan"
    )

# Фильтруем группы товаров, оставляем только те, у которых есть хотя бы один размер в наличии
filtered_df = filtered_df.groupby(['brand', 'model_clean', 'color']).filter(has_any_size_in_stock)

st.divider()

# --- Упрощенная сетка карточек товаров для Telegram ---
st.markdown("## Каталог товаров")

if len(filtered_df) == 0:
    st.warning("Товары по выбранным фильтрам не найдены")
else:
    st.write(f"**Найдено товаров: {len(filtered_df)}**")

    # Группируем по модели и цвету для отображения
    def get_first_with_image(group):
        """Берет первую строку с изображением из группы"""
        for _, row in group.iterrows():
            if row['image'] and pd.notna(row['image']) and str(row['image']).strip():
                return row
        return group.iloc[0]

    grouped_df = filtered_df.groupby(['brand', 'model_clean', 'color']).apply(get_first_with_image).reset_index(drop=True)
    
    def get_available_sizes(group):
        """Получает только размеры в наличии для группы"""
        available_sizes = []
        for _, row in group.iterrows():
            us_size = str(row['size US']).strip()
            in_stock = str(row.get('in stock', 'yes')).strip().lower()
            if us_size and us_size != "nan" and in_stock == 'yes':
                available_sizes.append(us_size)
        unique_sizes = list(dict.fromkeys(available_sizes))
        return ', '.join(sort_sizes(unique_sizes))
    
    size_groups = filtered_df.groupby(['brand', 'model_clean', 'color']).apply(get_available_sizes, include_groups=False).reset_index()
    size_groups.columns = ['brand', 'model_clean', 'color', 'size US']
    
    grouped_df = grouped_df.merge(size_groups, on=['brand', 'model_clean', 'color'], suffixes=('', '_grouped'))
    grouped_df['size US'] = grouped_df['size US_grouped']
    grouped_df = grouped_df.drop('size US_grouped', axis=1)
    grouped_df['size_eu'] = grouped_df['size US'].apply(get_eu_sizes)

    num_cols = 3
    rows = [grouped_df.iloc[i:i + num_cols] for i in range(0, len(grouped_df), num_cols)]

    for row_idx, row_df in enumerate(rows):
        cols = st.columns(num_cols)
        for col_idx, (col, (_, row)) in enumerate(zip(cols, row_df.iterrows())):
            with col:
                # Оптимизированное изображение для Telegram
                image_names = row["image"]
                image_path = get_image_path(image_names)
                image_base64 = optimize_image_for_telegram(image_path)

                # Компактная карточка товара
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 8px; margin: 4px 0; background: white; height: 380px; display: flex; flex-direction: column;">
                        <img src="data:image/jpeg;base64,{image_base64}" style="width:100%; border-radius:6px; height:140px; object-fit:contain; background:#f8f9fa; margin-bottom:8px;">
                        <h4 style="margin:4px 0; font-size:13px; color:#333; line-height:1.2;">{row['brand']} {row['model_clean']}</h4>
                        <p style="color:#666; font-size:11px; margin:2px 0;">{row['color']} | {row['gender']}</p>
                        <div style="flex: 1; display: flex; gap: 8px; margin: 6px 0; align-items: center;">
                            <div style="flex: 1; font-size: 10px; text-align: center;">
                                <strong>US:</strong><br>{row['size US']}
                            </div>
                            <div style="flex: 1; font-size: 10px; text-align: center;">
                                <strong>EU:</strong><br>{row['size_eu']}
                            </div>
                        </div>
                        <p style="font-weight:bold; font-size:13px; margin:4px 0; color:#e74c3c;">{int(round(row['price'] / 1000) * 1000)} ₸</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Кнопка "Подробнее" - ВАЖНО: правильный отступ
                if st.button("Подробнее", key=f"details_{row_idx}_{col_idx}", use_container_width=True):
                    st.session_state.product_data = dict(row)
                    st.switch_page("pages/2_Детали_товара.py")

# --- ФУТЕР ---
from components.documents import documents_footer
documents_footer()