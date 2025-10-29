import streamlit as st
import pandas as pd
import os
import glob
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="JMD Store", layout="wide")

# --- Путь к данным ---
DATA_DIR = "data"
IMAGE_DIR = os.path.join(DATA_DIR, "images")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.xlsx")

# --- Загрузка баннера ---
banner_path = os.path.join(IMAGE_DIR, "banner.jpg")
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)

st.markdown("<h1 style='text-align:center; margin-top:-20px;'>JMD Store</h1>", unsafe_allow_html=True)

# --- Загрузка Excel с несколькими листами ---
xls = pd.ExcelFile(CATALOG_PATH)
df_list = []
for sheet_name in xls.sheet_names:
    sheet_df = pd.read_excel(xls, sheet_name)
    sheet_df["brand"] = sheet_name  # если в листе нет столбца brand
    df_list.append(sheet_df)
df = pd.concat(df_list, ignore_index=True)

# --- Очистка и подготовка данных ---
df.columns = df.columns.str.strip().str.lower()
df = df.fillna("")
df["image"] = df["image"].astype(str)
df["color"] = df["color"].astype(str)

# --- Функция поиска изображения по всем подпапкам ---
def find_image_paths(image_names):
    found_paths = []
    for name in image_names.split():
        pattern = os.path.join(IMAGE_DIR, "**", f"{name}.*")
        matches = glob.glob(pattern, recursive=True)
        if matches:
            found_paths.append(matches[0])
    return found_paths

# --- Группировка по модели и цвету ---
grouped = []
for (brand, model, gender, color), group in df.groupby(["brand", "model", "gender", "color"]):
    images = " ".join(group["image"].unique()).strip()
    sizes_us = sorted(set(group["size us"].astype(str)))
    sizes_eu = sorted(set(group["size eu"].astype(str)))
    price = group["price"].iloc[0]
    preorder = group["preorder"].iloc[0]
    in_stock = group["in stock"].iloc[0] if "in stock" in group.columns else ""
    description = group["description"].iloc[0] if "description" in group.columns else ""
    grouped.append({
        "brand": brand,
        "model": model,
        "gender": gender,
        "color": color,
        "images": images,
        "sizes_us": sizes_us,
        "sizes_eu": sizes_eu,
        "price": price,
        "preorder": preorder,
        "in_stock": in_stock,
        "description": description
    })
cards_df = pd.DataFrame(grouped)

# --- Фильтры ---
col1, col2, col3, col4, col5 = st.columns(5)
brands = ["Все"] + sorted(cards_df["brand"].unique().tolist())
models = ["Все"] + sorted(cards_df["model"].unique().tolist())
genders = ["Все"] + sorted(cards_df["gender"].unique().tolist())
colors = ["Все"] + sorted(cards_df["color"].unique().tolist())
sizes = ["Все"] + sorted({s for lst in cards_df["sizes_us"] for s in lst if s})

with col1:
    brand_filter = st.selectbox("Бренд", brands)
with col2:
    model_filter = st.selectbox("Модель", models)
with col3:
    gender_filter = st.selectbox("Пол", genders)
with col4:
    color_filter = st.selectbox("Цвет", colors)
with col5:
    size_filter = st.selectbox("Размер US", sizes)

# --- Применение фильтров ---
filtered = cards_df.copy()
if brand_filter != "Все":
    filtered = filtered[filtered["brand"] == brand_filter]
if model_filter != "Все":
    filtered = filtered[filtered["model"] == model_filter]
if gender_filter != "Все":
    filtered = filtered[filtered["gender"] == gender_filter]
if color_filter != "Все":
    filtered = filtered[filtered["color"] == color_filter]
if size_filter != "Все":
    filtered = filtered[filtered["sizes_us"].apply(lambda x: size_filter in x)]

# --- Отображение карточек ---
st.markdown("---")
cols = st.columns(4)
for idx, row in enumerate(filtered.itertuples()):
    image_paths = find_image_paths(row.images)
    first_image = image_paths[0] if image_paths else None

    with cols[idx % 4]:
        if first_image:
            st.image(first_image, use_container_width=True)
        else:
            st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
        
        st.markdown(f"""
        <div style='text-align:center; margin-top:-10px;'>
            <b>{row.brand}</b><br>
            {row.model}<br>
            <span style='color:gray; font-size:13px;'>{row.color}</span><br>
            <span style='font-weight:bold;'>{row.price} ₸</span><br>
            <button style='margin-top:5px; padding:5px 10px; border:none; background-color:#333; color:white; border-radius:6px; cursor:pointer;' 
                onclick="window.location.href='?popup={idx}'">Подробнее</button>
        </div>
        """, unsafe_allow_html=True)

# --- Popup (деталка карточки) ---
query_params = st.query_params
if "popup" in query_params:
    popup_idx = int(query_params["popup"])
    if popup_idx < len(filtered):
        product = filtered.iloc[popup_idx]
        popup_images = find_image_paths(product["images"])

        with st.container():
            st.markdown(
                """
                <style>
                .popup {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background-color: rgba(0,0,0,0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }
                .popup-content {
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    max-width: 900px;
                    width: 90%;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    overflow-y: auto;
                    max-height: 90vh;
                }
                .close-btn {
                    float: right;
                    font-size: 20px;
                    cursor: pointer;
                    color: #999;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown("<div class='popup'><div class='popup-content'>", unsafe_allow_html=True)
            st.markdown("<span class='close-btn' onclick='window.location.href=\"/\"'>&times;</span>", unsafe_allow_html=True)

            st.markdown(f"### {product['brand']} — {product['model']} ({product['color']})")
            if popup_images:
                st.image(popup_images, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/800x500?text=No+Image", use_container_width=True)
            
            st.markdown(f"**Цена:** {product['price']} ₸")
            if product['in_stock'] == 'yes':
                st.markdown("<p style='color:green;'>В наличии</p>", unsafe_allow_html=True)
            elif product['preorder'] == 'yes':
                st.markdown("<p style='color:orange;'>Доступен для предзаказа</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:red;'>Нет в наличии</p>", unsafe_allow_html=True)
            
            st.markdown(f"**Размеры (US):** {' | '.join(product['sizes_us'])}")
            st.markdown(f"**Размеры (EU):** {' | '.join(product['sizes_eu'])}")
            st.markdown(f"**Описание:** {product['description']}")
            st.markdown("</div></div>", unsafe_allow_html=True)
