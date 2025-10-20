import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.xlsx")
NO_IMAGE_PATH = os.path.join(DATA_DIR, "images", "no_image.jpg")

# Кэшируем загрузку
@st.cache_data
def load_catalog():
    return pd.read_excel(CATALOG_PATH)

df = load_catalog()

# Стили
st.set_page_config(page_title="Каталог JMD Store", layout="wide")
st.markdown("""
    <style>
        .card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        .card img {
            width: 100%;
            height: auto;
            border-radius: 8px;
        }
        .card p {
            margin: 5px 0;
        }
    </style>
""", unsafe_allow_html=True)

# Фильтры
brands = ["Все"] + sorted(df["brand"].dropna().unique().tolist())
selected_brand = st.selectbox("Выберите бренд", brands)
if selected_brand != "Все":
    df = df[df["brand"] == selected_brand]

# Сетка карточек
cols = st.columns(4)
col_idx = 0

for _, row in df.iterrows():
    # если нет цены — пропускаем
    if pd.isna(row.get("price")) or str(row["price"]).strip() == "":
        continue

    image_path = os.path.join(DATA_DIR, "images", str(row.get("image", ""))).replace("\\", "/")

    # если нет фото — вставляем no_image.jpg
    if not os.path.exists(image_path) or not str(row.get("image", "")).strip():
        image_path = NO_IMAGE_PATH

    # карточка
    with cols[col_idx]:
        st.markdown(
            f"""
            <div class="card">
                <img src="data:image/jpeg;base64,{open(image_path, 'rb').read().encode('base64').decode()}" alt="Фото">
                <p><b>{row.get('brand', '')}</b></p>
                <p>{row.get('model', '')}</p>
                <p>{int(row['price'])} ₸</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_idx = (col_idx + 1) % 4
