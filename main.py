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

def display_product_photos(image_paths, key_suffix=""):
    """Отображение фото как на Intertop - большое фото + миниатюры снизу"""
    if not image_paths:
        st.markdown("""
            <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 12px;">
                <div style="color: #666;">Нет изображений</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    if f"selected_{key_suffix}" not in st.session_state:
        st.session_state[f"selected_{key_suffix}"] = 0
    
    selected_index = st.session_state[f"selected_{key_suffix}"]
    
    # Основное большое фото
    try:
        st.image(image_paths[selected_index], use_container_width=True)
    except:
        st.markdown("""
            <div style="text-align: center; padding: 60px; background: #f5f5f5; border-radius: 12px; color: #999;">
                Ошибка загрузки изображения
            </div>
        """, unsafe_allow_html=True)
    
    # Миниатюры под основным фото
    if len(image_paths) > 1:
        cols = st.columns(len(image_paths[:4]))
        for i, img_path in enumerate(image_paths[:4]):
            with cols[i]:
                # Рамка вокруг выбранной миниатюры
                border_style = "2px solid #000" if i == selected_index else "1px solid #ddd"
                st.markdown(f"<div style='border: {border_style}; border-radius: 4px; padding: 2px;'>", unsafe_allow_html=True)
                
                if st.button("", key=f"thumb_{key_suffix}_{i}", use_container_width=True):
                    st.session_state[f"selected_{key_suffix}"] = i
                    st.rerun()
                
                try:
                    st.image(img_path, use_container_width=True)
                except:
                    st.markdown("<div style='text-align: center; padding: 20px;'>❌</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

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
    """Получает другие цвета для данной модели"""
    variants = df[
        (df['brand'] == brand) & 
        (df['model_clean'] == model_clean) &
        (df['color'] != current_color)
    ].drop_duplicates('color')
    return variants

# --- Корзина ---
def add_to_cart(item):
    st.session_state.cart.append(item)
    st.success(f"Добавлено: {item['brand']} {item['model']} {item['size_us']}US")

def display_cart():
    if not st.session_state.cart:
        st.info("Корзина пуста")
        return
    
    st.subheader("Корзина")
    
    total = 0
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"Цвет: {item['color']}")
            st.write(f"Размер: {item['size_us']}US")
        with col2:
            st.write(f"{item['price']} ₸")
        with col3:
            if st.button("Удалить", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        
        total += float(item['price']) if item['price'] and str(item['price']).strip() else 0
    
    st.markdown(f"**Итого: {total} ₸**")
    
    if st.button("Оформить заказ", type="primary"):
        st.success("Заказ оформлен! С вами свяжутся для подтверждения.")

# --- Детальная страница товара как на Intertop ---
def show_product_details(product, other_colors, df):
    """Детальная страница товара в стиле Intertop"""
    
    # Хлебные крошки
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**Главная → {product['brand']} → {product['model_clean']}**")
    with col2:
        if st.button("← Назад к каталогу"):
            st.session_state.selected_product = None
            st.rerun()
    
    st.markdown("---")
    
    # Основная информация о товаре
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Фото товара
        image_paths = get_image_paths(product['image'], product['sku'])
        display_product_photos(image_paths, key_suffix=f"detail_{product['sku']}")
    
    with col2:
        # Информация о товаре
        st.markdown(f"## {product['brand']} {product['model_clean']}")
        
        # Цена
        price = product['price']
        if price and str(price).strip() and str(price) != 'nan':
            st.markdown(f"# {price} ₸")
        else:
            st.markdown("### Цена не указана")
        
        st.markdown("---")
        
        # Цвет
        st.markdown(f"**Цвет:** {product['color']}")
        
        # Другие цвета
        if not other_colors.empty:
            st.markdown("**Другие цвета:**")
            color_cols = st.columns(len(other_colors))
            for idx, (_, variant) in enumerate(other_colors.iterrows()):
                with color_cols[idx]:
                    if st.button(variant['color'], key=f"color_{variant['sku']}", use_container_width=True):
                        new_other_colors = get_other_colors(df, variant['brand'], variant['model_clean'], variant['color'])
                        st.session_state.selected_product = {
                            'product': variant,
                            'other_colors': new_other_colors
                        }
                        st.rerun()
        
        st.markdown("---")
        
        # Размеры
        st.markdown("**Выберите размер:**")
        us_sizes = product['size_us']
        eu_sizes = product['size_eu']
        
        if us_sizes:
            # Показываем размеры в виде сетки кнопок
            size_cols = st.columns(4)
            for i, size in enumerate(us_sizes):
                with size_cols[i % 4]:
                    if st.button(f"{size} US", key=f"size_{size}", use_container_width=True):
                        selected_size = size
        
        st.markdown("---")
        
        # Кнопка добавления в корзину
        if st.button("Добавить в корзину", type="primary", use_container_width=True):
            selected_size = us_sizes[0] if us_sizes else ""
            add_to_cart({
                'brand': product['brand'],
                'model': product['model_clean'],
                'color': product['color'],
                'size_us': selected_size,
                'price': price if price and str(price).strip() else "0"
            })
        
        # Информация о доставке и возврате
        with st.expander("Информация о доставке и возврате"):
            st.write("• Бесплатная доставка от 20 000 ₸")
            st.write("• Доставка по городу 1-2 дня")
            st.write("• Легкий возврат в течение 14 дней")
            st.write("• Гарантия качества")

# --- Основной интерфейс ---
st.markdown("## Каталог товаров")

# --- Загружаем данные ---
with st.spinner('Загрузка каталога...'):
    df = load_data()

if df.empty:
    st.error("Каталог пуст или не загружен")
    st.stop()

# --- Боковая панель ---
with st.sidebar:
    st.header("Корзина")
    display_cart()
    
    st.header("Поиск")
    search_query = st.text_input("Поиск по названию", "")
    
    st.header("Фильтры")
    
    # Бренд
    brands = ["Все бренды"] + sorted(df['brand'].unique().tolist())
    brand_filter = st.selectbox("Бренд", brands)
    
    # Цвет
    colors = ["Все цвета"] + sorted(df['color'].unique().tolist())
    color_filter = st.selectbox("Цвет", colors)
    
    # Размер
    sizes = ["Все размеры"] + sorted([s for s in df['size_us'].unique() if s])
    size_filter = st.selectbox("Размер US", sizes)
    
    # Пол
    genders = ["Все", "men", "women", "unisex"]
    gender_filter = st.selectbox("Пол", genders)
    
    # Сортировка
    sort_option = st.selectbox("Сортировка", [
        "По популярности", 
        "По цене (сначала дешевые)",
        "По цене (сначала дорогие)",
        "По новизне"
    ])

# --- Показываем детальную страницу если товар выбран ---
if st.session_state.selected_product is not None:
    show_product_details(
        st.session_state.selected_product['product'], 
        st.session_state.selected_product['other_colors'],
        df
    )
else:
    # --- Обычный каталог ---
    
    # Применяем фильтры
    filtered_df = df.copy()
    if brand_filter != "Все бренды":
        filtered_df = filtered_df[filtered_df['brand'] == brand_filter]
    if color_filter != "Все цвета":
        filtered_df = filtered_df[filtered_df['color'] == color_filter]
    if size_filter != "Все размеры":
        filtered_df = filtered_df[filtered_df['size_us'] == size_filter]
    if gender_filter != "Все":
        filtered_df = filtered_df[filtered_df['gender'] == gender_filter]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["model_clean"].str.contains(search_query, case=False, na=False) |
            filtered_df["brand"].str.contains(search_query, case=False, na=False)
        ]

    # Сортировка
    if sort_option == "По цене (сначала дешевые)":
        filtered_df = filtered_df.sort_values('price', ascending=True)
    elif sort_option == "По цене (сначала дорогие)":
        filtered_df = filtered_df.sort_values('price', ascending=False)

    # Группируем товары
    grouped_products = group_products(filtered_df)

    if grouped_products.empty:
        st.warning("Товары по заданным фильтрам не найдены.")
    else:
        # Показываем товары в сетке
        num_cols = 4
        rows = [grouped_products.iloc[i:i+num_cols] for i in range(0, len(grouped_products), num_cols)]

        for i, row_df in enumerate(rows):
            cols = st.columns(num_cols)
            for col_idx, (_, product) in zip(cols, row_df.iterrows()):
                with col_idx:
                    # Карточка товара
                    with st.container():
                        # Фото
                        image_paths = get_image_paths(product['image'], product['sku'])
                        if image_paths:
                            try:
                                st.image(image_paths[0], use_container_width=True)
                            except:
                                st.markdown("<div style='height: 200px; background: #f5f5f5; display: flex; align-items: center; justify-content: center;'>Нет фото</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='height: 200px; background: #f5f5f5; display: flex; align-items: center; justify-content: center;'>Нет фото</div>", unsafe_allow_html=True)
                        
                        # Информация
                        st.markdown(f"**{product['brand']}**")
                        st.markdown(f"*{product['model_clean']}*")
                        st.write(f"Цвет: {product['color']}")
                        
                        # Цена
                        price = product['price']
                        if price and str(price).strip() and str(price) != 'nan':
                            st.markdown(f"**{price} ₸**")
                        else:
                            st.write("Цена не указана")
                        
                        # Кнопка для детального просмотра
                        if st.button("Подробнее", key=f"view_{product['sku']}_{i}_{col_idx}", use_container_width=True):
                            other_colors = get_other_colors(df, product['brand'], product['model_clean'], product['color'])
                            st.session_state.selected_product = {
                                'product': product,
                                'other_colors': other_colors
                            }
                            st.rerun()

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>© DENE Store 2024</div>", unsafe_allow_html=True)