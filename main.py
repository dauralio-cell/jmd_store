import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="JMD Store", layout="wide")

# --- Стили ---
st.markdown("""
<style>
body {
    background-color: #f8f9fa;
}
.card {
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    padding: 10px;
    transition: all 0.3s ease;
    background: white;
    cursor: pointer;
    text-align: center;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
.card img {
    border-radius: 12px;
    object-fit: cover;
}
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.65);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}
.modal-content {
    background-color: #fff;
    border-radius: 16px;
    padding: 25px;
    width: 80%;
    max-width: 900px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}
.modal img {
    border-radius: 10px;
    max-height: 400px;
    object-fit: cover;
}
.close-btn {
    background-color: #333;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    cursor: pointer;
    float: right;
}
.close-btn:hover {
    background-color: #555;
}
.thumb {
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s;
}
.thumb:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# --- Обложка ---
if os.path.exists("jmd_store/data/banner.jpg"):
    st.image("jmd_store/data/banner.jpg", use_container_width=True)
else:
    st.warning("⚠️ Не найден файл banner.jpg в jmd_store/data/")

# --- Загрузка Excel ---
excel_path = "jmd_store/data/catalog.xlsx"
if not os.path.exists(excel_path):
    st.error("Файл каталога не найден. Убедись, что он загружен в jmd_store/data/catalog.xlsx")
    st.stop()

df = pd.read_excel(excel_path)
df.fillna("", inplace=True)

# --- Функция поиска изображения ---
def find_image(name):
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        path = f"jmd_store/data/images/{name}{ext}"
        if os.path.exists(path):
            return path
    return None

# --- Кодирование картинки ---
def image_to_base64(img_path):
    try:
        with open(img_path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except:
        return None

# --- Группировка ---
grouped = df.groupby(["brand", "model", "gender", "color"], dropna=False)

# --- Фильтры ---
brands = sorted(df["brand"].dropna().unique())
models = sorted(df["model"].dropna().unique())
genders = sorted(df["gender"].dropna().unique())
colors = sorted(df["color"].dropna().unique())

st.sidebar.header("Фильтр товаров")
brand_filter = st.sidebar.multiselect("Бренд", brands)
model_filter = st.sidebar.multiselect("Модель", models)
gender_filter = st.sidebar.multiselect("Пол", genders)
color_filter = st.sidebar.multiselect("Цвет", colors)

def apply_filters(grouped):
    filtered = []
    for key, group in grouped:
        brand, model, gender, color = key
        if (not brand_filter or brand in brand_filter) and \
           (not model_filter or model in model_filter) and \
           (not gender_filter or gender in gender_filter) and \
           (not color_filter or color in color_filter):
            filtered.append((key, group))
    return filtered

filtered_groups = apply_filters(grouped)

# --- Отрисовка карточек ---
cols = st.columns(4)
i = 0

for (brand, model, gender, color), group in filtered_groups:
    first_row = group.iloc[0]
    img_names = str(first_row["image"]).split()
    images = [find_image(name) for name in img_names if find_image(name)]
    if not images:
        continue

    img_main = image_to_base64(images[0])
    if not img_main:
        continue

    price = int(first_row["price"]) if str(first_row["price"]).isdigit() else first_row["price"]

    with cols[i]:
        button_key = f"{brand}_{model}_{color}"
        if st.button("", key=f"btn_{button_key}"):
            st.session_state["popup"] = (brand, model, gender, color)
        st.markdown(f"""
            <div class='card'>
                <img src='{img_main}' width='100%' height='220'>
                <h4>{brand}</h4>
                <p style='margin:0;'>{model}</p>
                <p style='color:gray'>{color} / {gender}</p>
                <p style='font-weight:600;'>Цена: {price} ₸</p>
            </div>
        """, unsafe_allow_html=True)
    i = (i + 1) % 4

# --- Popup (модалка) ---
if "popup" in st.session_state:
    brand, model, gender, color = st.session_state["popup"]
    _, group = next(((k, g) for k, g in filtered_groups if k == (brand, model, gender, color)), (None, None))
    if group is not None:
        first_row = group.iloc[0]
        img_names = str(first_row["image"]).split()
        images = [find_image(name) for name in img_names if find_image(name)]
        sizes_us = ", ".join(str(s) for s in group["size US"].unique() if s)
        sizes_eu = ", ".join(str(s) for s in group["size EU"].unique() if s)
        price = int(first_row["price"]) if str(first_row["price"]).isdigit() else first_row["price"]
        desc = first_row["description"] or "Описание отсутствует"

        thumbs_html = "".join([
            f"<img src='{image_to_base64(img)}' width='70' class='thumb' style='margin:5px;'>"
            for img in images
        ])

        modal_html = f"""
        <div class="modal">
            <div class="modal-content">
                <button class="close-btn" onclick="window.location.reload()">Закрыть</button>
                <h2>{brand} {model} ({color})</h2>
                <div style="display:flex; gap:20px;">
                    <div style="flex:1;">
                        <img src="{image_to_base64(images[0])}" width="100%">
                        <div style="display:flex; justify-content:center; margin-top:10px;">{thumbs_html}</div>
                    </div>
                    <div style="flex:1;">
                        <p><b>Пол:</b> {gender}</p>
                        <p><b>Цвет:</b> {color}</p>
                        <p><b>Размеры US:</b> {sizes_us}</p>
                        <p><b>Размеры EU:</b> {sizes_eu}</p>
                        <p><b>Цена:</b> {price} ₸</p>
                        <p><b>Описание:</b> {desc}</p>
                    </div>
                </div>
            </div>
        </div>
        """

        st.markdown(modal_html, unsafe_allow_html=True)
