import os
import pandas as pd
import streamlit as st

# 📁 Путь к каталогу
CATALOG_PATH = os.path.join("data", "catalog.xlsx")

# 🔄 Функция загрузки каталога
def load_catalog():
    df = pd.read_excel(CATALOG_PATH)
    df.fillna('', inplace=True)
    return df

# Загружаем данные
catalog = load_catalog()

st.title("🛍 Каталог товаров")

# 🔍 Отображение карточек
for _, row in catalog.iterrows():
    # Проверка на пустую цену
    price_value = row['price']
    try:
        price_str = f"{int(price_value)} ₸" if str(price_value).strip() != '' else ""
    except ValueError:
        price_str = ""

    # Проверка на фото
    image_html = ""
    if str(row['image']).strip() != "":
        image_html = f'<img src="{row["image"]}" style="width:100%; border-radius:8px; margin-bottom:6px;">'

    # Вывод карточки
    st.markdown(f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:12px; margin:10px 0;">
        {image_html}
        <p style="font-weight:bold; font-size:18px;">{row['name']}</p>
        {'<p style="font-size:16px; color:gray;">' + price_str + '</p>' if price_str else ''}
    </div>
    """, unsafe_allow_html=True)