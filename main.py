import streamlit as st
import pandas as pd
import os
from PIL import Image

# ==============================
# 🌟 Настройки страницы
# ==============================
st.set_page_config(page_title="DENE Store", layout="wide")

# ==============================
# 🌄 Баннер
# ==============================
banner_path = "data/images/banner.jpg"
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)
else:
    st.warning("⚠️ Не найден файл banner.jpg в data/images/")

st.markdown(
    "<h1 style='text-align:center; white-space: nowrap;'>DENE Store</h1>",
    unsafe_allow_html=True
)

# ==============================
# 📊 Загрузка Excel каталога
# ==============================
excel_path = "data/catalog.xlsx"
if not os.path.exists(excel_path):
    st.error("❌ Файл каталога не найден. Убедись, что он загружен в data/catalog.xlsx")
    st.stop()

# Считываем все листы
xls = pd.ExcelFile(excel_path)
all_data = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df["brand"] = sheet_name  # подставляем имя листа как бренд, если нужно
    all_data.append(df)

df = pd.concat(all_data, ignore_index=True)

# Убираем лишние пробелы в названиях колонок
df.columns = df.columns.str.strip()

# ==============================
# 🔍 Функции
# ==============================
def find_image(name):
    """Ищет первую найденную картинку в data/images/ по SKU или названию."""
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        path = f"data/images/{name}{ext}"
        if os.path.exists(path):
            return path
    return "data/images/no_image.jpg"

def get_first_image(image_str):
    if pd.isna(image_str) or not image_str:
        return "data/images/no_image.jpg"
    first_name = str(image_str).split()[0]
    return find_image(first_name)

# ==============================
# 🎛 Фильтры
# ==============================
brands = sorted(df["brand"].dropna().unique())
models = sorted(df["model"].dropna().unique())
genders = sorted(df["gender"].dropna().unique())
sizes = sorted(df["size US"].dropna().unique())

col1, col2, col3, col4 = st.columns(4)
brand_filter = col1.multiselect("Бренд", brands)
model_filter = col2.multiselect("Модель", models)
gender_filter = col3.multiselect("Пол", genders)
size_filter = col4.multiselect("Размер US", sizes)

filtered_df = df.copy()
if brand_filter:
    filtered_df = filtered_df[filtered_df["brand"].isin(brand_filter)]
if model_filter:
    filtered_df = filtered_df[filtered_df["model"].isin(model_filter)]
if gender_filter:
    filtered_df = filtered_df[filtered_df["gender"].isin(gender_filter)]
if size_filter:
    filtered_df = filtered_df[filtered_df["size US"].isin(size_filter)]

# ==============================
# 🧩 Группировка по цветам
# ==============================
grouped = (
    filtered_df.groupby(["brand", "model", "gender", "color"], dropna=False)
    .agg({
        "image": "first",
        "description": "first",
        "price": "first",
        "in stock": "first",
        "preorder": "first",
        "size US": lambda x: sorted(x.dropna().astype(str).unique()),
        "size EU": lambda x: sorted(x.dropna().astype(str).unique()),
    })
    .reset_index()
)

# ==============================
# 💳 Отображение карточек
# ==============================
st.markdown("---")
st.subheader("Каталог товаров")

cols = st.columns(4)

for i, (_, row) in enumerate(grouped.iterrows()):
    with cols[i % 4]:
        image_path = get_first_image(row["image"])
        brand = row["brand"]
        model = row["model"]
        color = row["color"]
        price = int(row["price"]) if pd.notna(row["price"]) else "—"
        stock = str(row.get("in stock", "")).strip().lower()
        available = "✅ В наличии" if stock == "yes" else "❌ Нет в наличии"

        # Карточка
        with st.container(border=True):
            st.image(image_path, use_container_width=True)
            st.markdown(f"**{brand} {model}**<br><small>{color}</small>", unsafe_allow_html=True)
            st.markdown(f"💸 <b>{price} ₸</b>", unsafe_allow_html=True)
            st.caption(available)

            # Popup окно
            if st.button("Подробнее", key=f"btn_{i}"):
                with st.expander(f"{brand} {model} — {color}", expanded=True):
                    st.image(image_path, use_container_width=True)
                    st.markdown(f"**Описание:** {row.get('description', '—')}")
                    st.markdown(f"**Размеры US:** {', '.join(row['size US']) if row['size US'] else '—'}")
                    st.markdown(f"**Размеры EU:** {', '.join(row['size EU']) if row['size EU'] else '—'}")
                    st.markdown(f"**Предзаказ:** {row.get('preorder', '—')}")
                    st.markdown(f"**Наличие:** {available}")

st.markdown("---")
st.caption("© DENE Store — 2025")
