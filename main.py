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
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None

# --- Загрузка данных с автоматической проверкой ---
@st.cache_data(ttl=300)
def load_data():
    try:
        if not os.path.exists(CATALOG_PATH):
            st.error(f"Файл каталога не найден: {CATALOG_PATH}")
            return pd.DataFrame()
        
        df_nike = pd.read_excel(CATALOG_PATH, sheet_name='Nike')
        df_mizuno = pd.read_excel(CATALOG_PATH, sheet_name='Mizuno')
        
        df = pd.concat([df_nike, df_mizuno], ignore_index=True)
        
        columns_to_fill = ['brand', 'model', 'color', 'gender', 'image']
        for col in columns_to_fill:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill').fillna('')
        
        df["model_clean"] = df["model"].apply(lambda x: re.sub(r'\([^)]*\)', '', str(x))).str.strip()
        
        size_columns = ['size US', 'size EU', 'size_US', 'size_EU']
        for size_col in size_columns:
            if size_col in df.columns:
                if 'US' in size_col:
                    df["size_us"] = df[size_col].fillna("").astype(str).str.strip()
                elif 'EU' in size_col:
                    df["size_eu"] = df[size_col].fillna("").astype(str).str.strip()
        
        if 'size_us' not in df.columns:
            df['size_us'] = ''
        if 'size_eu' not in df.columns:
            df['size_eu'] = ''
        
        df = df[
            (df['brand'].notna()) & (df['brand'] != '') &
            (df['model_clean'].notna()) & (df['model_clean'] != '')
        ]
        
        st.success(f"✅ Загружено {len(df)} товаров")
        return df
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки каталога: {str(e)}")
        return pd.DataFrame()

# --- Функции для изображений ---
def get_image_paths(image_names, sku):
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
    
    if f"selected_{key_suffix}" not in st.session_state:
        st.session_state[f"selected_{key_suffix}"] = 0
    
    selected_index = st.session_state[f"selected_{key_suffix}"]
    
    main_col, dots_col = st.columns([3, 1])
    
    with main_col:
        try:
            st.image(image_paths[selected_index], use_container_width=True)
        except:
            st.error("❌ Ошибка загрузки изображения")

    with dots_col:
        st.write("")
        st.write("")
        
        for i in range(len(image_paths[:4])):
            dot = "●" if i == selected_index else "○"
            
            if st.button(
                dot, 
                key=f"dot_{key_suffix}_{i}",
                type="primary" if i == selected_index else "secondary"
            ):
                st.session_state[f"selected_{key_suffix}"] = i
                st.rerun()

# --- Группировка товаров ---
def group_products(df):
    if df.empty:
        return pd.DataFrame()
    
    df_clean = df[
        (df['brand'].notna()) & (df['brand'] != '') &
        (df['model_clean'].notna()) & (df['model_clean'] != '') &
        (df['color'].notna()) & (df['color'] != '')
    ].copy()
    
    if df_clean.empty:
        return pd.DataFrame()
    
    grouped = df_clean.groupby(['brand', 'model_clean', 'color']).agg({
        'sku': 'first',
        'image': 'first', 
        'gender': 'first',
        'price': 'first',
        'size_us': lambda x: [str(s) for s in x if s and str(s).strip() != ""],
        'size_eu': lambda x: [str(s) for s in x if s and str(s).strip() != ""]
    }).reset_index()
    
    return grouped

def get_product_variants(df, brand, model_clean):
    """Получает все варианты цвета для данной модели"""
    variants = df[
        (df['brand'] == brand) & 
        (df['model_clean'] == model_clean)
    ]
    return variants

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
    
    total = sum(float(item['price']) for item in st.session_state.cart if item['price'] and str(item['price']).strip())
    st.markdown(f"**Итого: {total} ₸**")
    
    if st.button("📦 Оформить заказ"):
        st.success("🎉 Заказ оформлен!")

# --- Модальное окно товара ---
def show_product_modal(product, all_variants, df):
    """Показывает детальную информацию о товаре в модальном окне"""
    st.markdown("---")
    st.markdown("### 📦 Детальная информация о товаре")
    
    # Кнопка закрытия
    if st.button("← Назад к каталогу"):
        st.session_state.selected_product = None
        st.rerun()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Основное фото
        image_paths = get_image_paths(product['image'], product['sku'])
        display_product_photo(image_paths, key_suffix=f"modal_{product['sku']}")
    
    with col2:
        # Информация о товаре
        st.markdown(f"# {product['brand']} {product['model_clean']}")
        st.markdown(f"**Цвет:** {product['color']}")
        st.markdown(f"**Пол:** {product['gender']}")
        
        # Размеры
        us_sizes = product['size_us']
        eu_sizes = product['size_eu']
        
        if us_sizes:
            st.markdown(f"**US размеры:** {', '.join(us_sizes)}")
        if eu_sizes:
            st.markdown(f"**EU размеры:** {', '.join(eu_sizes)}")
        
        # Цена
        price = product['price']
        if price and str(price).strip() and str(price) != 'nan':
            st.markdown(f"# {price} ₸")
        else:
            st.markdown("**Цена:** Не указана")
        
        # Кнопка добавления в корзину
        if st.button("🛒 Добавить в корзину", use_container_width=True, type="primary"):
            add_to_cart({
                'brand': product['brand'],
                'model': product['model_clean'],
                'color': product['color'],
                'size_us': us_sizes[0] if us_sizes else "",
                'price': price if price and str(price).strip() else "0"
            })
    
    # Другие цвета этой модели
    st.markdown("---")
    st.markdown("### 🎨 Другие цвета этой модели")
    
    if len(all_variants) > 1:
        cols = st.columns(min(len(all_variants), 4))
        
        for idx, (_, variant) in enumerate(all_variants.iterrows()):
            with cols[idx % 4]:
                # Миниатюра цвета
                variant_images = get_image_paths(variant['image'], variant['sku'])
                
                if variant_images:
                    try:
                        st.image(variant_images[0], use_container_width=True)
                    except:
                        st.markdown("""
                            <div style="text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;">
                                ❌
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;">
                            📷
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"**{variant['color']}**")
                
                # Кнопка переключения на этот цвет
                if st.button(f"Выбрать {variant['color']}", key=f"variant_{variant['sku']}", use_container_width=True):
                    st.session_state.selected_product = {
                        'product': variant,
                        'all_variants': all_variants
                    }
                    st.rerun()
    else:
        st.info("Другие цвета для этой модели не найдены")

# --- Основной интерфейс ---
st.markdown("## 👟 Каталог товаров")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Обновить каталог"):
        st.cache_data.clear()
        st.rerun()

# --- Загружаем данные ---
with st.spinner("📥 Загрузка каталога..."):
    df = load_data()

if df.empty:
    st.error("Каталог пуст или не загружен")
    st.stop()

# --- Показываем модальное окно если товар выбран ---
if st.session_state.selected_product is not None:
    show_product_modal(
        st.session_state.selected_product['product'], 
        st.session_state.selected_product['all_variants'],
        df
    )
else:
    # --- Обычный каталог ---
    with st.sidebar:
        st.header("📊 Информация")
        st.write(f"Всего товаров: {len(df)}")
        st.write(f"Бренды: {len(df['brand'].unique())}")
        st.write(f"Модели: {len(df['model_clean'].unique())}")

    # --- Фильтры ---
    st.markdown("### 🔍 Фильтры")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        brands = ["Все"] + sorted(df['brand'].unique().tolist())
        brand_filter = st.selectbox("Бренд", brands)
    with col2:
        colors = ["Все"] + sorted(df['color'].unique().tolist())
        color_filter = st.selectbox("Цвет", colors)
    with col3:
        genders = ["Все"] + sorted(df['gender'].unique().tolist())
        gender_filter = st.selectbox("Пол", genders)
    with col4:
        sizes = ["Все"] + sorted([s for s in df['size_us'].unique() if s])
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

    # --- Группируем отфильтрованные товары ---
    grouped_products = group_products(filtered_df)

    if grouped_products.empty:
        st.warning("🚫 Товары по выбранным фильтрам не найдены")
    else:
        st.success(f"🎯 Найдено {len(grouped_products)} товаров")
        
        # Показываем товары
        num_cols = 4
        for i in range(0, len(grouped_products), num_cols):
            cols = st.columns(num_cols)
            batch = grouped_products.iloc[i:i+num_cols]
            
            for col_idx, (_, product) in zip(cols, batch.iterrows()):
                with col_idx:
                    # Карточка товара (кликабельная)
                    st.markdown("""
                        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer;" onclick="this.nextElementSibling.querySelector('button').click()">
                    """, unsafe_allow_html=True)
                    
                    # Фото
                    image_paths = get_image_paths(product['image'], product['sku'])
                    display_product_photo(image_paths, key_suffix=f"main_{product['sku']}_{i}_{col_idx}")
                    
                    # Информация
                    st.markdown(f"**{product['brand']} {product['model_clean']}**")
                    st.write(f"🎨 {product['color']}")
                    st.write(f"👫 {product['gender']}")
                    
                    # Размеры
                    us_sizes = product['size_us']
                    eu_sizes = product['size_eu']
                    
                    if us_sizes:
                        st.write(f"👟 US: {', '.join(us_sizes[:3])}{'...' if len(us_sizes) > 3 else ''}")
                    
                    # Цена
                    price = product['price']
                    if price and str(price).strip() and str(price) != 'nan':
                        st.markdown(f"**💰 {price} ₸**")
                    else:
                        st.write("💵 Цена не указана")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Невидимая кнопка для открытия модального окна
                    if st.button("📖 Подробнее", key=f"details_{product['sku']}_{i}_{col_idx}", use_container_width=True):
                        all_variants = get_product_variants(df, product['brand'], product['model_clean'])
                        st.session_state.selected_product = {
                            'product': product,
                            'all_variants': all_variants
                        }
                        st.rerun()

st.markdown("---")
st.caption("© DENE Store 2025")