# product_detail.py
import streamlit as st
import pandas as pd
import glob
import os
import re
import base64

# --- Настройки страницы ---
st.set_page_config(page_title="Детали товара - DENE Store", layout="wide")

# --- Функции для работы с изображениями ---
def get_image_path(image_names, images_path="data/images"):
    """Ищет изображение по имени из колонки image"""
    if not image_names or pd.isna(image_names) or str(image_names).strip() == "":
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

# --- Загрузка данных ---
@st.cache_data(show_spinner=False)
def load_data():
    catalog_path = "data/catalog.xlsx"
    all_sheets = pd.read_excel(catalog_path, sheet_name=None)
    df_list = []
    for sheet_data in all_sheets.values():
        df_list.append(sheet_data)
    df = pd.concat(df_list, ignore_index=True)
    df = df.fillna("")
    
    # Та же обработка данных что и в основном файле
    df["model_clean"] = df["model"].str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True).str.strip()
    # ... остальная обработка такая же как в основном файле
    
    return df

# --- Основная логика страницы деталей ---
def main():
    st.title("Детальная информация о товаре")
    
    # Получаем параметры из URL
    query_params = st.experimental_get_query_params()
    product_param = query_params.get("product", [""])[0]
    
    if not product_param:
        st.error("Товар не найден")
        st.stop()
    
    # Загружаем данные
    df = load_data()
    
    # Ищем товар (упрощенная логика - в реальности нужно парсить product_param)
    # Для демонстрации покажем первый товар
    if len(df) > 0:
        product = df.iloc[0]  # В реальности ищем по product_param
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Все изображения товара
            all_images = []
            if product["image"]:
                image_names_list = str(product["image"]).strip().split()
                for img_name in image_names_list:
                    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        pattern = os.path.join("data/images", "**", f"{img_name}*{ext}")
                        files = glob.glob(pattern, recursive=True)
                        all_images.extend(files)
            
            all_images = list(dict.fromkeys(all_images))
            
            if not all_images:
                all_images = [os.path.join("data/images", "no_image.jpg")]
            
            # Показываем все изображения
            for img_path in all_images:
                try:
                    st.image(img_path, use_column_width=True)
                except Exception as e:
                    st.error(f"Ошибка загрузки изображения: {e}")
        
        with col2:
            st.markdown(f"# {product['brand']} {product['model_clean']}")
            st.markdown(f"**Цена:** {int(product['price'])} ₸")
            st.markdown(f"**Размеры:** US {product['size_us'] or '-'} | EU {product['size_eu'] or '-'}")
            st.markdown(f"**Пол:** {product['gender']}")
            st.markdown(f"**Цвет:** {product['color']}")
            st.markdown(f"**Описание:** {product['description']}")
            
            # Кнопка назад
            if st.button("← Назад к каталогу"):
                st.switch_page("main_app.py")
    
    else:
        st.error("Товар не найден")

if __name__ == "__main__":
    main()