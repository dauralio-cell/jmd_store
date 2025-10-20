import streamlit as st
import pandas as pd
import os
import base64

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_DIR = "data/images"

# --- Кэш загрузки каталога ---
@st.cache_data
def load_data():
    df = pd.read_excel(CATALOG_PATH)
    return df

# --- Поиск изображения по SKU ---
def find_image(sku):
    for root, _, files in os.walk(IMAGES_DIR):
        for file in files:
            filename, ext = os.path.splitext(file)
            if ext.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                if filename.startswith(str(sku)):
                    return os.path.join(root, file)
    # Если ничего не найдено — вернуть no_image
    return os.path.join(IMAGES_DIR, "no_image.jpg")

# --- Настройки страницы ---
st.set_page_config(page_title="JMD Store", layout="wide")

# --- Обложка ---
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 40px;'>
        <h1 style='font-size:48px; font-weight:700;'>JMD Store</h1>
        <p style='font-size:18px; color:#666;'>Каталог кроссовок Mizuno и других брендов</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Загрузка данных ---
df = load_data()

# --- Фильтры ---
brands = sorted(df["brand"].dropna().unique())
selected_brand = st.selectbox("Бренд", ["Все"] + list(brands))

sizes_us = sorted(df["size_us"].dropna().unique()) if "size_us" in df.columns else []
sizes_eu = sorted(df["size_eu"].dropna().unique()) if "size_eu" in df.columns else []

col1, col2 = st.columns(2)
with col1:
    selected_us = st.selectbox("US размер", ["Все"] + [str(s) for s in sizes_us])
with col2:
    selected_eu = st.selectbox("EU размер", ["Все"] + [str(s) for s in sizes_eu])

# --- Применение фильтров ---
filtered_df = df.copy()
if selected_brand != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == selected_brand]
if selected_us != "Все" and "size_us" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["size_us"].astype(str) == selected_us]
if selected_eu != "Все" and "size_eu" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["size_eu"].astype(str) == selected_eu]

# --- Отображение карточек товаров ---
st.markdown("<div style='display: flex; flex-wrap: wrap; gap: 20px;'>", unsafe_allow_html=True)

for _, row in filtered_df.iterrows():
    price = row.get("price", "")
    model = row.get("model", "")
    brand = row.get("brand", "")
    sku = row.get("sku", "")

    if pd.isna(price) or str(price).strip() == "":
        continue  # пропускаем товары без цены

    image_path = find_image(sku)

    # Кодирование фото
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style='width: 220px; border-radius: 15px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
            <img src="data:image/jpeg;base64,{img_data}" style='width:100%; height:180px; object-fit:cover;'>
            <div style='padding:10px; text-align:center;'>
                <h4 style='margin:5px 0; font-size:16px;'>{brand}</h4>
                <p style='margin:0; color:#555;'>{model}</p>
                <p style='font-weight:bold; margin-top:5px;'>{int(price)} ₸</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)
