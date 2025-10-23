import streamlit as st
import pandas as pd
import glob
import os
import re
import base64
import json

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
st.image("data/images/banner.jpg", width="stretch")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Пути и константы ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Таблица конверсии размеров US ↔ EU ---
size_conversion = {
    "6": "39", "6.5": "39.5", "7": "40", "7.5": "40.5",
    "8": "41", "8.5": "42", "9": "42.5", "9.5": "43",
    "10": "44", "10.5": "44.5", "11": "45", "11.5": "46", "12": "46.5"
}
reverse_conversion = {v: k for k, v in size_conversion.items()}

# --- Функции для работы с изображениями ---
def get_image_path(image_names, sku):
    """Ищет изображение по названиям из колонки image или по SKU"""
    # Если есть названия в колонке image, берем первое изображение
    if pd.notna(image_names) and image_names != "":
        # Берем первое название из списка (разделитель - пробел)
        image_list = str(image_names).split()
        if image_list:
            first_image = image_list[0]
            # Пробуем разные расширения и пути
            patterns = [
                os.path.join(IMAGES_PATH, "**", f"{first_image}.*"),
                os.path.join(IMAGES_PATH, "**", f"{first_image}.jpg"),
                os.path.join(IMAGES_PATH, "**", f"{first_image}.webp"),
                os.path.join(IMAGES_PATH, "**", f"{first_image}.png"),
            ]
            
            for pattern in patterns:
                image_files = glob.glob(pattern, recursive=True)
                if image_files:
                    return image_files[0]
    
    # Если по названию не нашли, пробуем по SKU
    if pd.notna(sku) and sku != "":
        patterns = [
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.jpg"),
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.webp"),
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.png"),
        ]
        
        for pattern in patterns:
            image_files = glob.glob(pattern, recursive=True)
            if image_files:
                return image_files[0]
    
    # Если ничего не нашли, возвращаем no_image
    return os.path.join(IMAGES_PATH, "no_image.jpg")

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        try:
            with open(fallback, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except:
            return ""

# --- Функции для группировки моделей ---
def get_unique_models(df):
    """Получаем уникальные модели для отображения"""
    if len(df) == 0:
        return pd.DataFrame()
        
    # Группируем по основным характеристикам модели
    grouped = df.groupby(['brand', 'model_clean', 'gender', 'color']).agg({
        'sku': 'first',  # берем первый SKU для изображения
        'image': 'first', # берем первое изображение
        'price': lambda x: list(x.unique()),  # все уникальные цены
        'size_us': list,  # все доступные размеры US
        'size_eu': list   # все доступные размеры EU
    }).reset_index()
    
    return grouped

# --- Загрузка данных ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
        # Читаем оба листа
        df_nike = pd.read_excel(CATALOG_PATH, sheet_name='Nike')
        df_mizuno = pd.read_excel(CATALOG_PATH, sheet_name='Mizuno')
        
        # Объединяем данные
        df = pd.concat([df_nike, df_mizuno], ignore_index=True)
        df = df.fillna("")

        # Заполняем пустые значения в бренде и модели
        df['brand'] = df['brand'].fillna(method='ffill')
        df['model'] = df['model'].fillna(method='ffill')
        df['gender'] = df['gender'].fillna(method='ffill')
        df['color'] = df['color'].fillna(method='ffill')
        df['image'] = df['image'].fillna(method='ffill')

        # Обработка модели
        df["model_clean"] = (
            df["model"]
            .str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True)
            .str.strip()
        )

        # Извлекаем размеры
        df["size_us"] = df["model"].apply(lambda x: re.search(r"(\d{1,2}(\.\d)?)(?=US)", str(x)))
        df["size_us"] = df["size_us"].apply(lambda m: m.group(1) if m else "")
        df["size_eu"] = df["model"].apply(lambda x: re.search(r"(\d{2}(\.\d)?)(?=EU)", str(x)))
        df["size_eu"] = df["size_eu"].apply(lambda m: m.group(1) if m else "")

        # Автозаполнение при отсутствии одного из размеров
        df["size_eu"] = df.apply(lambda r: size_conversion.get(r["size_us"], r["size_eu"]), axis=1)
        df["size_us"] = df.apply(lambda r: reverse_conversion.get(r["size_eu"], r["size_us"]), axis=1)

        # Пол и цвет
        df["gender"] = df["model"].apply(
            lambda x: "men" if "men" in str(x).lower() else (
                "women" if "women" in str(x).lower() else "unisex"
            )
        )
        df["color"] = df["model"].str.extract(
            r"(white|black|blue|red|green|pink|gray|brown)", flags=re.IGNORECASE, expand=False
        ).fillna("other")

        # Описание
        if "description" not in df.columns:
            df["description"] = "Описание временно недоступно."

        # Фильтрация по наличию товара (колонка 'yes')
        if 'yes' in df.columns:
            # Более гибкая фильтрация
            df = df[df['yes'].astype(str).str.lower().str.strip().isin(['yes', 'да', '1', 'true', 'есть'])]
        
        # Исключаем товары без модели (но оставляем без цены)
        df = df[df["model_clean"].astype(str).str.strip() != ""]

        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

# --- Загружаем данные ---
df = load_data()

# --- Отладочная информация ---
if len(df) > 0 and 'image' in df.columns:
    st.sidebar.write("📸 Примеры названий изображений:")
    sample_images = df['image'].head(3).tolist()
    for img in sample_images:
        st.sidebar.write(f" - {img}")

# --- Фильтры ---
st.divider()
st.markdown("### 🔎 Фильтр каталога")

col1, col2, col3, col4, col5, col6 = st.columns(6)

# Бренд
available_brands = ["Все"] + sorted(df["brand"].unique().tolist()) if len(df) > 0 else ["Все"]
brand_filter = col1.selectbox("Бренд", available_brands)

# Модель зависит от выбранного бренда
if len(df) > 0:
    if brand_filter != "Все":
        brand_models = sorted(df[df["brand"] == brand_filter]["model_clean"].unique().tolist())
    else:
        brand_models = sorted(df["model_clean"].unique().tolist())
else:
    brand_models = ["Все"]
model_filter = col2.selectbox("Модель", ["Все"] + brand_models)

# Размеры
available_sizes_us = ["Все"] + sorted(df["size_us"].dropna().unique().tolist()) if len(df) > 0 else ["Все"]
available_sizes_eu = ["Все"] + sorted(df["size_eu"].dropna().unique().tolist()) if len(df) > 0 else ["Все"]
size_us_filter = col3.selectbox("Размер (US)", available_sizes_us)
size_eu_filter = col4.selectbox("Размер (EU)", available_sizes_eu)

# Пол и цвет
gender_filter = col5.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col6.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()) if len(df) > 0 else ["Все"])

# --- Применяем фильтры ---
filtered_df = df.copy()
if len(df) > 0:
    if brand_filter != "Все":
        filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
    if model_filter != "Все":
        filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
    if size_us_filter != "Все":
        eu_equiv = size_conversion.get(size_us_filter, "")
        filtered_df = filtered_df[
            (filtered_df["size_us"] == size_us_filter) | (filtered_df["size_eu"] == eu_equiv)
        ]
    if size_eu_filter != "Все":
        us_equiv = reverse_conversion.get(size_eu_filter, "")
        filtered_df = filtered_df[
            (filtered_df["size_eu"] == size_eu_filter) | (filtered_df["size_us"] == us_equiv)
        ]
    if gender_filter != "Все":
        filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
    if color_filter != "Все":
        filtered_df = filtered_df[filtered_df["color"] == color_filter]

st.divider()

# --- Статистика ---
col_info1, col_info2, col_info3, col_info4 = st.columns(4)
with col_info1:
    st.metric("📦 Всего товаров", len(filtered_df))
with col_info2:
    st.metric("🏷️ Уникальных моделей", filtered_df["model_clean"].nunique() if len(filtered_df) > 0 else 0)
with col_info3:
    if len(filtered_df) > 0 and 'price' in filtered_df.columns:
        # Фильтруем только товары с ценой
        prices_with_values = filtered_df[filtered_df['price'].astype(str).str.strip() != ""]
        if len(prices_with_values) > 0:
            min_price = int(prices_with_values["price"].min())
            st.metric("💰 Минимальная цена", f"{min_price} ₸")
        else:
            st.metric("💰 Минимальная цена", "—")
    else:
        st.metric("💰 Минимальная цена", "—")
with col_info4:
    if len(filtered_df) > 0 and 'price' in filtered_df.columns:
        # Фильтруем только товары с ценой
        prices_with_values = filtered_df[filtered_df['price'].astype(str).str.strip() != ""]
        if len(prices_with_values) > 0:
            max_price = int(prices_with_values["price"].max())
            st.metric("💎 Максимальная цена", f"{max_price} ₸")
        else:
            st.metric("💎 Максимальная цена", "—")
    else:
        st.metric("💎 Максимальная цена", "—")

st.divider()

# --- Сетка карточек товаров ---
st.markdown("## 👟 Каталог товаров")

if len(filtered_df) == 0:
    st.warning("🔍 Товары по заданным фильтрам не найдены.")
    st.info("💡 Попробуйте изменить параметры фильтрации")
    
    if st.button("🔄 Сбросить все фильтры"):
        st.experimental_rerun()
else:
    # Получаем сгруппированные модели
    unique_models = get_unique_models(filtered_df)
    
    if len(unique_models) == 0:
        st.warning("🔍 Нет данных для отображения.")
    else:
        # Отображаем по 4 модели в ряд
        num_cols = 4
        rows = [unique_models.iloc[i:i+num_cols] for i in range(0, len(unique_models), num_cols)]

        for row_df in rows:
            cols = st.columns(num_cols)
            for col, (_, model_row) in zip(cols, row_df.iterrows()):
                with col:
                    # Берем первый SKU и image для изображения
                    first_sku = model_row['sku']
                    first_image = model_row['image']
                    image_path = get_image_path(first_image, first_sku)
                    image_base64 = get_image_base64(image_path)
                    
                    # Формируем строку с размерами
                    us_sizes = [str(size) for size in model_row['size_us'] if size and str(size).strip() != ""]
                    eu_sizes = [str(size) for size in model_row['size_eu'] if size and str(size).strip() != ""]
                    sizes_text = f"US: {', '.join(us_sizes)}" if us_sizes else "Размеры не указаны"
                    if eu_sizes:
                        sizes_text += f" | EU: {', '.join(eu_sizes)}"
                    
                    # Диапазон цен
                    prices = model_row['price']
                    if prices and any(prices):
                        valid_prices = [p for p in prices if p != "" and str(p).strip() != ""]
                        if valid_prices:
                            min_price = min(valid_prices)
                            max_price = max(valid_prices)
                            price_text = f"{int(min_price)} - {int(max_price)} ₸" if min_price != max_price else f"{int(min_price)} ₸"
                        else:
                            price_text = "Цена не указана"
                    else:
                        price_text = "Цена не указана"

                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #eee;
                            border-radius:16px;
                            padding:12px;
                            margin-bottom:16px;
                            background-color:#fff;
                            box-shadow:0 2px 10px rgba(0,0,0,0.05);
                            transition:transform 0.2s ease-in-out;
                        " onmouseover="this.style.transform='scale(1.02)';"
                          onmouseout="this.style.transform='scale(1)';">
                            <img src="data:image/jpeg;base64,{image_base64}" 
                                 style='width:100%; border-radius:12px; object-fit:cover; height:220px;'>
                            <h4 style="margin:10px 0 4px 0;">{model_row['brand']} {model_row['model_clean']}</h4>
                            <p style="color:gray; font-size:13px; margin:0;">
                                {model_row['color']} | {model_row['gender']}
                            </p>
                            <p style="font-size:12px; color:#666; margin:4px 0;">
                                {sizes_text}
                            </p>
                            <p style="font-weight:bold; font-size:16px; margin-top:6px;">{price_text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Кнопка для просмотра всех размеров
                    with st.expander("📋 Все размеры", expanded=False):
                        # Находим все варианты этой модели в отфильтрованных данных
                        model_variants = filtered_df[
                            (filtered_df['brand'] == model_row['brand']) & 
                            (filtered_df['model_clean'] == model_row['model_clean']) &
                            (filtered_df['color'] == model_row['color'])
                        ]
                        
                        for _, variant in model_variants.iterrows():
                            col1, col2, col3 = st.columns([1, 1, 2])
                            with col1:
                                st.text(f"US: {variant['size_us']}")
                            with col2:
                                st.text(f"EU: {variant['size_eu']}")
                            with col3:
                                price_val = variant['price']
                                if price_val and str(price_val).strip() != "":
                                    st.text(f"{int(price_val)} ₸")
                                else:
                                    st.text("Цена не указана")
                                if st.button("🛒", key=f"cart_{variant['sku']}", help="Добавить в корзину"):
                                    st.success(f"Добавлен размер {variant['size_us']}US")

st.divider()
st.caption("© DENE Store 2025")