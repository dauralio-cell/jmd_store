import streamlit as st
import pandas as pd
import glob
import os
from PIL import Image

# ======================
# НАСТРОЙКИ СТРАНИЦЫ
# ======================
st.set_page_config(page_title="DENE Store", layout="wide")

# ======================
# БАННЕР
# ======================
banner_path = "data/images/banner.jpg"
if os.path.exists(banner_path):
    st.markdown(
        f"""
        <div style="
            position: relative;
            height: 320px;
            background-image: url('{banner_path}');
            background-size: cover;
            background-position: center;
            border-radius: 20px;
            margin-bottom: 40px;">
            <div style="
                position: absolute;
                inset: 0;
                background: rgba(0, 0, 0, 0.35);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;">
                <h1 style="color: white; font-size: 60px; font-weight: 700; text-shadow: 0 4px 15px rgba(0,0,0,0.7);">
                    DENE Store
                </h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ======================
# ЧТЕНИЕ КАТАЛОГА
# ======================
catalog_path = "data/catalog.xlsx"
all_sheets = pd.read_excel(catalog_path, sheet_name=None)
df = pd.concat(all_sheets.values(), ignore_index=True)
df.columns = [c.strip().lower() for c in df.columns]

# Очистим пробелы
df = df.fillna("")
df["model"] = df["model"].astype(str).str.strip()
df["color"] = df["color"].astype(str).str.strip()

# ======================
# ПОИСК ВСЕХ ИЗОБРАЖЕНИЙ
# ======================
image_files = glob.glob("data/images/**/*.*", recursive=True)
image_map = {os.path.splitext(os.path.basename(p))[0]: p for p in image_files}

def find_image_paths(image_string):
    images = []
    for img in str(image_string).split():
        img = img.strip()
        if img in image_map:
            images.append(image_map[img])
    return images

# ======================
# ГРУППИРОВКА МОДЕЛЕЙ
# ======================
models = []
for (brand, model), group in df.groupby(["brand", "model"], sort=False):
    colors = []
    for color, color_group in group.groupby("color", sort=False):
        if not color:
            continue
        images = find_image_paths(color_group.iloc[0]["image"])
        sizes_us = [s for s in color_group["size us"].tolist() if s]
        sizes_eu = [s for s in color_group["size eu"].tolist() if s]
        description = color_group.iloc[0]["description"]
        price = color_group.iloc[0]["price"]
        preorder = color_group.iloc[0]["preorder"]
        instock = color_group.iloc[0]["in stock"]
        colors.append({
            "color": color,
            "images": images,
            "sizes_us": sizes_us,
            "sizes_eu": sizes_eu,
            "description": description,
            "price": price,
            "preorder": preorder,
            "instock": instock
        })
    models.append({
        "brand": brand,
        "model": model,
        "colors": colors
    })

# ======================
# СТИЛЬ КАРТОЧЕК
# ======================
st.markdown("""
    <style>
    .card {
        border-radius: 18px;
        background-color: #111;
        color: #eee;
        box-shadow: 0 0 12px rgba(255,255,255,0.05);
        padding: 15px;
        transition: 0.3s;
        text-align: center;
    }
    .card:hover {
        box-shadow: 0 0 25px rgba(255,255,255,0.15);
        transform: translateY(-5px);
    }
    .card img {
        border-radius: 14px;
        height: 240px;
        width: 100%;
        object-fit: cover;
    }
    .brand {
        font-size: 16px;
        color: #aaa;
        margin-top: 8px;
    }
    .model {
        font-size: 18px;
        font-weight: 600;
        color: #fff;
    }
    .price {
        font-size: 16px;
        color: #6bf56b;
    }
    </style>
""", unsafe_allow_html=True)

# ======================
# ФИЛЬТРЫ
# ======================
st.sidebar.header("Фильтры 🔍")
brands = sorted(df["brand"].unique())
genders = sorted(df["gender"].unique())
selected_brand = st.sidebar.multiselect("Бренд", brands)
selected_gender = st.sidebar.multiselect("Пол", genders)

# ======================
# ОТОБРАЖЕНИЕ КАТАЛОГА
# ======================
cols = st.columns(4)
col_index = 0

for model in models:
    if selected_brand and model["brand"] not in selected_brand:
        continue
    for color_info in model["colors"]:
        first_img = color_info["images"][0] if color_info["images"] else "data/images/no_image.jpg"
        col = cols[col_index]
        with col:
            if st.button(f"{model['brand']} {model['model']} ({color_info['color']})", key=f"btn_{model['model']}_{color_info['color']}"):
                st.session_state["selected"] = {
                    "brand": model["brand"],
                    "model": model["model"],
                    "color_info": color_info,
                    "all_colors": model["colors"]
                }
            st.markdown(f"""
                <div class="card">
                    <img src="{first_img}">
                    <div class="brand">{model['brand']}</div>
                    <div class="model">{model['model']} ({color_info['color']})</div>
                    <div class="price">{int(color_info['price']) if color_info['price'] else ''} ₸</div>
                </div>
            """, unsafe_allow_html=True)
        col_index = (col_index + 1) % 4

# ======================
# POPUP ОКНО
# ======================
if "selected" in st.session_state:
    selected = st.session_state["selected"]
    color_info = selected["color_info"]
    all_colors = selected["all_colors"]

    with st.modal(f"{selected['brand']} {selected['model']} ({color_info['color']})"):
        st.markdown(f"### {selected['brand']} {selected['model']} ({color_info['color']})")
        st.image(color_info["images"], use_container_width=True)
        st.write(f"**Цена:** {color_info['price']} ₸")
        st.write(f"**Описание:** {color_info['description']}")
        st.write(f"**Размеры US:** {', '.join(color_info['sizes_us'])}")
        st.write(f"**Размеры EU:** {', '.join(color_info['sizes_eu'])}")
        st.write(f"**Наличие:** {'✅ В наличии' if str(color_info['instock']).lower() == 'yes' else '❌ Нет в наличии'}")
        st.divider()
        st.markdown("**Другие цвета этой модели:**")
        cols_c = st.columns(len(all_colors))
        for i, alt_color in enumerate(all_colors):
            if alt_color["color"] == color_info["color"]:
                continue
            alt_img = alt_color["images"][0] if alt_color["images"] else "data/images/no_image.jpg"
            with cols_c[i]:
                if st.button(f"{alt_color['color']}", key=f"color_{alt_color['color']}"):
                    st.session_state["selected"]["color_info"] = alt_color
                    st.rerun()

        if st.button("Закрыть"):
            del st.session_state["selected"]
            st.rerun()
