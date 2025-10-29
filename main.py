import streamlit as st
import pandas as pd
import os
import glob
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
if os.path.exists("data/images/banner.jpg"):
    st.image("data/images/banner.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center;'>DENE Store — Каталог</h1>", unsafe_allow_html=True)
st.write("Добро пожаловать! Здесь вы можете подобрать кроссовки по бренду, модели, размеру и полу 👟")

# --- Загрузка данных ---
@st.cache_data
def load_data():
    df = pd.read_excel("data/catalog.xlsx")
    df = df.fillna("")
    return df

df = load_data()

# --- Сканирование изображений ---
image_files = glob.glob("data/images/**/*.*", recursive=True)
image_index = {}
for img_path in image_files:
    base = os.path.splitext(os.path.basename(img_path))[0].lower()
    image_index[base] = img_path

# --- Панель фильтров ---
with st.expander("🔎 Фильтр товаров", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        brand_filter = st.selectbox("Бренд", ["Все"] + sorted(df["brand"].dropna().unique().tolist()))
    with col2:
        model_filter = st.selectbox("Модель", ["Все"] + sorted(df["model"].dropna().unique().tolist()))
    with col3:
        size_filter = st.selectbox("Размер", ["Все"] + sorted(df["size"].dropna().unique().tolist()))
    with col4:
        gender_filter = st.selectbox("Пол", ["Все"] + sorted(df["gender"].dropna().unique().tolist()))

search_query = st.text_input("🔍 Поиск по бренду или модели").strip().lower()

# --- Применяем фильтры ---
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model"] == model_filter]
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df["size"] == size_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if search_query:
    filtered_df = filtered_df[
        filtered_df["brand"].str.lower().str.contains(search_query) |
        filtered_df["model"].str.lower().str.contains(search_query)
    ]

# --- Вывод карточек товаров ---
if filtered_df.empty:
    st.warning("❌ Товары не найдены по вашему запросу.")
else:
    cols = st.columns(3)
    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        # --- Поиск картинки ---
        images = str(row.get("image", "")).split()
        found_image = None
        for name in images:
            key = name.strip().lower()
            if key in image_index:
                found_image = image_index[key]
                break
        if not found_image:
            found_image = "data/images/no_image.jpg"

        with cols[idx % 3]:
            st.image(found_image, use_container_width=True)
            st.markdown(
                f"""
                <div style="
                    border:1px solid #eee;
                    border-radius:16px;
                    padding:12px;
                    margin-top:8px;
                    background-color:#fff;
                    box-shadow:0 2px 8px rgba(0,0,0,0.05);
                    text-align:center;
                ">
                    <h4 style="margin:4px 0;">{row.get('brand','')} {row.get('model','')}</h4>
                    <p style="color:gray; font-size:13px; margin:2px 0;">{row.get('color','')} | {row.get('gender','')}</p>
                    <p style="font-weight:bold; color:#111; margin:4px 0;">{int(row.get('price',0))} ₸</p>
                    <p style="font-size:13px; color:{'green' if str(row.get('in stock', 'yes')).lower() in ['yes','в наличии','true'] else 'red'};">
                        {'В наличии' if str(row.get('in stock', 'yes')).lower() in ['yes','в наличии','true'] else 'Нет в наличии'}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
