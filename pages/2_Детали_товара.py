import streamlit as st
import pandas as pd
from PIL import Image
import os

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store — Детали", layout="wide")

# --- Загрузка данных ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("data/catalog.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# --- Заполняем пустые значения модели и цвета ---
df["model"] = df["model"].ffill()
df["color"] = df["color"].ffill()

# --- Определяем реальные имена колонок размеров ---
size_us_col = next((c for c in df.columns if "size" in c.lower() and "us" in c.lower()), None)
size_eu_col = next((c for c in df.columns if "size" in c.lower() and "eu" in c.lower()), None)

# --- Группировка модели + цвета ---
group_cols = [c for c in ["brand", "model", "color", "gender", "price", "description", "image"] if c in df.columns]
agg_dict = {}
if size_us_col:
    agg_dict[size_us_col] = lambda x: ", ".join(sorted(set(str(i) for i in x if pd.notna(i))))
if size_eu_col:
    agg_dict[size_eu_col] = lambda x: ", ".join(sorted(set(str(i) for i in x if pd.notna(i))))

df_grouped = df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()

# --- Если выбрана модель через session_state ---
if "selected_product" not in st.session_state:
    st.warning("Выберите товар из каталога.")
    st.stop()

product = st.session_state.selected_product
product_row = df_grouped[
    (df_grouped["brand"] == product["brand"]) &
    (df_grouped["model"] == product["model"]) &
    (df_grouped["color"] == product["color"])
]

if product_row.empty:
    st.error("Товар не найден.")
    st.stop()

row = product_row.iloc[0]

# --- Отображение информации ---
st.markdown(f"## {row['brand']} {row['model']}")
st.markdown(f"**Цвет:** {row['color']}  |  **Цена:** {row['price']}")

size_us = row.get(size_us_col, "")
size_eu = row.get(size_eu_col, "")
if size_us or size_eu:
    st.markdown(
        f"<p style='color:gray; font-size:13px; margin:0;'>"
        f"<b>Размеры:</b> "
        f"{'US ' + size_us if size_us else ''}"
        f"{' | ' if size_us and size_eu else ''}"
        f"{'EU ' + size_eu if size_eu else ''}"
        f"</p>",
        unsafe_allow_html=True
    )

st.markdown(f"<p>{row.get('description', '')}</p>", unsafe_allow_html=True)

image_path = row.get("image", "")
if image_path and os.path.exists(image_path):
    st.image(image_path, use_container_width=True)
else:
    st.image("data/images/no-image.jpg", use_container_width=True)

# --- Похожие товары (другие цвета той же модели) ---
similar = df_grouped[(df_grouped["model"] == row["model"]) & (df_grouped["color"] != row["color"])]
if not similar.empty:
    st.markdown("### Другие цвета:")
    cols = st.columns(4)
    for i, (_, sim) in enumerate(similar.iterrows()):
        col = cols[i % 4]
        with col:
            img = sim.get("image", "")
            if img and os.path.exists(img):
                st.image(img, use_container_width=True)
            else:
                st.image("data/images/no-image.jpg", use_container_width=True)
            st.markdown(sim["color"])
