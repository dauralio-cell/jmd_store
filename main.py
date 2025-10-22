import streamlit as st
import pandas as pd
import os
from PIL import Image
import base64
from io import BytesIO

st.set_page_config(page_title="JMD Store", layout="wide")

# ---------- Загрузка Excel ----------
@st.cache_data
def load_data():
    excel_path = os.path.join("data", "catalog.xlsx")
    xls = pd.ExcelFile(excel_path)

    all_data = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["brand"] = df.get("brand", sheet)
        all_data.append(df)

    df = pd.concat(all_data, ignore_index=True)
    df = df.fillna("")

    # Приводим названия колонок к нижнему регистру
    df.columns = df.columns.str.strip().str.lower()

    # Переименуем нужные колонки
    rename_map = {
        "sku": "sku",
        "brand": "brand",
        "model": "model",
        "gender": "gender",
        "color": "color",
        "image": "image",
        "images": "image",
        "size us": "size_us",
        "size eu": "size_eu",
        "price": "price",
        "prices": "price"
    }
    df = df.rename(columns=rename_map)
    return df

df = load_data()

# Проверим нужные поля
for col in ["sku", "brand", "model", "gender", "color", "image", "size_us", "size_eu", "price"]:
    if col not in df.columns:
        df[col] = ""

# Очистим названия моделей
df["model_clean"] = df["model"].str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()

# ---------- Фильтры ----------
st.sidebar.header("Фильтр")

brand_filter = st.sidebar.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
gender_filter = st.sidebar.selectbox("Пол", ["Все"] + sorted([g for g in df["gender"].unique() if g]))
model_filter = st.sidebar.selectbox("Модель", ["Все"] + sorted(df["model_clean"].unique().tolist()))
color_filter = st.sidebar.selectbox("Цвет", ["Все"] + sorted([c for c in df["color"].unique() if c]))

# Соберём все размеры
all_sizes = sorted({
    s.strip() for sub in df["size_eu"].astype(str).str.split(',')
    for s in sub if s.strip()
})
size_filter = st.sidebar.selectbox("Размер (EU)", ["Все"] + all_sizes)

filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
if color_filter != "Все":
    filtered_df = filtered_df[filtered_df["color"] == color_filter]
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df["size_eu"].astype(str).str.contains(size_filter)]

# ---------- Группировка ----------
grouped = filtered_df.groupby(["brand", "model_clean", "color"], dropna=False)
IMAGE_DIR = "data/images"

# ---------- Конвертация изображения ----------
def image_to_base64(image_path):
    try:
        img = Image.open(image_path)
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode()
    except:
        return None

# ---------- Каталог карточек ----------
st.markdown("<h2 style='text-align:center;margin-bottom:30px;'>Каталог товаров</h2>", unsafe_allow_html=True)
cols = st.columns(3)
col_index = 0

for (brand, model, color), group in grouped:
    sku = group["sku"].iloc[0]
    sizes_eu = ", ".join(sorted({s.strip() for sub in group["size_eu"].astype(str).str.split(',') for s in sub if s.strip()}))
    sizes_us = ", ".join(sorted({s.strip() for sub in group["size_us"].astype(str).str.split(',') for s in sub if s.strip()}))
    price = ", ".join(sorted({str(p) for p in group["price"].astype(str).unique() if p != ""}))
    images = [i.strip() for i in group["image"].astype(str).unique() if i.strip()]

    found_images = []
    for img_name in images:
        for root, dirs, files in os.walk(IMAGE_DIR):
            for f in files:
                if f.lower().startswith(img_name.lower().split('.')[0]):
                    found_images.append(os.path.join(root, f))
    if not found_images:
        found_images = ["data/images/no_image.jpg"]

    # Слайдер
    if "slider_index" not in st.session_state:
        st.session_state.slider_index = {}
    key_base = f"{sku}_{brand}_{model}_{color}"
    if key_base not in st.session_state.slider_index:
        st.session_state.slider_index[key_base] = 0

    img_index = st.session_state.slider_index[key_base]
    image_path = found_images[img_index % len(found_images)]
    img_b64 = image_to_base64(image_path)

    # ---------- Карточка ----------
    with cols[col_index]:
        st.markdown(
            f"""
            <div style='border:1px solid #ddd;border-radius:10px;padding:10px;margin-bottom:25px;text-align:center;position:relative;overflow:hidden;'>
                <div style="position:relative;">
                    <img src='data:image/jpeg;base64,{img_b64}' style='width:100%;border-radius:10px;object-fit:cover;height:220px;'>
                    <button style="position:absolute;left:5px;top:50%;transform:translateY(-50%);background:none;border:none;color:black;font-size:22px;cursor:pointer;" onclick="window.location.reload()">◀</button>
                    <button style="position:absolute;right:5px;top:50%;transform:translateY(-50%);background:none;border:none;color:black;font-size:22px;cursor:pointer;" onclick="window.location.reload()">▶</button>
                </div>
                <h4 style="margin:10px 0 4px 0;">{brand} {model}</h4>
                <p style="color:gray;font-size:13px;margin:0;">{color}</p>
                <p style="font-size:14px;color:#555;">Размеры (EU): {sizes_eu}</p>
                <p style="font-size:13px;color:#555;">Размеры (US): {sizes_us}</p>
                <p style="font-weight:bold;font-size:16px;margin-top:6px;">{price if price else 'Цена уточняется'} ₸</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_index = (col_index + 1) % 3
