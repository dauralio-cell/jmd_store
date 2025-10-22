import streamlit as st
import pandas as pd
import os
from PIL import Image

# ============ НАСТРОЙКИ ============
DATA_PATH = "data/catalog.xlsx"
IMAGES_FOLDER = "data/images"

st.set_page_config(page_title="JMD Store", layout="wide")

@st.cache_data
def load_data():
    xls = pd.ExcelFile(DATA_PATH)
    sheets = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
    df = pd.concat(sheets.values(), ignore_index=True)
    return df

df = load_data()

# ============ САЙДБАР ============
st.sidebar.title("Фильтры")
brands = ["Все"] + sorted(df["brand"].dropna().unique().tolist())
genders = ["Все"] + sorted(df["gender"].dropna().unique().tolist())

# размеры
sizes_eu = sorted({str(s).strip() for sub in df["size EU"].dropna().astype(str).str.split(",") for s in sub if s.strip()})
sizes_us = sorted({str(s).strip() for sub in df["size US"].dropna().astype(str).str.split(",") for s in sub if s.strip()})

brand_filter = st.sidebar.selectbox("Бренд", brands)
gender_filter = st.sidebar.selectbox("Пол", genders)
size_type = st.sidebar.radio("Тип размера", ["EU", "US"])
size_filter = st.sidebar.selectbox(
    f"Размер ({size_type})", ["Все"] + (sizes_eu if size_type == "EU" else sizes_us)
)

# ============ ФИЛЬТРАЦИЯ ============
filtered_df = df.copy()

if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]

size_col = "size EU" if size_type == "EU" else "size US"
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df[size_col].astype(str).str.contains(size_filter, na=False)]

# ============ ФУНКЦИЯ ЗАГРУЗКИ ФОТО ============
def get_images(image_names_str):
    image_list = []
    if not isinstance(image_names_str, str):
        return image_list
    names = image_names_str.split()
    for name in names:
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            path = os.path.join(IMAGES_FOLDER, name + ext)
            if os.path.exists(path):
                image_list.append(path)
    return image_list

# ============ ПОКАЗ ТОВАРОВ ============
st.title("Каталог товаров")

cols = st.columns(3)
for idx, (_, row) in enumerate(filtered_df.iterrows()):
    with cols[idx % 3]:
        sku = str(row.get("sku", ""))
        images = get_images(row.get("image", ""))

        if len(images) == 0:
            st.warning(f"Нет фото для {sku}")
            continue

        # индекс фото в сессии
        if f"img_index_{sku}" not in st.session_state:
            st.session_state[f"img_index_{sku}"] = 0

        img_index = st.session_state[f"img_index_{sku}"]
        image_path = images[img_index]
        image = Image.open(image_path)

        st.image(image, use_container_width=True)

        # стрелки
        col_left, col_mid, col_right = st.columns([1, 4, 1])
        with col_left:
            if st.button("◀", key=f"left_{sku}_{idx}"):
                st.session_state[f"img_index_{sku}"] = (img_index - 1) % len(images)
                st.rerun()
        with col_right:
            if st.button("▶", key=f"right_{sku}_{idx}"):
                st.session_state[f"img_index_{sku}"] = (img_index + 1) % len(images)
                st.rerun()

        # инфо
        st.markdown(f"**{row.get('brand', '')}** {row.get('model', '')}")
        st.caption(f"Пол: {row.get('gender', '')} | EU: {row.get('size EU', '')} | US: {row.get('size US', '')}")
        st.text(f"Артикул: {sku}")
