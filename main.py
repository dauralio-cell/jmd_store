import streamlit as st
import pandas as pd
import os
from PIL import Image
import glob

# ----------------------------
# 🧭 Настройка путей
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMG_DIR = os.path.join(DATA_DIR, "images")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.xlsx")
BANNER_PATH = os.path.join(IMG_DIR, "banner.jpg")

# ----------------------------
# 🚨 Проверка файлов
# ----------------------------
if not os.path.exists(CATALOG_PATH):
    st.error(f"❌ Файл каталога не найден: {CATALOG_PATH}")
    st.stop()

if not os.path.exists(BANNER_PATH):
    st.warning(f"⚠️ Баннер не найден: {BANNER_PATH}")

# ----------------------------
# 📊 Загрузка каталога
# ----------------------------
def load_catalog(path):
    xls = pd.ExcelFile(path)
    dfs = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["sheet"] = sheet
        dfs.append(df)
    catalog = pd.concat(dfs, ignore_index=True)

    # Чистим пробелы, приводим к строкам
    catalog = catalog.fillna("")
    catalog.columns = [c.strip() for c in catalog.columns]
    return catalog

catalog = load_catalog(CATALOG_PATH)

# ----------------------------
# 🖼️ Загрузка баннера
# ----------------------------
if os.path.exists(BANNER_PATH):
    st.image(BANNER_PATH, use_container_width=True)

st.markdown(
    "<h1 style='text-align:center; margin-top:-20px;'>👟 DENE Store — Каталог кроссовок</h1>",
    unsafe_allow_html=True
)

# ----------------------------
# 🔍 Фильтры
# ----------------------------
brands = sorted([b for b in catalog["brand"].unique() if b])
models = sorted([m for m in catalog["model"].unique() if m])
genders = sorted([g for g in catalog["gender"].unique() if g])
sizes = sorted([s for s in catalog["size US"].unique() if s])

col1, col2, col3, col4 = st.columns(4)
brand_filter = col1.multiselect("Бренд", brands)
model_filter = col2.multiselect("Модель", models)
gender_filter = col3.multiselect("Пол", genders)
size_filter = col4.multiselect("Размер US", sizes)

filtered = catalog.copy()

if brand_filter:
    filtered = filtered[filtered["brand"].isin(brand_filter)]
if model_filter:
    filtered = filtered[filtered["model"].isin(model_filter)]
if gender_filter:
    filtered = filtered[filtered["gender"].isin(gender_filter)]
if size_filter:
    filtered = filtered[filtered["size US"].isin(size_filter)]

# ----------------------------
# 🖼️ Поиск фото
# ----------------------------
def find_image_files(image_names):
    files = []
    for name in image_names:
        pattern = os.path.join(IMG_DIR, "**", f"{name}.*")
        found = glob.glob(pattern, recursive=True)
        if found:
            files.append(found[0])
    return files

# ----------------------------
# 💎 Отображение карточек
# ----------------------------
st.markdown("<hr>", unsafe_allow_html=True)

if filtered.empty:
    st.info("Не найдено товаров по выбранным фильтрам 😔")
else:
    cols = st.columns(4)

    for i, (_, row) in enumerate(filtered.iterrows()):
        color = row["color"]
        brand = row["brand"]
        model = row["model"]
        price = row["price"]
        desc = row["description"]
        in_stock = str(row.get("in stock", "")).strip().lower() == "yes"
        preorder = str(row.get("preorder", "")).strip().lower() == "yes"
        size_us = str(row["size US"])
        size_eu = str(row["size EU"])
        images = str(row["image"]).split()

        image_files = find_image_files(images)
        main_image = image_files[0] if image_files else None

        with cols[i % 4]:
            with st.container(border=True):
                if main_image:
                    st.image(main_image, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/300x200?text=No+Image")

                st.markdown(
                    f"""
                    <h4 style='text-align:center'>{brand} {model}</h4>
                    <p style='text-align:center; color:gray'>{color}</p>
                    <p style='text-align:center; font-weight:bold; font-size:16px;'>{int(price):,} ₸</p>
                    <p style='text-align:center; color:{'green' if in_stock else 'red'}'>
                        {'В наличии' if in_stock else 'Нет в наличии'}
                    </p>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(f"Подробнее", key=f"btn_{i}"):
                    st.session_state["selected_product"] = row

# ----------------------------
# 🪟 Popup товара
# ----------------------------
if "selected_product" in st.session_state:
    row = st.session_state["selected_product"]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f"<h2 style='text-align:center'>{row['brand']} {row['model']}</h2>",
        unsafe_allow_html=True
    )
    st.markdown(f"<p style='text-align:center; color:gray'>{row['color']}</p>", unsafe_allow_html=True)

    images = str(row["image"]).split()
    image_files = find_image_files(images)

    img_cols = st.columns(len(image_files) if image_files else 1)
    for j, img in enumerate(image_files):
        with img_cols[j]:
            st.image(img, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**Описание:** {row['description']}")
    st.markdown(f"**Размеры US/EU:** {row['size US']} / {row['size EU']}")
    st.markdown(f"**Цена:** {int(row['price']):,} ₸")

    if str(row.get("preorder", "")).strip().lower() == "yes":
        st.markdown("🕓 *Доступен предзаказ*")

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Закрыть"):
        del st.session_state["selected_product"]
