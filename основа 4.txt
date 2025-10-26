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

# --- Загрузка данных ---
@st.cache_data(ttl=300)
def load_data():
    try:
        if not os.path.exists(CATALOG_PATH):
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
        
        return df
        
    except Exception as e:
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
            st.markdown("""
                <div style="text-align: center; padding: 60px; background: #f5f5f5; border-radius: 12px; color: #999;">
                    <div style="font-size: 36px;">❌</div>
                    <div>Ошибка загрузки изображения</div>
                </div>
            """, unsafe_allow_html=True)

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

def get_other_colors(df, brand, model_clean, current_color):
    """Получает другие цвета для данной модели (исключая текущий)"""
    variants = df[
        (df['brand'] == brand) & 
        (df['model_clean'] == model_clean) &
        (df['color'] != current_color)
    ].drop_duplicates('color')
    return variants

# --- Корзина ---
def add_to_cart(item):
    st.session_state.cart.append(item)
    st.success(f"✅ Добавлено: {item['brand']} {item['model']} {item['size_us']}US")

def display_cart():
    if not st.session_state.cart:
        st.info("🛒 Корзина пуста")
        return
    
    st.subheader("🛒 Ваша корзина")
    
    total = 0
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        with col1:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"Цвет: {item['color']}")
            st.write(f"Размер: {item['size_us']}US")
        with col2:
            st.write(f"{item['price']} ₸")
        with col3:
            if st.button("🗑️", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        
        total += float(item['price']) if item['price'] and str(item['price']).strip() else 0
    
    st.markdown(f"**Итого: {total} ₸**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Оформить заказ", type="primary"):
            st.success("🎉 Заказ оформлен! С вами свяжутся для подтверждения.")
    with col2:
        if st.button("🗑️ Очистить корзину", type="secondary"):
            st.session_state.cart = []
            st.rerun()

# --- Детальная страница товара ---
def show_product_details(product, other_colors, df):
    """Показывает детальную информацию о товаре"""
    
    # Кнопка назад
    if st.button("← Назад к каталогу"):
        st.session_state.selected_product = None
        st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Фото товара
        image_paths = get_image_paths(product['image'], product['sku'])
        display_product_photo(image_paths, key_suffix=f"detail_{product['sku']}")
    
    with col2:
        # Информация о товаре
        st.markdown(f"**{product['brand']} {product['model_clean']}**")
        st.write(f"Цвет: {product['color']}")
        st.write(f"{product['gender']}")
        
        # Размеры
        us_sizes = product['size_us']
        eu_sizes = product['size_eu']
        
        if us_sizes or eu_sizes:
            sizes_text = f"US: {', '.join(us_sizes)}" if us_sizes else ""
            if eu_sizes:
                sizes_text += f" | EU: {', '.join(eu_sizes)}" if sizes_text else f"EU: {', '.join(eu_sizes)}"
            st.write(sizes_text)
        else:
            st.write("Размеры не указаны")
        
        # Цена
        price = product['price']
        if price and str(price).strip() and str(price) != 'nan':
            st.markdown(f"**{price} ₸**")
        else:
            st.write("Цена не указана")
        
        # Кнопка добавления в корзину
        if st.button("🛒 Добавить в корзину", use_container_width=True, type="primary"):
            add_to_cart({
                'brand': product['brand'],
                'model': product['model_clean'],
                'color': product['color'],
                'size_us': us_sizes[0] if us_sizes else "",
                'price': price if price and str(price).strip() else "0"
            })
    
    # Другие цвета (только если есть)
    if not other_colors.empty:
        st.markdown("---")
        st.markdown("**Другие цвета:**")
        
        cols = st.columns(min(len(other_colors), 4))
        
        for idx, (_, variant) in enumerate(other_colors.iterrows()):
            with cols[idx]:
                variant_images = get_image_paths(variant['image'], variant['sku'])
                
                if variant_images:
                    try:
                        st.image(variant_images[0], width=100)
                    except:
                        st.markdown("""
                            <div style="text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px; color: #999;">
                                ❌
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px; color: #999;">
                            📷
                        </div>
                    """, unsafe_allow_html=True)
                
                st.write(f"{variant['color']}")
                
                if st.button("Выбрать", key=f"select_{variant['sku']}", use_container_width=True):
                    new_other_colors = get_other_colors(df, variant['brand'], variant['model_clean'], variant['color'])
                    st.session_state.selected_product = {
                        'product': variant,
                        'other_colors': new_other_colors
                    }
                    st.rerun()

# --- Основной интерфейс ---
st.markdown("## 👟 Каталог товаров")

# --- Загружаем данные ---
with st.spinner('🔄 Загрузка каталога...'):
    df = load_data()

if df.empty:
    st.error("Каталог пуст или не загружен")
    st.stop()

# --- Боковая панель ---
with st.sidebar:
    st.header("🛒 Корзина")
    display_cart()
    
    st.header("🔍 Поиск")
    search_query = st.text_input("Поиск по названию", "")
    
    st.header("Настройки")
    items_per_page = st.slider("Товаров на странице", 8, 32, 16)

# --- Показываем детальную страницу если товар выбран ---
if st.session_state.selected_product is not None:
    show_product_details(
        st.session_state.selected_product['product'], 
        st.session_state.selected_product['other_colors'],
        df
    )
else:
    # --- Обычный каталог ---
    
    # Фильтры
    st.markdown("### Фильтр каталога")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        brands = ["Все"] + sorted(df['brand'].unique().tolist())
        brand_filter = st.selectbox("Бренд", brands)
    with col2:
        if brand_filter != "Все":
            brand_models = sorted(df[df["brand"] == brand_filter]["model_clean"].unique().tolist())
        else:
            brand_models = sorted(df["model_clean"].unique().tolist())
        model_filter = st.selectbox("Модель", ["Все"] + brand_models)
    with col3:
        sizes_us = ["Все"] + sorted([s for s in df['size_us'].unique() if s])
        size_us_filter = st.selectbox("Размер (US)", sizes_us)
    with col4:
        sizes_eu = ["Все"] + sorted([s for s in df['size_eu'].unique() if s])
        size_eu_filter = st.selectbox("Размер (EU)", sizes_eu)
    with col5:
        genders = ["Все", "men", "women", "unisex"]
        gender_filter = st.selectbox("Пол", genders)
    with col6:
        colors = ["Все"] + sorted(df['color'].unique().tolist())
        color_filter = st.selectbox("Цвет", colors)

    # Применяем фильтры
    filtered_df = df.copy()
    if brand_filter != "Все":
        filtered_df = filtered_df[filtered_df['brand'] == brand_filter]
    if model_filter != "Все":
        filtered_df = filtered_df[filtered_df['model_clean'] == model_filter]
    if size_us_filter != "Все":
        filtered_df = filtered_df[filtered_df['size_us'] == size_us_filter]
    if size_eu_filter != "Все":
        filtered_df = filtered_df[filtered_df['size_eu'] == size_eu_filter]
    if gender_filter != "Все":
        filtered_df = filtered_df[filtered_df['gender'] == gender_filter]
    if color_filter != "Все":
        filtered_df = filtered_df[filtered_df['color'] == color_filter]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["model_clean"].str.contains(search_query, case=False, na=False) |
            filtered_df["brand"].str.contains(search_query, case=False, na=False)
        ]

    # Группируем товары
    grouped_products = group_products(filtered_df)

    if grouped_products.empty:
        st.warning("Товары по заданным фильтрам не найдены.")
    else:
        # Показываем товары
        num_cols = 4
        rows = [grouped_products.iloc[i:i+num_cols] for i in range(0, len(grouped_products), num_cols)]

        for i, row_df in enumerate(rows):
            cols = st.columns(num_cols)
            for col_idx, (_, product) in zip(cols, row_df.iterrows()):
                with col_idx:
                    # Карточка товара
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
                        
                        # Фото
                        image_paths = get_image_paths(product['image'], product['sku'])
                        display_product_photo(image_paths, key_suffix=f"main_{product['sku']}_{i}_{col_idx}")
                        
                        # Информация
                        st.markdown(f"**{product['brand']} {product['model_clean']}**")
                        st.write(f"{product['color']} | {product['gender']}")
                        
                        # Размеры
                        us_sizes = product['size_us']
                        eu_sizes = product['size_eu']
                        
                        if us_sizes or eu_sizes:
                            sizes_text = f"US: {', '.join(us_sizes)}" if us_sizes else ""
                            if eu_sizes:
                                sizes_text += f" | EU: {', '.join(eu_sizes)}" if sizes_text else f"EU: {', '.join(eu_sizes)}"
                            st.write(sizes_text)
                        else:
                            st.write("Размеры не указаны")
                        
                        # Цена
                        price = product['price']
                        if price and str(price).strip() and str(price) != 'nan':
                            st.markdown(f"**{price} ₸**")
                        else:
                            st.write("Цена не указана")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Кнопка для детального просмотра
                    if st.button("Подробнее", key=f"view_{product['sku']}_{i}_{col_idx}", use_container_width=True):
                        other_colors = get_other_colors(df, product['brand'], product['model_clean'], product['color'])
                        st.session_state.selected_product = {
                            'product': product,
                            'other_colors': other_colors
                        }
                        st.rerun()

st.markdown("---")
st.caption("© DENE Store 2025")