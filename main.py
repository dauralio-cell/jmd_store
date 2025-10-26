import streamlit as st
import pandas as pd
import glob
import os
import re
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
st.image("data/images/banner.jpg", width="stretch")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Инициализация сессии ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- Загрузка данных ---
@st.cache_data
def load_data():
    try:
        # Читаем оба листа
        df_nike = pd.read_excel(CATALOG_PATH, sheet_name='Nike')
        df_mizuno = pd.read_excel(CATALOG_PATH, sheet_name='Mizuno')
        
        # Объединяем
        df = pd.concat([df_nike, df_mizuno], ignore_index=True)
        
        # Заполняем пустые значения
        df['brand'] = df['brand'].fillna(method='ffill')
        df['model'] = df['model'].fillna(method='ffill')
        df['color'] = df['color'].fillna(method='ffill')
        df['gender'] = df['gender'].fillna(method='ffill')
        df['image'] = df['image'].fillna(method='ffill')
        
        # Очищаем названия моделей
        df["model_clean"] = df["model"].str.replace(r'\([^)]*\)', '', regex=True).str.strip()
        
        # Берем размеры напрямую из колонок
        df["size_us"] = df["size US"].fillna("").astype(str).str.strip()
        df["size_eu"] = df["size EU"].fillna("").astype(str).str.strip()
        
        # Фильтруем только товары в наличии
        if 'yes' in df.columns:
            df = df[df['yes'].astype(str).str.lower().str.strip().isin(['yes', 'да', '1', 'true', 'есть'])]
        
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return pd.DataFrame()

# --- Функции для изображений ---
def get_image_paths(image_names, sku):
    """Ищет изображения по названиям или SKU"""
    image_paths = []
    
    if pd.notna(image_names) and image_names != "":
        for image_name in str(image_names).split():
            patterns = [
                os.path.join(IMAGES_PATH, "**", f"{image_name}.*"),
                os.path.join(IMAGES_PATH, "**", f"{image_name}.jpg"),
            ]
            for pattern in patterns:
                found = glob.glob(pattern, recursive=True)
                if found:
                    image_paths.extend(found)
                    break
    
    if pd.notna(sku) and sku != "":
        patterns = [
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.jpg"),
            os.path.join(IMAGES_PATH, "**", f"{sku}_*.webp"),
        ]
        for pattern in patterns:
            found = glob.glob(pattern, recursive=True)
            if found:
                for img in found:
                    if img not in image_paths:
                        image_paths.append(img)
    
    return list(dict.fromkeys(image_paths))

def display_product_photo(image_paths, key_suffix=""):
    """Показывает фото товара с точками для переключения"""
    if not image_paths:
        st.markdown("""
            <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 12px;">
                <div style="font-size: 48px;">📷</div>
                <div style="color: #666;">Нет изображений</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Инициализируем выбранное фото
    if f"selected_{key_suffix}" not in st.session_state:
        st.session_state[f"selected_{key_suffix}"] = 0
    
    selected_index = st.session_state[f"selected_{key_suffix}"]
    
    # Создаем колонки: основное фото и точки
    main_col, dots_col = st.columns([3, 1])
    
    with main_col:
        # Основное большое фото
        try:
            st.image(image_paths[selected_index], use_container_width=True)
        except Exception as e:
            st.error(f"❌ Ошибка загрузки изображения")

    with dots_col:
        st.write("")  # Отступ
        st.write("")  # Отступ
        
        # Точки для переключения фото
        for i in range(len(image_paths[:4])):  # Максимум 4 точки
            dot = "●" if i == selected_index else "○"
            
            # Создаем кнопку-точку
            if st.button(
                dot, 
                key=f"dot_{key_suffix}_{i}",
                type="primary" if i == selected_index else "secondary"
            ):
                st.session_state[f"selected_{key_suffix}"] = i
                st.rerun()

# --- Группировка товаров ---
def group_products(df):
    """Группирует товары по модели и цвету"""
    if df.empty:
        return pd.DataFrame()
    
    # Группируем по модели и цвету, собираем все размеры
    grouped = df.groupby(['brand', 'model_clean', 'color']).agg({
        'sku': 'first',
        'image': 'first', 
        'gender': 'first',
        'price': 'first',
        'size_us': lambda x: [s for s in x if s and str(s).strip() != ""],
        'size_eu': lambda x: [s for s in x if s and str(s).strip() != ""]
    }).reset_index()
    
    return grouped

# --- Корзина ---
def add_to_cart(item):
    st.session_state.cart.append(item)
    st.success(f"✅ Добавлено: {item['brand']} {item['model']}")

def display_cart():
    if not st.session_state.cart:
        st.info("🛒 Корзина пуста")
        return
    
    st.subheader("🛒 Корзина")
    for i, item in enumerate(st.session_state.cart):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"Цвет: {item['color']} | Размер: {item['size_us']}US")
            st.write(f"Цена: {item['price']} ₸")
        with col2:
            if st.button("🗑️", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
    
    total = sum(item['price'] for item in st.session_state.cart if item['price'])
    st.markdown(f"**Итого: {total} ₸**")
    
    if st.button("📦 Оформить заказ"):
        st.success("🎉 Заказ оформлен!")

# --- Загружаем данные ---
df = load_data()

# --- Боковая панель ---
with st.sidebar:
    st.header("🛒 Корзина")
    display_cart()
    
    st.header("🔍 Поиск")
    search_query = st.text_input("Поиск товаров")
    
    st.header("⚙️ Настройки")
    items_per_page = st.slider("Товаров на странице", 8, 32, 16)

# --- Основной интерфейс ---
st.markdown("## 👟 Каталог товаров")

if df.empty:
    st.warning("Каталог пуст")
    st.stop()

# --- Фильтры ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    brands = ["Все"] + sorted(df['brand'].unique().tolist())
    brand_filter = st.selectbox("Бренд", brands)
with col2:
    colors = ["Все"] + sorted(df['color'].unique().tolist())
    color_filter = st.selectbox("Цвет", colors)
with col3:
    genders = ["Все", "men", "women", "unisex"]
    gender_filter = st.selectbox("Пол", genders)
with col4:
    sizes = ["Все"] + sorted(df['size_us'].unique().tolist())
    size_filter = st.selectbox("Размер US", sizes)

# --- Применяем фильтры ---
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df['brand'] == brand_filter]
if color_filter != "Все":
    filtered_df = filtered_df[filtered_df['color'] == color_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df['gender'] == gender_filter]
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df['size_us'] == size_filter]
if search_query:
    filtered_df = filtered_df[filtered_df['model_clean'].str.contains(search_query, case=False, na=False)]

# --- Группируем отфильтрованные товары ---
grouped_products = group_products(filtered_df)

if grouped_products.empty:
    st.warning("Товары не найдены")
else:
    # Показываем товары
    num_cols = 4
    for i in range(0, len(grouped_products), num_cols):
        cols = st.columns(num_cols)
        batch = grouped_products.iloc[i:i+num_cols]
        
        for col_idx, (_, product) in zip(cols, batch.iterrows()):
            with col_idx:
                # Карточка товара
                st.markdown("""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: white;">
                """, unsafe_allow_html=True)
                
                # Фото
                image_paths = get_image_paths(product['image'], product['sku'])
                display_product_photo(image_paths, key_suffix=f"{product['sku']}_{i}_{col_idx}")
                
                # Информация
                st.markdown(f"**{product['brand']} {product['model_clean']}**")
                st.write(f"Цвет: {product['color']}")
                st.write(f"Пол: {product['gender']}")
                
                # Размеры
                us_sizes = product['size_us']
                eu_sizes = product['size_eu']
                if us_sizes:
                    st.write(f"US: {', '.join(us_sizes)}")
                if eu_sizes:
                    st.write(f"EU: {', '.join(eu_sizes)}")
                
                # Цена
                price = product['price']
                if price and str(price).strip():
                    st.markdown(f"**{price} ₸**")
                else:
                    st.write("Цена не указана")
                
                # Кнопка добавления в корзину
                if st.button("🛒 Добавить в корзину", key=f"cart_{product['sku']}_{i}_{col_idx}"):
                    add_to_cart({
                        'brand': product['brand'],
                        'model': product['model_clean'],
                        'color': product['color'],
                        'size_us': us_sizes[0] if us_sizes else "",
                        'price': price
                    })
                
                st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("© DENE Store 2025")