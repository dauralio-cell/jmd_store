import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
st.image("data/images/banner.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Загрузка данных ---
@st.cache_data
def load_data():
    df = pd.read_excel("data/catalog.xlsx")
    df = df.fillna("")
    
    # Чистим и разбиваем model
    df["model_clean"] = df["model"].str.replace(r"\d{1,2}(\.\d)?", "", regex=True).str.strip()
    df["size"] = df["model"].str.extract(r"(\d{1,2}(\.\d)?)")[0]
    df["gender"] = df["model"].apply(lambda x: "men" if "men" in x.lower() else ("women" if "women" in x.lower() else "unisex"))
    df["color"] = df["model"].str.extract(r"(white|black|blue|red|green|pink|gray|brown)", expand=False).fillna("other")
    return df

df = load_data()

# --- Фильтры ---
col1, col2, col3, col4, col5 = st.columns(5)
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
filtered_df = df if brand_filter == "Все" else df[df["brand"] == brand_filter]

# Модели по выбранному бренду
models = sorted(filtered_df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + models)

size_filter = col3.selectbox("Размер", ["Все"] + sorted(df["size"].dropna().unique().tolist()))
gender_filter = col4.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col5.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()))

# --- Применяем фильтры ---
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df["size"] == size_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if color_filter != "Все":
    filtered_df = filtered_df[filtered_df["color"] == color_filter]

# --- Показ товаров ---
for _, row in filtered_df.iterrows():
    st.markdown(f"### {row['brand']} — {row['model_clean']} ({row['size']})")
    
    # ищем все изображения по SKU
    image_files = glob.glob(f"data/images/{row['SKU']}*.jpg")

    if not image_files:
        image_files = ["data/images/no_image.jpg"]

    # создаем слайдер для переключения изображений
    if len(image_files) > 1:
        idx = st.slider(f"Фото {row['SKU']}", 0, len(image_files)-1, 0, label_visibility="collapsed")
        st.image(image_files[idx], use_container_width=True)
    else:
        st.image(image_files[0], use_container_width=True)
    
    st.write(f"💰 Цена: {int(row['price'])} ₸")
    st.button("🛒 Добавить в корзину", key=row["SKU"])
    st.divider()
