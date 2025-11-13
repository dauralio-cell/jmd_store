import streamlit as st
import pandas as pd
import glob
import os
import re
import base64

# --- Настройки страницы ---
st.set_page_config(page_title="Детали товара - DENE Store", layout="wide")

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Функция округления цены ---
def round_price(price):
    """Округляет цену до тысяч"""
    try:
        return round(float(price) / 1000) * 1000
    except:
        return price

# --- Функции для изображений ---
def get_image_path(image_names):
    """Ищет изображение по имени из колонки image"""
    if (image_names is pd.NA or 
        pd.isna(image_names) or 
        not image_names or 
        str(image_names).strip() == ""):
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        return fallback
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        return fallback
    
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
    fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
    return fallback

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        with open(fallback, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

# --- Таблица конверсии размеров US ↔ EU ---
size_conversion = {
    "1": "34", "2": "35", "3": "36", "4": "37", "5": "38",
    "6": "39", "7": "40", "8": "41", "9": "42", "10": "43",
    "11": "44", "12": "45", "13": "46"
}

# --- Функция для получения EU размеров ---
def get_eu_size(us_size):
    """Конвертирует один US размер в EU размер"""
    if not us_size or us_size == "":
        return ""
    return size_conversion.get(str(us_size).strip(), "")

# --- Функция сортировки размеров ---
def sort_sizes(size_list):
    """Сортирует размеры правильно: числа по значению, строки по алфавиту"""
    numeric_sizes = []
    string_sizes = []
    
    for size in size_list:
        clean_size = str(size).strip()
        if clean_size.replace('.', '').isdigit():
            numeric_sizes.append(float(clean_size))
        else:
            string_sizes.append(clean_size)
    
    numeric_sizes.sort()
    string_sizes.sort()
    
    return [str(int(x) if x.is_integer() else x) for x in numeric_sizes] + string_sizes

# --- Функция для нормализации дробных размеров ---
def normalize_size(size_str):
    """Приводит дробные размеры к ближайшему целому"""
    if not size_str or pd.isna(size_str):
        return ""
    
    size_str = str(size_str).strip()
    
    # Обрабатываем дробные размеры типа "42 1/3"
    if '/' in size_str:
        # Разделяем целую и дробную части
        parts = size_str.split()
        if len(parts) == 2 and '/' in parts[1]:
            try:
                whole_part = float(parts[0])
                fraction_part = parts[1]
                # Преобразуем дробь в десятичное число
                if fraction_part == '1/3':
                    return str(int(whole_part))  # 42 1/3 -> 42
                elif fraction_part == '2/3':
                    return str(int(whole_part) + 1)  # 42 2/3 -> 43
            except:
                return size_str
    
    # Обрабатываем десятичные дроби
    try:
        size_float = float(size_str)
        return str(int(round(size_float)))
    except:
        return size_str

# --- Загрузка данных (согласованная с главной страницей) ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
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

# --- Функция для добавления в корзину ---
def add_to_cart(product_data, selected_size=None, selected_price=None):
    """Добавляет товар в корзину"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    # ОКРУГЛЯЕМ ЦЕНУ ДО ТЫСЯЧ
    rounded_price = round_price(selected_price if selected_price else product_data['price'])
    
    cart_item = {
        'brand': product_data['brand'],
        'model': product_data['model_clean'],
        'color': product_data['color'],
        'price': rounded_price,
        'size': selected_size,
        'image': product_data['image']
    }
    
    st.session_state.cart.append(cart_item)
    st.success(f"Товар добавлен в корзину!")

# --- Основная функция ---
def main():
    # Кнопка назад
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Назад к каталогу", use_container_width=True):
            st.switch_page("main.py")
    with col3:
        cart_count = len(st.session_state.cart) if 'cart' in st.session_state else 0
        cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
        if st.button(cart_text, use_container_width=True):
            st.switch_page("pages/3_Корзина.py")

    # Проверяем, есть ли выбранный товар
    if "product_data" not in st.session_state:
        st.error("Товар не найден. Вернитесь в каталог и выберите товар.")
        return

    product_data = st.session_state.product_data
    df = load_data()

    # Получаем все варианты той же модели и цвета
    same_model_color_df = df[
        (df["model_clean"] == product_data["model_clean"]) & 
        (df["brand"] == product_data["brand"]) &
        (df["color"] == product_data["color"])
    ]

    if same_model_color_df.empty:
        st.error("Данные о товаре не найдены в каталоге")
        return

    # Получаем ВСЕ размеры для этого цвета с их ценами и наличием
    available_sizes = []
    for _, row in same_model_color_df.iterrows():
        us_size = str(row['size US']).strip()
        # Проверяем наличие товара (in stock)
        in_stock = str(row.get('in stock', 'yes')).strip().lower() if pd.notna(row.get('in stock')) else 'yes'
        
        # ПОКАЗЫВАЕМ ВСЕ РАЗМЕРЫ В НАЛИЧИИ (не только 5-11)
        if us_size and us_size != "nan" and in_stock == 'yes':
            # ОКРУГЛЯЕМ ЦЕНУ ДО ТЫСЯЧ
            rounded_price = round_price(row['price'])
            
            available_sizes.append({
                'us_size': us_size,
                'eu_size': get_eu_size(us_size),
                'price': rounded_price,
                'in_stock': in_stock
            })

    # Сортируем размеры
    sorted_sizes = sorted(available_sizes, key=lambda x: float(x['us_size']) if x['us_size'].replace('.', '').isdigit() else x['us_size'])

    # Получаем все цвета этой модели для переключения (только те, у которых есть размеры в наличии)
    all_colors_df = df[
        (df["model_clean"] == product_data["model_clean"]) & 
        (df["brand"] == product_data["brand"])
    ]
    
    # Фильтруем цвета: оставляем только те, у которых есть хотя бы один размер в наличии
    colors_with_stock = []
    for color in all_colors_df['color'].unique():
        color_sizes = df[
            (df["model_clean"] == product_data["model_clean"]) & 
            (df["brand"] == product_data["brand"]) &
            (df["color"] == color)
        ]
        # Проверяем есть ли размеры в наличии для этого цвета
        has_stock = any(
            str(row.get('in stock', 'yes')).strip().lower() == 'yes' 
            for _, row in color_sizes.iterrows() 
            if str(row['size US']).strip() and str(row['size US']).strip() != "nan"
        )
        if has_stock:
            colors_with_stock.append(color)
    
    unique_colors = all_colors_df[all_colors_df['color'].isin(colors_with_stock)].groupby('color').first().reset_index()

    # Текущий выбранный цвет
    current_color = product_data["color"]
    current_color_data = unique_colors[unique_colors["color"] == current_color].iloc[0]

    # Заголовок
    st.markdown(f"<h1 style='margin-bottom: 10px;'>{current_color_data['brand']} {current_color_data['model_clean']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #666; margin-bottom: 30px;'>Цвет: {current_color.capitalize()}</h3>", unsafe_allow_html=True)

    # --- Горизонтальная галерея изображений ---
    all_images = []
    if current_color_data["image"]:
        image_names_list = str(current_color_data["image"]).strip().split()
        for img_name in image_names_list:
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                pattern = os.path.join(IMAGES_PATH, "**", f"{img_name}*{ext}")
                files = glob.glob(pattern, recursive=True)
                all_images.extend(files)

    all_images = list(dict.fromkeys(all_images))
    if not all_images:
        all_images = [os.path.join(IMAGES_PATH, "no_image.jpg")]

    # Показываем изображения горизонтально
    if len(all_images) > 0:
        cols = st.columns(len(all_images))
        for idx, (col, img_path) in enumerate(zip(cols, all_images)):
            with col:
                image_base64 = get_image_base64(img_path)
                st.markdown(
                    f'<img src="data:image/jpeg;base64,{image_base64}" '
                    f'style="width:100%; border-radius:12px; border:1px solid #eee;">',
                    unsafe_allow_html=True
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Основная информация и размеры ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Информация о товаре
        st.markdown("### Информация о товаре")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"**Бренд:** {current_color_data['brand']}")
            st.markdown(f"**Модель:** {current_color_data['model_clean']}")
            st.markdown(f"**Цвет:** {current_color.capitalize()}")
            
        with info_col2:
            st.markdown(f"**Пол:** {current_color_data['gender']}")
            # Показываем диапазон цен если есть разные цены
            if sorted_sizes:
                prices = [size['price'] for size in sorted_sizes]
                min_price = min(prices)
                max_price = max(prices)
                if min_price == max_price:
                    st.markdown(f"**Цена:** {int(min_price):,} ₸".replace(",", " "))
                else:
                    st.markdown(f"**Цена:** {int(min_price):,} - {int(max_price):,} ₸".replace(",", " "))
            else:
                st.markdown("**Нет в наличии**")
        
        # Описание
        st.markdown("### Описание")
        if current_color_data.get("description") and str(current_color_data["description"]).strip():
            st.markdown(f"{current_color_data['description']}")
        else:
            st.markdown("Описание временно недоступно")

    with col_right:
        # --- Доступные размеры с ценами ---
        st.markdown("### Доступные размеры")
        
        if sorted_sizes:
            # Инициализируем выбранный размер в session_state
            if 'selected_size' not in st.session_state:
                st.session_state.selected_size = None
            if 'selected_price' not in st.session_state:
                st.session_state.selected_price = None
            
            # Сетка размеров 2 колонки с ценами
            cols = st.columns(2)
            selected_size = st.session_state.selected_size
            
            for idx, size_data in enumerate(sorted_sizes):
                with cols[idx % 2]:
                    us_size = size_data['us_size']
                    eu_size = size_data['eu_size']
                    price = size_data['price']
                    
                    is_selected = selected_size == us_size
                    
                    # Кнопка с размером и ценой
                    button_text = f"US {us_size}"
                    if eu_size:
                        button_text += f"\nEU {eu_size}"
                    button_text += f"\n{int(price):,} ₸".replace(",", " ")
                    
                    if st.button(button_text, 
                                key=f"size_{us_size}",
                                use_container_width=True,
                                type="primary" if is_selected else "secondary"):
                        st.session_state.selected_size = us_size
                        st.session_state.selected_price = price
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Кнопка добавления в корзину
            if st.session_state.selected_size:
                selected_price = st.session_state.selected_price
                button_text = f"Добавить в корзину - {int(selected_price):,} ₸".replace(",", " ")
                if st.button(button_text, type="primary", use_container_width=True):
                    add_to_cart(current_color_data, st.session_state.selected_size, selected_price)
            else:
                st.button("Выберите размер", disabled=True, use_container_width=True)
                
        else:
            st.warning("😔 Нет размеров в наличии")
            st.info("Выберите другой цвет или проверьте позже")

                # --- Другие цвета этой модели ---
        other_colors = unique_colors[unique_colors["color"] != current_color]
        if not other_colors.empty:
            st.markdown("### Другие цвета")
            
            # Сетка цветов 2 колонки
            color_cols = st.columns(2)
            for idx, (_, variant) in enumerate(other_colors.iterrows()):
                with color_cols[idx % 2]:
                    # Показываем уменьшенное изображение для цвета
                    img_path = get_image_path(variant["image"])
                    
                    # Получаем минимальную цену для этого цвета (только размеры в наличии)
                    color_sizes = df[
                        (df["model_clean"] == variant["model_clean"]) & 
                        (df["brand"] == variant["brand"]) &
                        (df["color"] == variant["color"])
                    ]
                    # Фильтруем только размеры в наличии
                    available_color_sizes = [
                        row for _, row in color_sizes.iterrows()
                        if str(row.get('in stock', 'yes')).strip().lower() == 'yes'
                        and str(row['size US']).strip() and str(row['size US']).strip() != "nan"
                    ]
                    
                    if available_color_sizes:
                        # ОКРУГЛЯЕМ ЦЕНУ ДО ТЫСЯЧ
                        min_color_price = min(round_price(row['price']) for row in available_color_sizes)
                        
                        # Используем встроенный Streamlit image вместо HTML
                        try:
                            st.image(img_path, use_column_width=True, caption=f"{variant['color'].capitalize()}")
                        except Exception as e:
                            st.error(f"Ошибка загрузки изображения: {e}")
                            fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
                            st.image(fallback, use_column_width=True, caption=f"{variant['color'].capitalize()}")
                        
                        st.markdown(f"**от {int(min_color_price):,} ₸**".replace(",", " "))
                        
                        # Кнопка переключения на этот цвет
                        if st.button(f"Выбрать", key=f"color_{variant['color']}", use_container_width=True):
                            st.session_state.selected_size = None  # Сбрасываем выбранный размер
                            st.session_state.selected_price = None
                            st.session_state.product_data = dict(variant)
                            st.rerun()

    # --- Информация о доставке и возврате ---
    st.markdown("---")
    st.markdown("### Информация о доставке")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Доставка**")
        st.markdown("Курьерская служба")
        st.markdown("10-21 день")
    with col2:
        st.markdown("**Возврат**")
        st.markdown("14 дней с момента получения")

if __name__ == "__main__":
    main()

# Добавьте в самый конец файла:
from components.documents import documents_footer
documents_footer()