import streamlit as st
import pandas as pd
import glob
import os
import re
import base64
import json
import hashlib
from PIL import Image

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

# --- Инициализация сессии ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- Вспомогательные функции ---
def safe_int_convert(value):
    """Безопасное преобразование в int"""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def validate_data(df):
    """Проверка качества данных"""
    if df.empty:
        st.error("Каталог пуст или не загружен")
        return False
    
    required_columns = ['brand', 'model']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Отсутствуют обязательные колонки: {missing_columns}")
        return False
    
    return True

# --- Функции для работы с изображениями ---
@st.cache_data(show_spinner=False)
def get_image_paths_cached(image_names, sku):
    """Кэширование путей к изображениям"""
    return get_all_image_paths(image_names, sku)

def get_all_image_paths(image_names, sku):
    """Ищет все изображения по названиям из колонки image или по SKU"""
    image_paths = []
    
    # Если есть названия в колонке image, ищем все изображения
    if pd.notna(image_names) and image_names != "":
        image_list = str(image_names).split()
        for image_name in image_list:
            patterns = [
                os.path.join(IMAGES_PATH, "**", f"{image_name}.*"),
                os.path.join(IMAGES_PATH, "**", f"{image_name}.jpg"),
                os.path.join(IMAGES_PATH, "**", f"{image_name}.webp"),
                os.path.join(IMAGES_PATH, "**", f"{image_name}.png"),
            ]
            
            for pattern in patterns:
                image_files = glob.glob(pattern, recursive=True)
                if image_files:
                    image_paths.extend(image_files)
                    break
    
    # Если по названию не нашли или нужно дополнить по SKU
    if pd.notna(sku) and sku != "":
        patterns = [
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.jpg"),
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.webp"),
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.png"),
        ]
        
        for pattern in patterns:
            image_files = glob.glob(pattern, recursive=True)
            if image_files:
                # Добавляем только те, которых еще нет в списке
                for img_path in image_files:
                    if img_path not in image_paths:
                        image_paths.append(img_path)
    
    # Убираем дубликаты и возвращаем
    unique_paths = list(dict.fromkeys(image_paths))
    return unique_paths if unique_paths else []

def display_modern_cards(image_paths, key_suffix):
    """Современные карточки с превью фото"""
    if not image_paths:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px; background: #f8f9fa; 
                        border-radius: 12px; margin: 10px 0;">
                <div style="font-size: 48px;">📷</div>
                <div style="color: #666;">Нет изображений</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return
    
    # Инициализируем выбранное фото в session_state
    if f"selected_{key_suffix}" not in st.session_state:
        st.session_state[f"selected_{key_suffix}"] = 0
    
    selected_index = st.session_state[f"selected_{key_suffix}"]
    
    # Создаем колонки: основное фото и превью
    main_col, preview_col = st.columns([3, 1])
    
    with main_col:
        # Основное большое фото
        try:
            st.image(
                image_paths[selected_index], 
                use_container_width=True
            )
        except:
            st.markdown(
                f"""
                <div style="text-align: center; padding: 60px; background: #fff3cd; 
                            border-radius: 12px; color: #856404; margin: 10px 0;">
                    <div style="font-size: 36px;">❌</div>
                    <div>Ошибка загрузки фото</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with preview_col:
        st.write("")  # Отступ
        st.write("")  # Отступ
        
        # Маленькие точки-превью без цифр и подсказок
        for i, img_path in enumerate(image_paths[:4]):  # Максимум 4 превью
            # Определяем символ для кнопки (маленькие точки)
            dot = "●" if i == selected_index else "○"
            
            # Создаем маленькую кнопку выбора
            if st.button(
                dot, 
                key=f"btn_{key_suffix}_{i}",
                type="primary" if i == selected_index else "secondary"
            ):
                st.session_state[f"selected_{key_suffix}"] = i
                st.rerun()

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

# --- Функции корзины ---
def add_to_cart(item):
    """Добавление товара в корзину"""
    st.session_state.cart.append(item)
    st.success(f"✅ Добавлено: {item['brand']} {item['model_clean']} {item['size_us']}US")

def clear_cart():
    """Очистка корзины"""
    st.session_state.cart = []
    st.success("🛒 Корзина очищена")

def display_cart():
    """Отображение корзины"""
    if not st.session_state.cart:
        st.info("🛒 Корзина пуста")
        return
    
    st.subheader("🛒 Ваша корзина")
    
    total = 0
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        with col1:
            st.write(f"**{item['brand']} {item['model_clean']}**")
            st.write(f"Размер: {item['size_us']}US ({item['size_eu']}EU)")
        with col2:
            st.write(f"{item['price']} ₸")
        with col3:
            if st.button("🗑️", key=f"remove_{i}", help="Удалить из корзины"):
                st.session_state.cart.pop(i)
                st.rerun()
        
        total += safe_int_convert(item['price'])
    
    st.markdown(f"**Итого: {total} ₸**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Оформить заказ", type="primary"):
            st.success("🎉 Заказ оформлен! С вами свяжутся для подтверждения.")
    with col2:
        if st.button("🗑️ Очистить корзину", type="secondary"):
            clear_cart()

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

# --- Основной интерфейс ---
# Загрузка данных с индикатором
with st.spinner('🔄 Загрузка каталога...'):
    df = load_data()

# Валидация данных
if not validate_data(df):
    st.stop()

# --- Боковая панель с корзиной и поиском ---
with st.sidebar:
    st.header("🛒 Корзина")
    display_cart()
    
    st.divider()
    
    st.header("🔍 Расширенный поиск")
    search_query = st.text_input("Поиск по названию", "")
    
    st.divider()
    
    st.header("⚙️ Настройки")
    items_per_page = st.slider("Товаров на странице", 8, 32, 16)
    sort_option = st.selectbox("Сортировка", [
        "По умолчанию", 
        "Цена (по возрастанию)", 
        "Цена (по убыванию)",
        "Название (А-Я)",
        "Название (Я-А)"
    ])

# --- Основные фильтры ---
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
    
    # Поиск по названию
    if search_query:
        filtered_df = filtered_df[
            filtered_df["model_clean"].str.contains(search_query, case=False, na=False) |
            filtered_df["brand"].str.contains(search_query, case=False, na=False)
        ]

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
            min_price = safe_int_convert(prices_with_values["price"].min())
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
            max_price = safe_int_convert(prices_with_values["price"].max())
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
        st.rerun()
else:
    # Получаем сгруппированные модели
    unique_models = get_unique_models(filtered_df)
    
    # Сортировка
    if sort_option == "Цена (по возрастанию)":
        unique_models = unique_models.sort_values(by='price', key=lambda x: x.apply(lambda p: min(p) if p and any(p) else 0))
    elif sort_option == "Цена (по убыванию)":
        unique_models = unique_models.sort_values(by='price', key=lambda x: x.apply(lambda p: max(p) if p and any(p) else 0), ascending=False)
    elif sort_option == "Название (А-Я)":
        unique_models = unique_models.sort_values(by='model_clean')
    elif sort_option == "Название (Я-А)":
        unique_models = unique_models.sort_values(by='model_clean', ascending=False)
    
    if len(unique_models) == 0:
        st.warning("🔍 Нет данных для отображения.")
    else:
        # Пагинация
        if len(unique_models) > items_per_page:
            total_pages = (len(unique_models) - 1) // items_per_page + 1
            page = st.number_input("Страница", min_value=1, max_value=total_pages, value=1, key="pagination")
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_models = unique_models.iloc[start_idx:end_idx]
            
            st.caption(f"Страница {page} из {total_pages} | Показано {len(paginated_models)} из {len(unique_models)} моделей")
        else:
            paginated_models = unique_models
        
        # Отображаем по 4 модели в ряд
        num_cols = 4
        rows = [paginated_models.iloc[i:i+num_cols] for i in range(0, len(paginated_models), num_cols)]

        for i, row_df in enumerate(rows):
            cols = st.columns(num_cols)
            for col_idx, (_, model_row) in zip(cols, row_df.iterrows()):
                with col_idx:
                    # Создаем контейнер для карточки товара
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                border:1px solid #eee;
                                border-radius:16px;
                                padding:12px;
                                margin-bottom:16px;
                                background-color:#fff;
                                box-shadow:0 2px 10px rgba(0,0,0,0.05);
                            ">
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Получаем все изображения для товара
                        first_sku = model_row['sku']
                        first_image = model_row['image']
                        all_image_paths = get_image_paths_cached(first_image, first_sku)
                        
                        # Отображаем современные карточки с превью
                        display_modern_cards(all_image_paths, f"{first_sku}_{i}_{col_idx}")
                        
                        # Информация о товаре
                        st.markdown(f"**{model_row['brand']} {model_row['model_clean']}**")
                        st.caption(f"{model_row['color']} | {model_row['gender']}")
                        
                        # Формируем строку с размерами
                        us_sizes = [str(size) for size in model_row['size_us'] if size and str(size).strip() != ""]
                        eu_sizes = [str(size) for size in model_row['size_eu'] if size and str(size).strip() != ""]
                        sizes_text = f"US: {', '.join(us_sizes)}" if us_sizes else "Размеры не указаны"
                        if eu_sizes:
                            sizes_text += f" | EU: {', '.join(eu_sizes)}"
                        
                        st.write(sizes_text)
                        
                        # Диапазон цен
                        prices = model_row['price']
                        if prices and any(prices):
                            valid_prices = [p for p in prices if p != "" and str(p).strip() != ""]
                            if valid_prices:
                                min_price = min(valid_prices)
                                max_price = max(valid_prices)
                                price_text = f"{safe_int_convert(min_price)} - {safe_int_convert(max_price)} ₸" if min_price != max_price else f"{safe_int_convert(min_price)} ₸"
                            else:
                                price_text = "Цена не указана"
                        else:
                            price_text = "Цена не указана"
                        
                        st.markdown(f"**{price_text}**")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Кнопка для просмотра всех размеров
                    with st.expander("📋 Все размеры", expanded=False):
                        # Находим все варианты этой модели в отфильтрованных данных
                        model_variants = filtered_df[
                            (filtered_df['brand'] == model_row['brand']) & 
                            (filtered_df['model_clean'] == model_row['model_clean']) &
                            (filtered_df['color'] == model_row['color'])
                        ]
                        
                        for _, variant in model_variants.iterrows():
                            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                            with col1:
                                st.text(f"US: {variant['size_us']}")
                            with col2:
                                st.text(f"EU: {variant['size_eu']}")
                            with col3:
                                price_val = variant['price']
                                if price_val and str(price_val).strip() != "":
                                    st.text(f"{safe_int_convert(price_val)} ₸")
                                else:
                                    st.text("—")
                            with col4:
                                if st.button("🛒", key=f"cart_{variant['sku']}_{i}_{col_idx}", help="Добавить в корзину"):
                                    add_to_cart({
                                        'brand': variant['brand'],
                                        'model_clean': variant['model_clean'],
                                        'size_us': variant['size_us'],
                                        'size_eu': variant['size_eu'],
                                        'price': variant['price'],
                                        'sku': variant['sku']
                                    })

st.divider()
st.caption("© DENE Store 2025")