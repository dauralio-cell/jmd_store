import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Sneakers Catalog", layout="wide")

# === Загрузка данных ===
@st.cache_data
def load_data():
    if os.path.exists("data/catalog.csv"):
        return pd.read_csv("data/catalog.csv")
    else:
        return pd.DataFrame(columns=["Артикул", "Название", "Цвет", "Цена", "Бренд"])

df = load_data()

# === Поиск изображений по SKU в подпапках ===
def get_images_by_sku(sku):
    image_folder = "data/images"
    matches = []
    for root, _, files in os.walk(image_folder):
        for file in sorted(files):
            if file.startswith(str(sku)) and file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                matches.append(os.path.join(root, file))
    return matches

# === Заголовок и фильтры ===
st.markdown("<h1 style='text-align: center;'>Sneakers Catalog</h1>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    brand_filter = st.selectbox("Бренд", ["Все"] + sorted(df["Бренд"].unique().tolist()) if not df.empty else ["Все"])
with col2:
    color_filter = st.selectbox("Цвет", ["Все"] + sorted(df["Цвет"].unique().tolist()) if not df.empty else ["Все"])
with col3:
    price_filter = st.slider("Цена", 0, int(df["Цена"].max() if not df.empty else 100000), (0, int(df["Цена"].max() if not df.empty else 100000)))

# === Фильтрация ===
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["Бренд"] == brand_filter]
if color_filter != "Все":
    filtered_df = filtered_df[filtered_df["Цвет"] == color_filter]
filtered_df = filtered_df[(filtered_df["Цена"] >= price_filter[0]) & (filtered_df["Цена"] <= price_filter[1])]

# === Стили стрелок поверх изображения ===
arrow_style = """
<style>
.image-container {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
}
.image-container img {
    width: 100%;
    border-radius: 10px;
}
.arrow {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.4);
    color: black;
    border: 1px solid black;
    border-radius: 50%;
    font-size: 18px;
    font-weight: bold;
    padding: 6px 10px;
    cursor: pointer;
    transition: 0.2s;
    z-index: 10;
}
.arrow:hover {
    background: rgba(0, 0, 0, 0.15);
}
.arrow-left {
    left: 10px;
}
.arrow-right {
    right: 10px;
}
</style>
"""
st.markdown(arrow_style, unsafe_allow_html=True)

# === Отображение карточек ===
cols = st.columns(3)

for idx, row in filtered_df.iterrows():
    with cols[idx % 3]:
        sku = row["Артикул"]
        images = get_images_by_sku(sku)
        if not images:
            images = ["data/images/no_image.jpg"]

        key_base = f"photo_{sku}"
        if key_base not in st.session_state:
            st.session_state[key_base] = 0

        photo_index = st.session_state[key_base]
        image_path = images[photo_index % len(images)]

        # HTML блок с картинкой и стрелками поверх
        img_html = f"""
        <div class="image-container">
            <img src="data:image/jpeg;base64,{open(image_path, 'rb').read().encode('base64').decode()}" alt="Фото">
            <button class="arrow arrow-left" onclick="fetch('/?prev={sku}')">◀</button>
            <button class="arrow arrow-right" onclick="fetch('/?next={sku}')">▶</button>
        </div>
        """
        try:
            with open(image_path, "rb") as f:
                image = Image.open(f)
                st.image(image, use_container_width=True)
        except:
            st.image("data/images/no_image.jpg", use_container_width=True)

        # Управление стрелками
        c1, c2, c3 = st.columns([1, 6, 1])
        with c1:
            if st.button("◀", key=f"prev_{sku}"):
                st.session_state[key_base] = (photo_index - 1) % len(images)
                st.rerun()
        with c3:
            if st.button("▶", key=f"next_{sku}"):
                st.session_state[key_base] = (photo_index + 1) % len(images)
                st.rerun()

        st.markdown(f"**{row['Название']}**")
        st.markdown(f"Цвет: {row['Цвет']}")
        st.markdown(f"Бренд: {row['Бренд']}")
        st.markdown(f"Цена: {row['Цена']} ₸")
