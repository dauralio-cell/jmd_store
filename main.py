import streamlit as st
import pandas as pd
import os
import base64

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.xlsx")
NO_IMAGE_PATH = os.path.join(DATA_DIR, "images", "no_image.jpg")

# Загружаем Excel
@st.cache_data
def load_catalog():
    return pd.read_excel(CATALOG_PATH)

df = load_catalog()

# Настройки страницы
st.set_page_config(page_title="Каталог JMD Store", layout="wide")
st.markdown("""
    <style>
        .card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            margin-bottom: 20px;
            background: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
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

# Фильтр по бренду
brands = ["Все"] + sorted(df["brand"].dropna().unique().tolist())
selected_brand = st.selectbox("Выберите бренд", brands)
if selected_brand != "Все":
    df = df[df["brand"] == selected_brand]

# Сетка карточек
cols = st.columns(4)
col_idx = 0

for _, row in df.iterrows():
    # Пропускаем пустые цены
    if pd.isna(row.get("price")) or str(row["price"]).strip() == "":
        continue

    # Проверка пути изображения
    image_name = str(row.get("image", "")).strip()
    image_path = os.path.join(DATA_DIR, "images", image_name)
    if not image_name or not os.path.exists(image_path):
        image_path = NO_IMAGE_PATH

    # Конвертируем в base64
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    # Карточка товара
    with cols[col_idx]:
        st.markdown(
            f"""
            <div class="card">
                <img src="data:image/jpeg;base64,{img_base64}" alt="Фото">
                <p><b>{row.get('brand', '')}</b></p>
                <p>{row.get('model', '')}</p>
                <p>{int(row['price'])} ₸</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_idx = (col_idx + 1) % 4
