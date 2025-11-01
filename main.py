import streamlit as st
import pandas as pd
import glob
import os
import re
import base64

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

# --- Функция для безопасной загрузки фото ---
def get_image_path(image_names):
    """Ищет изображение по имени из колонки image (берет первое изображение из списка)"""
    if not image_names or pd.isna(image_names) or str(image_names).strip() == "":
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    # Разбиваем строку на отдельные имена файлов и берем первое
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    first_image_name = image_names_list[0]  # Берем первое изображение
    
    # Ищем файл с разными расширениями
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(IMAGES_PATH, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        
        # Также ищем файлы, которые начинаются с этого имени
        pattern_start = os.path.join(IMAGES_PATH, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    # Если файл не найден, возвращаем no_image
    return os.path.join(IMAGES_PATH, "no_image.jpg")

def get_all_images_for_product(image_names):
    """Возвращает все изображения для товара"""
    if not image_names or pd.isna(image_names) or str(image_names).strip() == "":
        return [os.path.join(IMAGES_PATH, "no_image.jpg")]
    
    image_names_list = str(image_names).strip().split()
    all_images = []
    
    for image_name in image_names_list:
        found = False
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            pattern = os.path.join(IMAGES_PATH, "**", f"{image_name}{ext}")
            image_files = glob.glob(pattern, recursive=True)
            if image_files:
                all_images.append(image_files[0])
                found = True
                break
        
        if not found:
            # Если не нашли конкретное изображение, добавляем no_image
            all_images.append(os.path.join(IMAGES_PATH, "no_image.jpg"))
    
    return all_images if all_images else [os.path.join(IMAGES_PATH, "no_image.jpg")]

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        with open(fallback, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

def get_similar_products(df, current_product):
    """Находит товары той же модели но других цветов"""
    similar = df[
        (df["model_clean"] == current_product["model_clean"]) &
        (df["brand"] == current_product["brand"]) &
        (df["sku"] != current_product["sku"])
    ]
    return similar

# --- Загрузка данных ---
@st.cache_data(show_spinner=False)
def load_data():
    # Читаем все листы Excel файла
    all_sheets = pd.read_excel(CATALOG_PATH, sheet_name=None)
    
    # Объединяем все листы в один DataFrame
    df_list = []
    for sheet_name, sheet_data in all_sheets.items():
        st.sidebar.write(f"📋 Лист '{sheet_name}': {len(sheet_data)} товаров")
        df_list.append(sheet_data)
    
    # Объединяем все данные
    df = pd.concat(df_list, ignore_index=True)
    df = df.fillna("")

    # Обработка модели
    df["model_clean"] = (
        df["model"]
        .str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True)
        .str.strip()
    )

    # Извлекаем размеры
    df["size_us"] = df["model"].apply(lambda x: re.search(r"(\d{1,2}(\.\d)?)(?=US)", x))
    df["size_us"] = df["size_us"].apply(lambda m: m.group(1) if m else "")
    df["size_eu"] = df["model"].apply(lambda x: re.search(r"(\d{2}(\.\d)?)(?=EU)", x))
    df["size_eu"] = df["size_eu"].apply(lambda m: m.group(1) if m else "")

    # Автозаполнение при отсутствии одного из размеров
    df["size_eu"] = df.apply(lambda r: size_conversion.get(r["size_us"], r["size_eu"]), axis=1)
    df["size_us"] = df.apply(lambda r: reverse_conversion.get(r["size_eu"], r["size_us"]), axis=1)

    # Пол и цвет
    df["gender"] = df["model"].apply(
        lambda x: "men" if "men" in x.lower() else (
            "women" if "women" in x.lower() else "unisex"
        )
    )
    df["color"] = df["model"].str.extract(
        r"(white|black|blue|red|green|pink|gray|brown)", expand=False
    ).fillna("other")

    # Описание
    if "description" not in df.columns:
        df["description"] = "Описание временно недоступно."

    # Исключаем товары без цены или модели
    df = df[df["price"].astype(str).str.strip() != ""]
    df = df[df["model_clean"].astype(str).str.strip() != ""]

    return df

# --- ЗАГРУЗКА ДАННЫХ ---
df = load_data()

# --- Инициализация состояния для модальных окон ---
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None
if 'current_image_index' not in st.session_state:
    st.session_state.current_image_index = 0

# --- Функции для работы с модальными окнами ---
def open_product_modal(product):
    st.session_state.selected_product = product
    st.session_state.current_image_index = 0

def close_modal():
    st.session_state.selected_product = None
    st.session_state.current_image_index = 0

def next_image():
    if st.session_state.selected_product:
        all_images = get_all_images_for_product(st.session_state.selected_product["image"])
        st.session_state.current_image_index = (st.session_state.current_image_index + 1) % len(all_images)

def prev_image():
    if st.session_state.selected_product:
        all_images = get_all_images_for_product(st.session_state.selected_product["image"])
        st.session_state.current_image_index = (st.session_state.current_image_index - 1) % len(all_images)

# --- ДИАГНОСТИКА ---
st.sidebar.write("🔍 ДИАГНОСТИКА:")
st.sidebar.write("Всего товаров после объединения:", len(df))
st.sidebar.write("Уникальные бренды:", df["brand"].nunique())
st.sidebar.write("Уникальные модели:", df["model_clean"].nunique())

# --- Фильтры ---
st.divider()
st.markdown("### 🔎 Фильтр каталога")

col1, col2, col3, col4, col5, col6 = st.columns(6)
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
filtered_df = df if brand_filter == "Все" else df[df["brand"] == brand_filter]

models = sorted(filtered_df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + models)

size_us_filter = col3.selectbox("Размер (US)", ["Все"] + sorted(df["size_us"].dropna().unique().tolist()))
size_eu_filter = col4.selectbox("Размер (EU)", ["Все"] + sorted(df["size_eu"].dropna().unique().tolist()))
gender_filter = col5.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col6.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()))

# --- Применяем фильтры ---
filtered_df = df.copy()
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

# --- Сетка карточек товаров ---
st.markdown("## 👟 Каталог товаров")

if len(filtered_df) == 0:
    st.warning("🚫 Товары по выбранным фильтрам не найдены")
else:
    st.write(f"**Найдено товаров: {len(filtered_df)}**")
    
    num_cols = 4
    rows = [filtered_df.iloc[i:i+num_cols] for i in range(0, len(filtered_df), num_cols)]

    for row_df in rows:
        cols = st.columns(num_cols)
        for col, (_, row) in zip(cols, row_df.iterrows()):
            with col:
                # Используем колонку 'image' с именами файлов
                image_path = get_image_path(row["image"])
                image_base64 = get_image_base64(image_path)

                # Создаем карточку товара с кликом
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
                        cursor:pointer;
                    " onclick="
                        const event = new CustomEvent('productClick', {{detail: {row.to_dict()}}});
                        window.parent.document.dispatchEvent(event);
                    " onmouseover="this.style.transform='scale(1.02)';"
                      onmouseout="this.style.transform='scale(1)';">
                        <img src="data:image/jpeg;base64,{image_base64}" 
                             style='width:100%; border-radius:12px; object-fit:cover; height:220px;'>
                        <h4 style="margin:10px 0 4px 0;">{row['brand']} {row['model_clean']}</h4>
                        <p style="color:gray; font-size:13px; margin:0;">
                            US {row['size_us'] or '-'} | EU {row['size_eu'] or '-'} | {row['color']}
                        </p>
                        <p style="font-size:14px; color:#555;">{row['description'][:100]}{'...' if len(row['description']) > 100 else ''}</p>
                        <p style="font-weight:bold; font-size:16px; margin-top:6px;">{int(row['price'])} ₸</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Кнопка для открытия модального окна
                if st.button("👀 Подробнее", key=f"btn_{row['sku']}", use_container_width=True):
                    open_product_modal(row.to_dict())

# --- Модальное окно товара ---
if st.session_state.selected_product:
    product = st.session_state.selected_product
    all_images = get_all_images_for_product(product["image"])
    similar_products = get_similar_products(df, product)
    
    # Создаем модальное окно
    st.markdown(
        """
        <style>
        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        }
        .modal-content {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 15px;
            z-index: 1000;
            max-width: 90%;
            max-height: 90%;
            overflow-y: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Фон модального окна
    st.markdown('<div class="modal-backdrop" onclick="window.parent.document.dispatchEvent(new CustomEvent(\'closeModal\'))"></div>', unsafe_allow_html=True)
    
    # Содержимое модального окна
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Галерея изображений
            st.markdown("### 📷 Галерея")
            current_image = all_images[st.session_state.current_image_index]
            current_image_base64 = get_image_base64(current_image)
            
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <img src="data:image/jpeg;base64,{current_image_base64}" 
                         style='width:100%; border-radius:12px; max-height:400px; object-fit:contain;'>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Навигация по изображениям
            if len(all_images) > 1:
                col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
                with col_nav1:
                    if st.button("⬅️ Назад", use_container_width=True):
                        prev_image()
                with col_nav2:
                    st.markdown(f"<div style='text-align: center; padding: 10px;'>{st.session_state.current_image_index + 1} / {len(all_images)}</div>", unsafe_allow_html=True)
                with col_nav3:
                    if st.button("Вперед ➡️", use_container_width=True):
                        next_image()
                
                # Миниатюры
                st.markdown("#### Миниатюры:")
                thumb_cols = st.columns(min(5, len(all_images)))
                for idx, (thumb_col, img_path) in enumerate(zip(thumb_cols, all_images)):
                    with thumb_col:
                        thumb_base64 = get_image_base64(img_path)
                        st.markdown(
                            f"""
                            <div style="border: {'2px solid #007bff' if idx == st.session_state.current_image_index else '1px solid #ddd'}; 
                                        border-radius:8px; padding:2px; cursor:pointer;"
                                 onclick="window.parent.document.dispatchEvent(new CustomEvent('changeImage', {{detail: {idx}}}))">
                                <img src="data:image/jpeg;base64,{thumb_base64}" 
                                     style='width:100%; border-radius:6px; height:60px; object-fit:cover;'>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if st.button("Выбрать", key=f"thumb_{idx}", use_container_width=True):
                            st.session_state.current_image_index = idx
        
        with col2:
            # Информация о товаре
            st.markdown("### 📋 Информация о товаре")
            st.markdown(f"**Бренд:** {product['brand']}")
            st.markdown(f"**Модель:** {product['model_clean']}")
            st.markdown(f"**Цвет:** {product['color']}")
            st.markdown(f"**Размер US:** {product['size_us'] or '-'}")
            st.markdown(f"**Размер EU:** {product['size_eu'] or '-'}")
            st.markdown(f"**Пол:** {product['gender']}")
            st.markdown(f"**Описание:** {product['description']}")
            st.markdown(f"**Цена:** **{int(product['price'])} ₸**")
            
            # Другие цвета
            if not similar_products.empty:
                st.markdown("### 🎨 Другие цвета")
                for _, similar in similar_products.iterrows():
                    similar_image = get_image_path(similar["image"])
                    similar_base64 = get_image_base64(similar_image)
                    
                    col_sim1, col_sim2 = st.columns([1, 3])
                    with col_sim1:
                        st.markdown(
                            f"""
                            <img src="data:image/jpeg;base64,{similar_base64}" 
                                 style='width:100%; border-radius:8px; height:60px; object-fit:cover;'>
                            """,
                            unsafe_allow_html=True
                        )
                    with col_sim2:
                        st.markdown(f"**Цвет:** {similar['color']}")
                        st.markdown(f"**Цена:** {int(similar['price'])} ₸")
                        if st.button("Выбрать", key=f"similar_{similar['sku']}", use_container_width=True):
                            open_product_modal(similar.to_dict())
        
        # Кнопка закрытия
        st.markdown("---")
        if st.button("✖️ Закрыть", use_container_width=True):
            close_modal()

# --- JavaScript для обработки кликов ---
st.markdown(
    """
    <script>
    window.addEventListener('load', function() {
        // Обработка клика по карточке товара
        window.parent.document.addEventListener('productClick', function(e) {
            const product = e.detail;
            // Здесь можно отправить данные в Streamlit
            console.log('Product clicked:', product);
        });
        
        // Обработка закрытия модального окна
        window.parent.document.addEventListener('closeModal', function() {
            // Здесь можно вызвать функцию закрытия в Streamlit
            console.log('Close modal');
        });
        
        // Обработка смены изображения
        window.parent.document.addEventListener('changeImage', function(e) {
            const index = e.detail;
            // Здесь можно обновить индекс изображения
            console.log('Change image to:', index);
        });
    });
    </script>
    """,
    unsafe_allow_html=True
)

st.divider()
st.caption("© DENE Store 2025")