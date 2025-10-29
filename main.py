import streamlit as st
import pandas as pd
import os
from glob import glob

st.set_page_config(page_title="Каталог JMD Store", layout="wide")

# ====== 1. Загрузка Excel ======
@st.cache_data
def load_catalog(path="data/catalog.xlsx"):
    all_sheets = pd.read_excel(path, sheet_name=None)
    dfs = []

    for brand, df in all_sheets.items():
        df["brand"] = brand
        df[['model', 'gender', 'color', 'price', 'preorder', 'in stock', 'description', 'image']] = (
            df[['model', 'gender', 'color', 'price', 'preorder', 'in stock', 'description', 'image']].ffill()
        )
        dfs.append(df)

    catalog = pd.concat(dfs, ignore_index=True)
    catalog = catalog.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
    return catalog


df = load_catalog()

# ====== 2. Поиск фото ======
def find_images(image_code):
    images = []
    if pd.isna(image_code):
        return images
    parts = str(image_code).split()
    for part in parts:
        found = glob(os.path.join("data", "images", "**", f"{part}.*"), recursive=True)
        images.extend(found)
    return images


# ====== 3. Фильтры ======
col1, col2 = st.columns(2)
brands = ["Все"] + sorted(df["brand"].unique())
genders = ["Все"] + sorted(df["gender"].dropna().unique())

brand_filter = col1.selectbox("Бренд", brands)
gender_filter = col2.selectbox("Пол", genders)

filtered = df.copy()
if brand_filter != "Все":
    filtered = filtered[filtered["brand"] == brand_filter]
if gender_filter != "Все":
    filtered = filtered[filtered["gender"] == gender_filter]

# ====== 4. Группировка ======
groups = filtered.groupby(["brand", "model", "color"], dropna=True)

st.markdown("### Каталог моделей")

# ====== 5. Карточки ======
for (brand, model, color), group in groups:
    gender = group["gender"].iloc[0]
    description = group["description"].iloc[0]
    image_code = group["image"].iloc[0]
    images = find_images(image_code)
    sizes_eu = group["size EU"].dropna().astype(str).tolist()
    prices = group["price"].astype(str).tolist()

    size_price_map = dict(zip(sizes_eu, prices))

    # Состояние для выбранного фото
    img_key = f"img_{brand}_{model}_{color}"
    if img_key not in st.session_state:
        st.session_state[img_key] = 0

    # Основное фото
    current_index = st.session_state[img_key]
    main_photo = images[current_index] if images else None

    st.markdown("---")
    cols = st.columns([1, 2])

    # ====== Фото + мини-слайдер ======
    with cols[0]:
        if main_photo and os.path.exists(main_photo):
            st.image(main_photo, use_container_width=True)
        else:
            st.markdown(
                f"""
                <div style="text-align:center;padding:40px;border:1px solid #eee;
                            border-radius:10px;color:#888;">Нет фото</div>
                """,
                unsafe_allow_html=True,
            )

        # Мини-слайдер (миниатюры)
        if len(images) > 1:
            st.markdown(
                "<p style='margin-top:10px;margin-bottom:4px;color:#666;'>Фото:</p>",
                unsafe_allow_html=True,
            )
            thumb_cols = st.columns(len(images))
            for i, thumb_path in enumerate(images):
                with thumb_cols[i]:
                    if os.path.exists(thumb_path):
                        if st.button(" ", key=f"thumb_{model}_{color}_{i}"):
                            st.session_state[img_key] = i
                        st.image(thumb_path, use_container_width=True)

    # ====== Информация ======
    with cols[1]:
        st.markdown(f"### {model}")
        st.markdown(f"**Цвет:** {color}")
        st.markdown(f"**Пол:** {gender}")
        st.markdown(f"<p style='color:#666'>{description}</p>", unsafe_allow_html=True)

        selected_size = st.selectbox("Выберите размер (EU):", sizes_eu, key=f"size_{model}_{color}")
        current_price = size_price_map.get(selected_size, group["price"].iloc[0])
        st.markdown(f"**Цена:** {current_price} ₸")

        if st.button("Добавить в корзину", key=f"add_{model}_{color}_{selected_size}"):
            st.success(f"✅ {model} ({color}, EU {selected_size}) добавлен в корзину!")