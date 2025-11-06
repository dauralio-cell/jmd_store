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

# --- Функции для изображений ---
def get_image_path(image_names, images_path="data/images"):
    """Ищет изображение по имени из колонки image"""
    if (image_names is pd.NA or 
        pd.isna(image_names) or 
        not image_names or 
        str(image_names).strip() == ""):
        return os.path.join(images_path, "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(images_path, "no_image.jpg")
    
    first_image_name = image_names_list[0]
    
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(images_path, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        
        pattern_start = os.path.join(images_path, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    return os.path.join(images_path, "no_image.jpg")

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
def get_eu_sizes(us_sizes_str):
    """Конвертирует US размеры в EU размеры"""
    if not us_sizes_str or us_sizes_str == "":
        return ""
    
    us_sizes = [size.strip() for size in us_sizes_str.split(",")]
    eu_sizes = []
    
    for us_size in us_sizes:
        eu_size = size_conversion.get(us_size, "")
        if eu_size:
            eu_sizes.append(eu_size)
    
    return ", ".join(eu_sizes)

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

# --- Основная функция ---
def main():
    # Кнопка назад
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Назад к каталогу", use_container_width=True):
            st.switch_page("main.py")

    # Проверяем, есть ли выбранный товар
    if "product_data" not in st.session_state:
        st.error("Товар не найден. Вернитесь в каталог и выберите товар.")
        return

    product_data = st.session_state.product_data
    df = load_data()

    # Получаем все варианты той же модели
    same_model_df = df[
        (df["model_clean"] == product_data["model_clean"]) & 
        (df["brand"] == product_data["brand"])
    ]

    if same_model_df.empty:
        st.error("Данные о товаре не найдены в каталоге")
        return

    # Группируем по цветам (как в главной странице)
    grouped_by_color = same_model_df.groupby(['brand', 'model_clean', 'color']).first().reset_index()
    
    # Группируем размеры отдельно
    size_groups = same_model_df.groupby(['brand', 'model_clean', 'color'])['size US'].agg(
        lambda x: ', '.join(sort_sizes(set(str(i).strip() for i in x if str(i).strip())))
    ).reset_index()
    
    # Объединяем
    grouped_by_color = grouped_by_color.merge(size_groups, on=['brand', 'model_clean', 'color'], suffixes=('', '_grouped'))
    grouped_by_color['size US'] = grouped_by_color['size US_grouped']
    grouped_by_color = grouped_by_color.drop('size US_grouped', axis=1)

    # Добавляем EU размеры после группировки
    grouped_by_color['size_eu'] = grouped_by_color['size US'].apply(get_eu_sizes)

    # Текущий выбранный цвет
    current_color = product_data["color"]
    current_item = grouped_by_color[grouped_by_color["color"] == current_color].iloc[0]

    # Заголовок
    st.markdown(f"<h1 style='margin-bottom: 10px;'>{current_item['brand']} {current_item['model_clean']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #666; margin-bottom: 30px;'>Цвет: {current_color.capitalize()}</h3>", unsafe_allow_html=True)

    # --- Горизонтальная галерея изображений ---
    all_images = []
    if current_item["image"]:
        image_names_list = str(current_item["image"]).strip().split()
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
            st.markdown(f"**Бренд:** {current_item['brand']}")
            st.markdown(f"**Модель:** {current_item['model_clean']}")
            st.markdown(f"**Цвет:** {current_color.capitalize()}")
            
        with info_col2:
            st.markdown(f"**Пол:** {current_item['gender']}")
            st.markdown(f"**Цена:** {int(current_item['price'])} ₸")
        
        # Описание
        st.markdown("### Описание")
        if current_item["description"] and str(current_item["description"]).strip():
            st.markdown(f"{current_item['description']}")
        else:
            st.markdown("Описание временно недоступно")

    with col_right:
        # --- Доступные размеры ---
        st.markdown("### Доступные размеры")
        
        if current_item["size US"]:
            us_sizes = [size.strip() for size in current_item["size US"].split(",")]
            eu_sizes = [size.strip() for size in current_item["size_eu"].split(",")] if current_item["size_eu"] else []
            
            # Сетка размеров 3 колонки
            cols = st.columns(3)
            for idx, us_size in enumerate(us_sizes):
                with cols[idx % 3]:
                    eu_size = eu_sizes[idx] if idx < len(eu_sizes) else ""
                    st.markdown(
                        f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 6px;
                            padding: 8px;
                            text-align: center;
                            margin: 4px;
                            background-color: #f8f9fa;
                            font-size: 12px;
                        ">
                            <div style="font-weight: bold;">US {us_size}</div>
                            <div style="color: #666;">EU {eu_size}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("Размеры для этого цвета не указаны")

        # --- Другие цвета ---
        other_colors = grouped_by_color[grouped_by_color["color"] != current_color]
        if not other_colors.empty:
            st.markdown("### Другие цвета")
            
            # Сетка цветов 2 колонки
            color_cols = st.columns(2)
            for idx, (_, variant) in enumerate(other_colors.iterrows()):
                with color_cols[idx % 2]:
                    # Показываем уменьшенное изображение для цвета
                    img_path = get_image_path(variant["image"])
                    image_base64 = get_image_base64(img_path)
                    
                    # Карточка цвета
                    st.markdown(
                        f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 8px;
                            padding: 6px;
                            text-align: center;
                            margin-bottom: 8px;
                            background-color: white;
                        ">
                            <img src="data:image/jpeg;base64,{image_base64}" 
                                 style="width:100%; border-radius:4px; height:80px; object-fit:cover;">
                            <div style="margin-top:6px; font-weight:bold; font-size:12px;">{variant['color'].capitalize()}</div>
                            <div style="font-size:11px; color:#666;">{int(variant['price'])} ₸</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Кнопка переключения на этот цвет
                    if st.button(f"Выбрать", key=f"color_{variant['color']}", use_container_width=True):
                        st.session_state.product_data = dict(variant)
                        st.rerun()

    # --- Информация о доставке и возврате ---
    st.markdown("---")
    st.markdown("### Информация о доставке")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Доставка**")
        st.markdown("По городу: 2-3 дня")
        st.markdown("По стране: 5-7 дней")
    with col2:
        st.markdown("**Возврат**")
        st.markdown("14 дней с момента получения")
        st.markdown("Товар в оригинальном состоянии")
    with col3:
        st.markdown("**Контакты**")
        st.markdown("+7 777 123 45 67")
        st.markdown("info@denestore.kz")

if __name__ == "__main__":
    main()