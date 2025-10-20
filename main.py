import streamlit as st
import pandas as pd
import glob
import os

# ==============================
# Настройки страницы
# ==============================
st.set_page_config(page_title="Sneaker Catalog", layout="wide")

# ==============================
# Обложка
# ==============================
st.markdown(
    """
    <div style='text-align:center; padding:40px 0;'>
        <h1 style='font-size:48px; margin-bottom:10px;'>🏁 Sneaker Catalog</h1>
        <p style='font-size:18px; color:gray;'>Поиск по бренду, цвету, размеру и цене</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# Загрузка данных
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("data/sneakers.csv")

    df["brand"] = df["brand"].fillna("").astype(str).str.strip()
    df["model_clean"] = df["model_clean"].fillna("").astype(str).str.strip()
    df["color"] = df["color"].fillna("").astype(str).str.strip()
    df["size_us"] = df["size_us"].fillna("")
    df["size_eu"] = df["size_eu"].fillna("")
    df["description"] = df["description"].fillna("")
    df["price"] = df["price"].fillna(0)
    df["SKU"] = df["SKU"].fillna("").astype(str).str.strip()
    return df

df = load_data()

# ==============================
# Панель фильтров
# ==============================
with st.sidebar:
    st.header("🔍 Фильтры")

    brands = sorted(df["brand"].dropna().unique())
    brand_filter = st.multiselect("Бренд", options=brands)

    colors = sorted(df["color"].dropna().unique())
    color_filter = st.multiselect("Цвет", options=colors)

    sizes_us = sorted(df["size_us"].dropna().unique())
    size_us_filter = st.multiselect("Размер US", options=sizes_us)

    price_min, price_max = st.slider(
        "Цена (₸)", 
        int(df["price"].min()), 
        int(df["price"].max()), 
        (int(df["price"].min()), int(df["price"].max()))
    )

# ==============================
# Применяем фильтры
# ==============================
filtered_df = df.copy()
if brand_filter:
    filtered_df = filtered_df[filtered_df["brand"].isin(brand_filter)]
if color_filter:
    filtered_df = filtered_df[filtered_df["color"].isin(color_filter)]
if size_us_filter:
    filtered_df = filtered_df[filtered_df["size_us"].isin(size_us_filter)]

filtered_df = filtered_df[
    (filtered_df["price"] >= price_min) & (filtered_df["price"] <= price_max)
]

# ==============================
# Сетка карточек товаров
# ==============================
st.markdown("## 👟 Каталог товаров")

num_cols = 4
rows = [filtered_df.iloc[i:i + num_cols] for i in range(0, len(filtered_df), num_cols)]

for row_df in rows:
    cols = st.columns(num_cols)
    for col, (_, row) in zip(cols, row_df.iterrows()):
        with col:
            # Ищем все изображения SKU (в любых подпапках и форматах)
            image_files = glob.glob(f"data/images/**/*{row['SKU']}*.*", recursive=True)
            image_files = [img for img in image_files if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

            # Если нет — подставляем no_image.jpg
            if not image_files:
                image_files = ["data/images/no_image.jpg"]

            main_image = image_files[0]

            # --- Карточка товара ---
            st.markdown(
                f"""
                <div style="
                    border:1px solid #eee;
                    border-radius:16px;
                    padding:12px;
                    margin-bottom:16px;
                    background-color:#fff;
                    box-shadow:0 2px 10px rgba(0,0,0,0.05);
                    transition:transform 0.2s ease-in-out;
                " onmouseover="this.style.transform='scale(1.02)';"
                  onmouseout="this.style.transform='scale(1)';">
                    <img src='{main_image}' style='width:100%; border-radius:12px; object-fit:cover; height:220px;'>
                    <h4 style="margin:10px 0 4px 0;">{row['brand']} {row['model_clean']}</h4>
                    <p style="color:gray; font-size:13px; margin:0;">
                        US {row['size_us'] or '-'} | EU {row['size_eu'] or '-'} | {row['color']}
                    </p>
                    <p style="font-size:14px; color:#555;">{row['description']}</p>
                    <p style="font-weight:bold; font-size:16px; margin-top:6px;">{int(row['price'])} ₸</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # --- Галерея (если есть доп. фото) ---
            if len(image_files) > 1:
                with st.expander("📸 Другие фото"):
                    st.image(image_files, use_container_width=True)

# ==============================
# Если ничего не найдено
# ==============================
if filtered_df.empty:
    st.warning("⚠️ Товары по выбранным фильтрам не найдены.")
