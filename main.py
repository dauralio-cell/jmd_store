import os
import pandas as pd
import streamlit as st
import glob

# 📁 Пути
CATALOG_PATH = os.path.join("data", "catalog.xlsx")
NO_IMAGE_PATH = os.path.join("data", "images", "no_image.jpg")

# 🔄 Загрузка каталога
def load_catalog():
    df = pd.read_excel(CATALOG_PATH)
    df.fillna('', inplace=True)

    # Проверяем нужные колонки
    for col in ['brand', 'model', 'SKU']:
        if col not in df.columns:
            df[col] = ''
    return df

catalog = load_catalog()

st.title("🛍 Каталог товаров")

# 🔍 Функция поиска фото
def find_image(brand, model, sku):
    brand_path = os.path.join("data", "images", brand)
    model_path = os.path.join(brand_path, model)
    search_pattern = os.path.join(model_path, f"{sku}*.jpg")
    matches = glob.glob(search_pattern)
    if matches:
        return matches[0]  # берем первое найденное фото
    return NO_IMAGE_PATH

# 🧩 Вывод карточек
for _, row in catalog.iterrows():
    brand = str(row['brand']).strip()
    model = str(row['model']).strip()
    sku = str(row['SKU']).strip()

    # --- Пропускаем если нет SKU ---
    if not sku:
        continue

    # --- Фото ---
    image_path = find_image(brand, model, sku)

    # --- Цена ---
    price = str(row.get('price', '')).strip()
    price_html = f"<p style='font-size:16px; color:gray; margin:2px 0;'>{int(price)} ₸</p>" if price.isdigit() else ""

    # --- Модель ---
    model_html = f"<p style='font-size:15px; color:#555; margin:2px 0;'>Модель: {model}</p>" if model else ""

    # --- Отображение карточки ---
    st.markdown(f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:12px; margin:10px 0; background:#fff;">
        <img src="{image_path}" style="width:100%; border-radius:8px; margin-bottom:6px;">
        <p style="font-weight:bold; font-size:18px;">{brand}</p>
        {model_html}
        {price_html}
    </div>
    """, unsafe_allow_html=True)
