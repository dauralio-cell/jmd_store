import streamlit as st
import pandas as pd
import os
import glob
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="JMD Store", layout="wide")

# --- Пути ---
DATA_DIR = "jmd_store/data"
IMG_DIR = os.path.join(DATA_DIR, "images")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.xlsx")
BANNER_PATH = os.path.join(IMG_DIR, "banner.jpg")

# --- Обложка ---
if os.path.exists(BANNER_PATH):
    st.image(BANNER_PATH, use_container_width=True)
else:
    st.warning(f"❌ Баннер не найден: {BANNER_PATH}")

st.markdown("<h1 style='text-align:center; font-size:40px;'>JMD Store</h1>", unsafe_allow_html=True)

# --- Проверка файла каталога ---
if not os.path.exists(CATALOG_PATH):
    st.error(f"❌ Файл каталога не найден: {CATALOG_PATH}")
    st.stop()

# --- Чтение Excel (все листы) ---
xls = pd.ExcelFile(CATALOG_PATH)
dfs = []
for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    df["brand"] = sheet  # подстраховка, если не указано в данных
    dfs.append(df)
data = pd.concat(dfs, ignore_index=True)

# --- Очистка данных ---
data = data.fillna("")
data = data[data["model"] != ""]

# --- Фильтры ---
brands = sorted(data["brand"].unique())
models = sorted(data["model"].unique())
genders = sorted(data["gender"].unique())
colors = sorted(data["color"].unique())

col1, col2, col3, col4 = st.columns(4)
brand_filter = col1.multiselect("Бренд", brands)
model_filter = col2.multiselect("Модель", models)
gender_filter = col3.multiselect("Пол", genders)
color_filter = col4.multiselect("Цвет", colors)

filtered = data.copy()
if brand_filter:
    filtered = filtered[filtered["brand"].isin(brand_filter)]
if model_filter:
    filtered = filtered[filtered["model"].isin(model_filter)]
if gender_filter:
    filtered = filtered[filtered["gender"].isin(gender_filter)]
if color_filter:
    filtered = filtered[filtered["color"].isin(color_filter)]

# --- Группировка по модели и цвету ---
grouped = filtered.groupby(["brand", "model", "color"], dropna=False)

# --- Функция для поиска изображений ---
def find_image_paths(image_names):
    found = []
    for name in str(image_names).split():
        pattern = os.path.join(IMG_DIR, "**", f"{name}.*")
        matches = glob.glob(pattern, recursive=True)
        if matches:
            found.extend(matches)
    return found

# --- Сетка карточек ---
for (brand, model, color), group in grouped:
    sku = group["sku"].iloc[0]
    images = find_image_paths(group["image"].iloc[0])
    sizes_us = [str(s) for s in group["size US"] if s]
    sizes_eu = [str(s) for s in group["size EU"] if s]
    price = group["price"].iloc[0]
    desc = group["description"].iloc[0]
    in_stock = group["in stock"].iloc[0]
    preorder = group["preorder"].iloc[0]

    if images:
        main_img = images[0]
    else:
        main_img = os.path.join(IMG_DIR, "no_image.jpg")

    col = st.container()
    with col:
        c1, c2 = st.columns([1, 3])
        with c1:
            try:
                st.image(main_img, use_container_width=True)
            except:
                st.warning("Ошибка при загрузке изображения")
        with c2:
            st.markdown(f"### {brand} — {model}")
            st.write(f"**Цвет:** {color}")
            st.write(f"**Цена:** {price} ₸")
            if in_stock.lower() == "yes":
                st.success("✅ В наличии")
            elif preorder.lower() == "yes":
                st.info("🕓 Предзаказ")
            else:
                st.error("❌ Нет в наличии")

            if st.button(f"Подробнее — {brand} {model} ({color})"):
                with st.expander(f"Подробнее о {brand} {model} ({color})", expanded=True):
                    if len(images) > 1:
                        cols = st.columns(min(len(images), 5))
                        for i, img in enumerate(images[:5]):
                            with cols[i]:
                                st.image(img, use_container_width=True)
                    st.write(f"**Размеры (US):** {', '.join(sizes_us)}")
                    st.write(f"**Размеры (EU):** {', '.join(sizes_eu)}")
                    st.write(f"**Описание:** {desc if desc else '—'}")

    st.divider()
