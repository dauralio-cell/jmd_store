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

# --- Загрузка всех листов Excel ---
excel_path = "data/catalog.xlsx"
sheets = pd.ExcelFile(excel_path).sheet_names

dfs = []
for sheet in sheets:
    df_temp = pd.read_excel(excel_path, sheet_name=sheet)
    df_temp["brand"] = sheet.strip()  # имя листа = бренд
    dfs.append(df_temp)

df = pd.concat(dfs, ignore_index=True)
df.columns = df.columns.str.strip().str.lower()

# --- Проверяем ключевые колонки ---
required_cols = ["brand", "model", "gender", "color", "image", "size us", "price", "in stock"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"❌ В таблице не хватает колонок: {missing}")
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

# --- Группировка по модели и цвету ---
grouped = (
    filtered_df.groupby(["brand", "model", "color"], as_index=False)
    .agg({
        "image": "first",
        "price": "first",
        "in stock": "first",
        "size us": lambda x: sorted(x.dropna().unique().tolist()),
        "gender": "first"
    })
)

# --- Поиск изображений ---
image_paths = glob.glob("data/images/**/*.*", recursive=True)
image_map = {os.path.splitext(os.path.basename(p))[0]: p for p in image_paths}

# --- Вывод карточек ---
st.markdown("### Каталог товаров")

if grouped.empty:
    st.warning("😕 Нет товаров по заданным фильтрам.")
else:
    cols = st.columns(4)
    for idx, (_, row) in enumerate(grouped.iterrows()):
        with cols[idx % 4]:
            image_names = str(row["image"]).split()
            found = None
            for name in image_names:
                if name in image_map:
                    found = image_map[name]
                    break
            
            if found:
                st.image(found, use_container_width=True)
            else:
                st.image("data/images/no_image.jpg", use_container_width=True)

            st.markdown(f"**{row['brand']} {row['model']} ({row['color']})**")
            st.markdown(f"Пол: {row['gender']}")
            st.markdown(f"Размеры: {', '.join(map(str, row['size us']))}")
            st.markdown(f"Цена: {int(row['price'])} ₸")

            color = "green" if str(row["in stock"]).strip().lower() == "yes" else "red"
            st.markdown(f"<p style='font-size:13px; color:{color};'>В наличии: {row['in stock']}</p>", unsafe_allow_html=True)
