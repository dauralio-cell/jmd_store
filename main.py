import os
import pandas as pd
import streamlit as st
import glob
import re

# === Настройки страницы ===
st.set_page_config(page_title="DENE Store", layout="wide")

# === Пути ===
CATALOG_PATH = os.path.join("data", "catalog.xlsx")
NO_IMAGE_PATH = os.path.join("data", "images", "no_image.jpg")

# === Обложка ===
st.image("data/images/banner.jpg", width="stretch")
st.markdown("<h1 style='text-align:center;'>👟 DENE Store — Добро пожаловать!</h1>", unsafe_allow_html=True)

# === Функция загрузки каталога ===
@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(CATALOG_PATH):
        st.error("❌ Файл каталога не найден.")
        return pd.DataFrame()

    df = pd.read_excel(CATALOG_PATH)
    df = df.fillna("")

    # Разбор модели и размера
    df["model_clean"] = df["model"].str.replace(r"\d{1,2}(\.\d)?", "", regex=True).str.strip()
    df["size"] = df["model"].str.extract(r"(\d{1,2}(\.\d)?)")[0]
    df["gender"] = df["model"].apply(lambda x: "men" if "men" in x.lower() else ("women" if "women" in x.lower() else "unisex"))
    df["color"] = df["model"].str.extract(r"(white|black|blue|red|green|pink|gray|brown)", expand=False).fillna("other")

    if "description" not in df.columns:
        df["description"] = "Описание временно недоступно."

    return df

df = load_data()

# === Фильтры ===
st.divider()
st.markdown("### 🔎 Фильтр каталога")

col1, col2, col3, col4, col5 = st.columns(5)
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
filtered_df = df if brand_filter == "Все" else df[df["brand"] == brand_filter]

models = sorted(filtered_df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + models)
size_filter = col3.selectbox("Размер", ["Все"] + sorted(df["size"].dropna().unique().tolist()))
gender_filter = col4.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col5.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()))

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

st.divider()
st.markdown("## 📦 Каталог товаров")

# === Функция поиска фото ===
def find_image(brand, model, sku):
    """
    Ищет фото по пути data/images/<brand>/<model>/<sku>*.jpg
    Если нет — возвращает no_image.jpg
    """
    brand_path = os.path.join("data", "images", brand)
    model_path = os.path.join(brand_path, model)
    search_pattern = os.path.join(model_path, f"{sku}*.jpg")
    matches = glob.glob(search_pattern)
    return matches[0] if matches else NO_IMAGE_PATH

# === Сетка карточек ===
num_cols = 4
rows = [filtered_df.iloc[i:i + num_cols] for i in range(0, len(filtered_df), num_cols)]

for row_df in rows:
    cols = st.columns(num_cols)
    for col, (_, row) in zip(cols, row_df.iterrows()):
        brand = str(row["brand"]).strip()
        model = str(row["model_clean"]).strip()
        sku = str(row["SKU"]).strip()
        price = str(row["price"]).strip()

        if not brand or not sku:
            continue  # Пропускаем пустые строки

        image_path = find_image(brand, model, sku)

        # Цена и описание
        price_html = f"<p style='font-weight:bold; font-size:16px; margin-top:6px;'>{int(price)} ₸</p>" if price.isdigit() else ""
        desc_html = f"<p style='font-size:13px; color:#555;'>{row['description']}</p>"

        col.markdown(f"""
        <div style="
            border:1px solid #eee;
            border-radius:16px;
            padding:12px;
            margin-bottom:16px;
            background-color:#fff;
            box-shadow:0 2px 10px rgba(0,0,0,0.05);
            transition:transform 0.2s ease-in-out;
        " onmouseover="this.style.transform='scale(1.02)';"
          onmouseout="this.style.transform='scale(1)';">
            <img src='{image_path}' style='width:100%; border-radius:12px; object-fit:cover; height:220px;'>
            <h4 style="margin:10px 0 4px 0;">{brand} {model}</h4>
            {desc_html}
            {price_html}
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption("© 2025 DENE Store")
