import streamlit as st
import pandas as pd
import glob
import os
import re
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(
    page_title="DENE Store", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS стили как у Intertop ---
st.markdown("""
<style>
    /* Основные стили */
    .main {
        background-color: #ffffff;
    }
    
    /* Хедер */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    
    /* Карточки товаров */
    .product-card {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        background: white;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    /* Кнопки */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    .secondary-button {
        background: #f8f9fa !important;
        color: #333 !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* Бейджи */
    .badge {
        background: #ff4444;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* Фильтры */
    .filter-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    /* Навигация */
    .nav-tabs {
        display: flex;
        border-bottom: 2px solid #e5e5e5;
        margin-bottom: 2rem;
    }
    
    .nav-tab {
        padding: 12px 24px;
        margin-right: 8px;
        cursor: pointer;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    
    .nav-tab.active {
        background: #667eea;
        color: white;
    }
    
    /* Цены */
    .price {
        font-size: 1.25rem;
        font-weight: bold;
        color: #2c5530;
    }
    
    .old-price {
        text-decoration: line-through;
        color: #999;
        font-size: 0.9rem;
    }
    
    /* Корзина */
    .cart-item {
        border-bottom: 1px solid #eee;
        padding: 12px 0;
    }
    
    /* Изображения */
    .product-image {
        border-radius: 8px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Обложка ---
st.markdown('<div class="header">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h1 style='text-align:center; color:white; margin:0;'>DENE STORE</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:white; margin:0; opacity:0.9;'>Премиальные кроссовки и спортивная обувь</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Инициализация сессии ---
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Каталог"

# --- Навигационные табы ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 Главная", use_container_width=True):
        st.session_state.current_tab = "Главная"
with col2:
    if st.button("👟 Каталог", use_container_width=True):
        st.session_state.current_tab = "Каталог"
with col3:
    if st.button("🔥 Новинки", use_container_width=True):
        st.session_state.current_tab = "Новинки"
with col4:
    if st.button("🏷️ Акции", use_container_width=True):
        st.session_state.current_tab = "Акции"
with col5:
    cart_count = len(st.session_state.cart)
    badge = f" 🛒 ({cart_count})" if cart_count > 0 else " 🛒 Корзина"
    if st.button(badge, use_container_width=True):
        st.session_state.current_tab = "Корзина"

st.markdown("---")

# --- Загрузка данных ---
@st.cache_data(ttl=300)
def load_data():
    try:
        if not os.path.exists(CATALOG_PATH):
            return pd.DataFrame()
        
        df_nike = pd.read_excel(CATALOG_PATH, sheet_name='Nike')
        df_mizuno = pd.read_excel(CATALOG_PATH, sheet_name='Mizuno')
        
        df = pd.concat([df_nike, df_mizuno], ignore_index=True)
        
        # Заполнение пропущенных значений
        columns_to_fill = ['brand', 'model', 'color', 'gender', 'image']
        for col in columns_to_fill:
            if col in df.columns:
                df[col] = df[col].fillna(method='ffill').fillna('')
        
        # Очистка названий моделей
        df["model_clean"] = df["model"].apply(lambda x: re.sub(r'\([^)]*\)', '', str(x))).str.strip()
        
        # Обработка размеров
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
        
        # Фильтрация валидных данных
        df = df[
            (df['brand'].notna()) & (df['brand'] != '') &
            (df['model_clean'].notna()) & (df['model_clean'] != '')
        ]
        
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
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

def display_product_image(image_paths, product_name, key_suffix=""):
    if not image_paths:
        st.markdown(f"""
            <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 12px; height: 200px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <div style="font-size: 48px; color: #ccc;">👟</div>
                <div style="color: #999;">Нет изображения</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    if f"selected_{key_suffix}" not in st.session_state:
        st.session_state[f"selected_{key_suffix}"] = 0
    
    selected_index = st.session_state[f"selected_{key_suffix}"]
    
    try:
        img = Image.open(image_paths[selected_index])
        st.image(img, use_container_width=True, caption=product_name)
    except:
        st.markdown(f"""
            <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 12px; height: 200px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <div style="font-size: 48px; color: #ccc;">❌</div>
                <div style="color: #999;">Ошибка загрузки</div>
            </div>
        """, unsafe_allow_html=True)

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
    variants = df[
        (df['brand'] == brand) & 
        (df['model_clean'] == model_clean) &
        (df['color'] != current_color)
    ].drop_duplicates('color')
    return variants

# --- Корзина ---
def add_to_cart(item):
    st.session_state.cart.append(item)
    st.success(f"✅ {item['brand']} {item['model']} добавлен в корзину")

def display_cart_page():
    st.markdown("## 🛒 Корзина покупок")
    
    if not st.session_state.cart:
        st.info("""
        ### Ваша корзина пуста
        Перейдите в каталог, чтобы добавить товары
        """)
        return
    
    total = 0
    for i, item in enumerate(st.session_state.cart):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{item['brand']} {item['model']}**")
                st.markdown(f"Цвет: {item['color']} | Размер: {item['size_us']}US")
            with col2:
                st.markdown(f"**{item['price']} ₸**")
            with col3:
                st.markdown("Кол-во: 1")
            with col4:
                if st.button("🗑️ Удалить", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
        
        total += float(item['price']) if item['price'] and str(item['price']).strip() else 0
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### Итого: {total:,.0f} ₸")
    with col2:
        if st.button("📦 Оформить заказ", type="primary", use_container_width=True):
            st.success("🎉 Заказ оформлен! С вами свяжутся для подтверждения.")
            st.session_state.cart = []
    
    if st.button("🗑️ Очистить корзину", type="secondary"):
        st.session_state.cart = []
        st.rerun()

# --- Детальная страница товара ---
def show_product_details(product, other_colors, df):
    st.markdown("### Детали товара")
    
    if st.button("← Назад к каталогу"):
        st.session_state.selected_product = None
        st.rerun()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        image_paths = get_image_paths(product['image'], product['sku'])
        display_product_image(image_paths, f"{product['brand']} {product['model_clean']}", 
                            key_suffix=f"detail_{product['sku']}")
    
    with col2:
        st.markdown(f"## {product['brand']} {product['model_clean']}")
        st.markdown(f"**Цвет:** {product['color']}")
        st.markdown(f"**Пол:** {product['gender']}")
        
        # Размеры
        us_sizes = product['size_us']
        eu_sizes = product['size_eu']
        
        if us_sizes:
            selected_size = st.selectbox("Выберите размер (US):", us_sizes)
        else:
            selected_size = "Не указан"
            st.warning("Размеры не указаны")
        
        # Цена
        price = product['price']
        if price and str(price).strip() and str(price) != 'nan':
            st.markdown(f'<div class="price">{price} ₸</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="price">Цена не указана</div>', unsafe_allow_html=True)
        
        # Кнопка добавления в корзину
        if st.button("🛒 Добавить в корзину", use_container_width=True, type="primary"):
            add_to_cart({
                'brand': product['brand'],
                'model': product['model_clean'],
                'color': product['color'],
                'size_us': selected_size,
                'price': price if price and str(price).strip() else "0"
            })
    
    # Другие цвета
    if not other_colors.empty:
        st.markdown("---")
        st.markdown("### Другие цвета")
        
        cols = st.columns(min(len(other_colors), 4))
        
        for idx, (_, variant) in enumerate(other_colors.iterrows()):
            with cols[idx]:
                with st.container():
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    
                    variant_images = get_image_paths(variant['image'], variant['sku'])
                    if variant_images:
                        try:
                            st.image(variant_images[0], use_container_width=True)
                        except:
                            st.markdown("""
                                <div style="text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px; color: #999;">
                                    ❌
                                </div>
                            """, unsafe_allow_html=True)
                    
                    st.write(f"**{variant['color']}**")
                    
                    variant_price = variant['price']
                    if variant_price and str(variant_price).strip():
                        st.write(f"{variant_price} ₸")
                    
                    if st.button("Выбрать", key=f"select_{variant['sku']}", use_container_width=True):
                        new_other_colors = get_other_colors(df, variant['brand'], variant['model_clean'], variant['color'])
                        st.session_state.selected_product = {
                            'product': variant,
                            'other_colors': new_other_colors
                        }
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# --- Главная страница ---
def show_home_page():
    st.markdown("""
    ## 🏠 Добро пожаловать в DENE Store!
    
    ### Лучшие предложения недели
    """)
    
    # Промо-блоки
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 12px; text-align: center;">
            <h3>🚀 Новинки</h3>
            <p>Самые свежие модели сезона</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 2rem; border-radius: 12px; text-align: center;">
            <h3>🔥 Распродажа</h3>
            <p>Скидки до 50%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 2rem; border-radius: 12px; text-align: center;">
            <h3>⭐ Бестселлеры</h3>
            <p>Самые популярные модели</p>
        </div>
        """, unsafe_allow_html=True)

# --- Каталог товаров ---
def show_catalog_page():
    st.markdown("## 👟 Каталог товаров")
    
    # Загружаем данные
    with st.spinner('🔄 Загрузка каталога...'):
        df = load_data()
    
    if df.empty:
        st.error("Каталог пуст или не загружен")
        return
    
    # Фильтры в виде карточек
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown("### 🔍 Поиск и фильтры")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            brands = ["Все бренды"] + sorted(df['brand'].unique().tolist())
            brand_filter = st.selectbox("Бренд", brands)
        
        with col2:
            if brand_filter != "Все бренды":
                brand_models = sorted(df[df["brand"] == brand_filter]["model_clean"].unique().tolist())
            else:
                brand_models = sorted(df["model_clean"].unique().tolist())
            model_filter = st.selectbox("Модель", ["Все модели"] + brand_models)
        
        with col3:
            sizes_us = ["Все размеры"] + sorted([s for s in df['size_us'].unique() if s])
            size_us_filter = st.selectbox("Размер US", sizes_us)
        
        with col4:
            colors = ["Все цвета"] + sorted(df['color'].unique().tolist())
            color_filter = st.selectbox("Цвет", colors)
        
        search_query = st.text_input("Поиск по названию...", placeholder="Введите название модели или бренда")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Применяем фильтры
    filtered_df = df.copy()
    if brand_filter != "Все бренды":
        filtered_df = filtered_df[filtered_df['brand'] == brand_filter]
    if model_filter != "Все модели":
        filtered_df = filtered_df[filtered_df['model_clean'] == model_filter]
    if size_us_filter != "Все размеры":
        filtered_df = filtered_df[filtered_df['size_us'] == size_us_filter]
    if color_filter != "Все цвета":
        filtered_df = filtered_df[filtered_df['color'] == color_filter]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["model_clean"].str.contains(search_query, case=False, na=False) |
            filtered_df["brand"].str.contains(search_query, case=False, na=False)
        ]
    
    # Группируем товары
    grouped_products = group_products(filtered_df)
    
    if grouped_products.empty:
        st.warning("😔 Товары по заданным фильтрам не найдены.")
        st.info("Попробуйте изменить параметры фильтрации")
    else:
        st.markdown(f"### Найдено товаров: {len(grouped_products)}")
        
        # Отображение товаров в сетке
        num_cols = 4
        rows = [grouped_products.iloc[i:i+num_cols] for i in range(0, len(grouped_products), num_cols)]
        
        for i, row_df in enumerate(rows):
            cols = st.columns(num_cols)
            for col_idx, (_, product) in zip(cols, row_df.iterrows()):
                with col_idx:
                    with st.container():
                        st.markdown('<div class="product-card">', unsafe_allow_html=True)
                        
                        # Фото товара
                        image_paths = get_image_paths(product['image'], product['sku'])
                        display_product_image(image_paths, f"{product['brand']} {product['model_clean']}", 
                                            key_suffix=f"main_{product['sku']}_{i}_{col_idx}")
                        
                        # Информация о товаре
                        st.markdown(f"**{product['brand']}**")
                        st.markdown(f"**{product['model_clean']}**")
                        st.markdown(f"*{product['color']}*")
                        
                        # Размеры
                        us_sizes = product['size_us']
                        if us_sizes:
                            st.markdown(f"Размеры US: {', '.join(us_sizes[:3])}{'...' if len(us_sizes) > 3 else ''}")
                        
                        # Цена
                        price = product['price']
                        if price and str(price).strip() and str(price) != 'nan':
                            st.markdown(f'<div class="price">{price} ₸</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color: #999;">Цена не указана</div>', unsafe_allow_html=True)
                        
                        # Кнопки
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("👀 Подробнее", key=f"view_{product['sku']}_{i}_{col_idx}", 
                                       use_container_width=True):
                                other_colors = get_other_colors(df, product['brand'], product['model_clean'], product['color'])
                                st.session_state.selected_product = {
                                    'product': product,
                                    'other_colors': other_colors
                                }
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("🛒 Купить", key=f"buy_{product['sku']}_{i}_{col_idx}", 
                                       use_container_width=True, type="primary"):
                                add_to_cart({
                                    'brand': product['brand'],
                                    'model': product['model_clean'],
                                    'color': product['color'],
                                    'size_us': us_sizes[0] if us_sizes else "",
                                    'price': price if price and str(price).strip() else "0"
                                })
                        
                        st.markdown('</div>', unsafe_allow_html=True)

# --- Основная логика приложения ---
def main():
    # Показываем детальную страницу если товар выбран
    if st.session_state.selected_product is not None:
        show_product_details(
            st.session_state.selected_product['product'], 
            st.session_state.selected_product['other_colors'],
            load_data()
        )
    else:
        # Показываем соответствующую страницу по табу
        if st.session_state.current_tab == "Главная":
            show_home_page()
            show_catalog_page()  # Показываем часть каталога на главной
        elif st.session_state.current_tab == "Каталог":
            show_catalog_page()
        elif st.session_state.current_tab == "Новинки":
            st.markdown("## 🔥 Новинки")
            # Здесь можно добавить фильтрацию по новинкам
            show_catalog_page()
        elif st.session_state.current_tab == "Акции":
            st.markdown("## 🏷️ Акции и скидки")
            st.info("Скоро появятся специальные предложения!")
            show_catalog_page()
        elif st.session_state.current_tab == "Корзина":
            display_cart_page()
    
    # Футер
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <h3>DENE STORE</h3>
        <p>Премиальные кроссовки и спортивная обувь</p>
        <p>© 2025 DENE Store. Все права защищены.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()