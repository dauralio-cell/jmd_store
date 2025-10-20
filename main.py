import streamlit as st
import pandas as pd
import os
import glob

DATA_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# === Новый блок: поиск изображений по SKU ===
def find_images_by_sku(base_path, sku):
    """Ищет изображения по SKU в любых подпапках (jpg, jpeg, png, webp)."""
    patterns = [
        f"**/{sku}_*.jpg",
        f"**/{sku}_*.jpeg",
        f"**/{sku}_*.png",
        f"**/{sku}_*.webp",
        f"**/{sku}.*",
    ]
    images = []
    for pattern in patterns:
        images.extend(glob.glob(os.path.join(base_path, pattern), recursive=True))
    images = [img for img in images if os.path.isfile(img)]
    return images if images else [os.path.join(base_path, "no_image.jpg")]

# === Функция загрузки каталога ===
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_PATH)
    df = df.fillna("")
    return df

df = load_data()

# === Интерфейс ===
st.set_page_config(page_title="Каталог товаров", layout="wide")

st.title("Каталог товаров")

brands = sorted(df["brand"].dropna().unique())
selected_brand = st.sidebar.selectbox("Выберите бренд", ["Все"] + brands)

if selected_brand != "Все":
    df = df[df["brand"] == selected_brand]

search_query = st.sidebar.text_input("Поиск по названию или SKU").strip().lower()

if search_query:
    df = df[df.apply(lambda row: search_query in str(row["SKU"]).lower() or search_query in str(row["model"]).lower(), axis=1)]

# === Сетка карточек ===
cols = st.columns(4)

for idx, (_, row) in enumerate(df.iterrows()):
    # Пропускаем, если нет цены
    if not str(row["price"]).strip():
        continue

    sku = str(row["SKU"]).strip()
    images = find_images_by_sku(IMAGES_PATH, sku)
    image_path = images[0] if images else os.path.join(IMAGES_PATH, "no_image.jpg")

    with cols[idx % 4]:
        st.markdown(
            f"""
            <div style='text-align:center; border:1px solid #ddd; border-radius:12px; padding:10px; margin:6px;'>
                <img src="data:image/jpeg;base64,{open(image_path, 'rb').read().encode('base64').decode()}" 
                     style='width:100%; border-radius:10px;' alt="Фото">
                <p style='font-weight:bold; font-size:16px; margin-top:6px;'>{row['brand']} {row['model']}</p>
                <p style='color:#444;'>SKU: {row['SKU']}</p>
                <p style='font-weight:bold; font-size:16px; color:#000;'>{int(row['price'])} ₸</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
