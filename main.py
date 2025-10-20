import os
import pandas as pd
import streamlit as st

# 📁 Пути к файлам
CATALOG_PATH = os.path.join("data", "catalog.xlsx")
NO_IMAGE_PATH = os.path.join("data", "no_image.jpg")

# Проверка, что файл-заглушка существует
if not os.path.exists(NO_IMAGE_PATH):
    st.error(f"Файл-заглушка 'no_image.jpg' не найден по пути: {NO_IMAGE_PATH}")
    st.stop() # Останавливаем приложение, так как нет файла-заглушки

# 🔄 Загрузка каталога
@st.cache_data # Добавим кэширование для скорости
def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        st.error(f"Файл каталога не найден: {CATALOG_PATH}")
        return pd.DataFrame()
    df = pd.read_excel(CATALOG_PATH)
    df.fillna('', inplace=True)
    return df

catalog = load_catalog()

st.title("🛍 Каталог товаров")

# 🧩 Вывод карточек
for _, row in catalog.iterrows():
    # --- Логика определения пути к изображению ---
    # 1. Получаем путь из Excel
    image_from_excel = str(row.get('image', '')).strip()
    
    # 2. Определяем путь для отображения
    # Проверяем, есть ли путь в Excel И существует ли файл по этому пути
    if image_from_excel and os.path.exists(image_from_excel):
        display_image_path = image_from_excel
    else:
        # Если пути нет или файл не найден, используем заглушку
        display_image_path = NO_IMAGE_PATH

    # --- Цена ---
    price = str(row.get('price', '')).strip()
    price_html = f"<p style='font-size:16px; color:gray; margin:2px 0;'>{int(price)} ₸</p>" if price.isdigit() else ""

    # --- Модель ---
    model = str(row.get('model', '')).strip()
    model_html = f"<p style='font-size:15px; color:#555; margin:2px 0;'>Модель: {model}</p>" if model else ""

    # --- Отображение карточки ---
    st.markdown(f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:12px; margin:10px 0;">
    """, unsafe_allow_html=True)
    
    # Используем st.image() вместо HTML-тега img
    st.image(display_image_path, use_column_width=True)
    
    st.markdown(f"""
        <p style="font-weight:bold; font-size:18px;">{row.get('name', '')}</p>
        {model_html}
        {price_html}
    </div>
    """, unsafe_allow_html=True)

