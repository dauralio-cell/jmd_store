import streamlit as st
import pandas as pd
import os
import glob
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
banner_path = "data/images/banner.jpg"
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)
st.markdown("<h1 style='text-align:center;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Загрузка данных ---
df = pd.read_excel("data/catalog.xlsx")

# --- Очистка названий колонок ---
df.columns = df.columns.str.strip().str.lower()

# --- Проверим наличие ключевых колонок ---
required_columns = ["brand", "model", "gender", "size us", "price", "in stock", "image"]
for col in required_columns:
    if col not in df.columns:
        st.error(f"❌ В таблице нет колонки: '{col}'")
        st.stop()

# --- Фильтры ---
col1, col2, col3, col4 = st.columns(4)

brands = sorted(df["brand"].dropna().unique().tolist())
models = sorted(df["model"].dropna().unique().tolist())
genders = sorted(df["gender"].dropna().unique().tolist())
sizes = sorted(df["size us"].dropna().unique().tolist())

brand_filter = col1.selectbox("Бренд", ["Все"] + brands)
model_filter = col2.selectbox("Модель", ["Все"] + models)
gender_filter = col3.selectbox("Пол", ["Все"] + genders)
size_filter = col4.selectbox("Размер US", ["Все"] + sizes)

filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model"] == model_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df["size us"] == size_filter]

# --- Сканируем все изображения в data/images ---
image_paths = glob.glob("data/images/**/*.*", recursive=True)
image_map = {}
for path in image_paths:
    name = os.path.splitext(os.path.basename(path))[0]
    image_map[name] = path

# --- Вывод карточек ---
st.markdown("### Каталог товаров")
if filtered_df.empty:
    st.warning("😕 Нет товаров по заданным фильтрам.")
else:
    cols = st.columns(4)
    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        with cols[idx % 4]:
            images = str(row["image"]).split()
            found_images = []
            for img_name in images:
                if img_name in image_map:
                    found_images.append(image_map[img_name])
            
            if found_images:
                st.image(found_images[0], use_container_width=True)
            else:
                st.image("data/images/no_image.jpg", use_container_width=True)

            st.markdown(f"**{row['brand']} {row['model']}**")
            st.markdown(f"Размер: {row['size us']}")
            st.markdown(f"Цена: {int(row['price'])} ₸")

            color = "green" if str(row["in stock"]).strip().lower() == "yes" else "red"
            st.markdown(f"<p style='font-size:13px; color:{color};'>В наличии: {row['in stock']}</p>", unsafe_allow_html=True)
