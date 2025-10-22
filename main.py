import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="JMD Store", layout="wide")

# ---------- Загрузка данных ----------
@st.cache_data
def load_data():
    excel_path = os.path.join("data", "catalog.xlsx")
    xls = pd.ExcelFile(excel_path)

    all_data = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df["brand"] = df["brand"].fillna(sheet_name)
        all_data.append(df)

    df = pd.concat(all_data, ignore_index=True)
    df = df.fillna("")
    return df

df = load_data()

# ---------- Очистка модели (удаляем артикул в скобках) ----------
df["model_clean"] = df["model"].str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()

# ---------- Фильтры ----------
st.sidebar.header("Фильтр")

brand_filter = st.sidebar.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
gender_filter = st.sidebar.selectbox("Пол", ["Все"] + sorted([g for g in df["gender"].unique() if g]))
model_filter = st.sidebar.selectbox("Модель", ["Все"] + sorted(df["model_clean"].unique().tolist()))
color_filter = st.sidebar.selectbox("Цвет", ["Все"] + sorted([c for c in df["color"].unique() if c]))
size_filter = st.sidebar.selectbox("Размер (EU)", ["Все"] + sorted({s for sub in df["sizes"].astype(str).str.split(',') for s in sub if s.strip()}))

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
    filtered_df = filtered_df[filtered_df["sizes"].astype(str).str.contains(size_filter)]

# ---------- Группировка карточек ----------
grouped = filtered_df.groupby(["brand", "model_clean", "color"], dropna=False)

# ---------- Папка с изображениями ----------
IMAGE_DIR = "images"

# ---------- Карточки товаров ----------
st.markdown("<h2 style='text-align:center;margin-bottom:30px;'>Каталог товаров</h2>", unsafe_allow_html=True)

cols = st.columns(3)
col_index = 0

for (brand, model, color), group in grouped:
    sku = group["sku"].iloc[0]
    sizes = ", ".join(sorted({s.strip() for sub in group["sizes"].astype(str).str.split(',') for s in sub if s.strip()}))
    prices = ", ".join(sorted({str(p) for p in group["prices"].astype(str).unique() if p != ""}))
    images = [i.strip() for i in group["image"].astype(str).unique() if i.strip()]

    # Проверка картинок
    found_images = []
    for img_name in images:
        for root, dirs, files in os.walk(IMAGE_DIR):
            for f in files:
                if f.lower().startswith(img_name.lower().split('.')[0]):
                    found_images.append(os.path.join(root, f))
    if not found_images:
        found_images = ["no_image.jpg"]

    # Слайдер
    if "slider_index" not in st.session_state:
        st.session_state.slider_index = {}
    key_base = f"{sku}_{brand}_{model}_{color}"
    if key_base not in st.session_state.slider_index:
        st.session_state.slider_index[key_base] = 0

    img_index = st.session_state.slider_index[key_base]
    image_path = found_images[img_index % len(found_images)]

    # Отрисовка карточки
    with cols[col_index]:
        st.markdown(
            f"""
            <div style='border:1px solid #ddd;border-radius:10px;padding:10px;margin-bottom:25px;text-align:center;'>
                <img src='data:image/png;base64,{Image.open(image_path).convert("RGB").tobytes().hex()}' style='width:100%;border-radius:10px;object-fit:cover;height:220px;'>
                <h4 style="margin:10px 0 4px 0;">{brand} {model}</h4>
                <p style="color:gray;font-size:13px;margin:0;">{color}</p>
                <p style="font-size:14px;color:#555;">Размеры (EU): {sizes}</p>
                <p style="font-weight:bold;font-size:16px;margin-top:6px;">{prices if prices else 'Цена уточняется'} ₸</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([1, 4, 1])
        with c1:
            if st.button("◀", key=f"left_{key_base}"):
                st.session_state.slider_index[key_base] = (img_index - 1) % len(found_images)
                st.rerun()
        with c3:
            if st.button("▶", key=f"right_{key_base}"):
                st.session_state.slider_index[key_base] = (img_index + 1) % len(found_images)
                st.rerun()

    col_index = (col_index + 1) % 3
