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
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store</h1>", unsafe_allow_html=True)

# --- Загрузка каталога ---
catalog_path = "data/catalog.xlsx"
xls = pd.ExcelFile(catalog_path)

# Объединяем все листы в один DataFrame
df_list = []
for sheet_name in xls.sheet_names:
    sheet_df = pd.read_excel(xls, sheet_name=sheet_name)
    sheet_df["brand_sheet"] = sheet_name
    df_list.append(sheet_df)
df = pd.concat(df_list, ignore_index=True)

# Заполняем пустые ячейки сверху вниз (для модели, бренда, цвета и т.д.)
df["brand"].ffill(inplace=True)
df["model"].ffill(inplace=True)
df["gender"].ffill(inplace=True)
df["color"].ffill(inplace=True)
df["description"].ffill(inplace=True)

# --- Группировка по модели и цвету ---
grouped = df.groupby(["brand", "model", "gender", "color"], dropna=True)

# --- Поиск фото ---
def find_image(img_name):
    img_name = img_name.strip()
    extensions = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
    for ext in extensions:
        files = glob.glob(f"data/images/**/*{img_name}*", recursive=True)
        for file in files:
            if file.lower().endswith(ext[1:]):
                return file
    return None

# --- Фильтры ---
st.sidebar.header("Фильтры")
brands = sorted(df["brand"].dropna().unique())
models = sorted(df["model"].dropna().unique())
genders = sorted(df["gender"].dropna().unique())
colors = sorted(df["color"].dropna().unique())

selected_brand = st.sidebar.multiselect("Бренд", brands)
selected_model = st.sidebar.multiselect("Модель", models)
selected_gender = st.sidebar.multiselect("Пол", genders)
selected_color = st.sidebar.multiselect("Цвет", colors)

filtered_df = df.copy()
if selected_brand:
    filtered_df = filtered_df[filtered_df["brand"].isin(selected_brand)]
if selected_model:
    filtered_df = filtered_df[filtered_df["model"].isin(selected_model)]
if selected_gender:
    filtered_df = filtered_df[filtered_df["gender"].isin(selected_gender)]
if selected_color:
    filtered_df = filtered_df[filtered_df["color"].isin(selected_color)]

filtered_groups = filtered_df.groupby(["brand", "model", "gender", "color"], dropna=True)

# --- Сетка карточек ---
cols = st.columns(4)
i = 0

for (brand, model, gender, color), group in filtered_groups:
    first_row = group.iloc[0]
    images = []
    if pd.notna(first_row["image"]):
        img_names = str(first_row["image"]).split()
        for img_name in img_names:
            img_path = find_image(img_name)
            if img_path:
                images.append(img_path)

    if not images:
        continue  # если фото нет, пропускаем карточку

    # Основное фото карточки
    img_main = images[0]

    # --- Карточка товара ---
    with cols[i]:
        with st.container(border=True):
            st.image(img_main, use_container_width=True)
            st.markdown(
                f"""
                <h4 style='margin:0; font-weight:600;'>{brand}</h4>
                <p style='margin:0; font-size:15px;'>{model}</p>
                <p style='margin:0; color:gray; font-size:13px;'>{color} / {gender}</p>
                <p style='margin:0; color:#333; font-size:15px;'>Цена: {int(first_row['price'])} ₸</p>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Подробнее", key=f"btn_{brand}_{model}_{color}"):
                with st.modal(f"{brand} {model} ({color})"):
                    st.image(images, width=200)
                    st.markdown(f"### {brand} {model}")
                    st.markdown(f"**Цвет:** {color}")
                    st.markdown(f"**Пол:** {gender}")

                    sizes_us = sorted(group["size US"].dropna().astype(str).unique())
                    sizes_eu = sorted(group["size EU"].dropna().astype(str).unique())
                    st.markdown(f"**Размеры (US):** {', '.join(sizes_us)}")
                    st.markdown(f"**Размеры (EU):** {', '.join(sizes_eu)}")

                    st.markdown(f"**Описание:** {first_row['description'] if pd.notna(first_row['description']) else '—'}")

                    in_stock = group["in stock"].dropna().unique()
                    if len(in_stock) > 0:
                        stock_text = "В наличии ✅" if "yes" in [x.lower() for x in in_stock] else "Нет в наличии ❌"
                    else:
                        stock_text = "Нет данных"
                    st.markdown(f"**Наличие:** {stock_text}")

    i = (i + 1) % 4
