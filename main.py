import streamlit as st
import pandas as pd
import glob
import os
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Загрузка данных ---
catalog = pd.read_excel("data/catalog.xlsx").fillna("")
catalog.columns = catalog.columns.str.strip().str.lower()

# --- Получаем все картинки из подпапок ---
image_paths = glob.glob("data/images/**/*.*", recursive=True)
image_dict = {}

for path in image_paths:
    filename = os.path.splitext(os.path.basename(path))[0]
    image_dict[filename] = path

# --- Заголовок ---
st.markdown(
    """
    <h1 style='text-align:center; font-size:42px; margin-bottom:10px;'>👟 DENE Store</h1>
    <p style='text-align:center; color:gray;'>Каталог кроссовок</p>
    <hr style='margin-top:20px;'>
    """,
    unsafe_allow_html=True
)

# --- Сетка карточек товаров ---
num_cols = 3
rows = [catalog.iloc[i:i + num_cols] for i in range(0, len(catalog), num_cols)]

for row_df in rows:
    cols = st.columns(num_cols)
    for col, (_, row) in zip(cols, row_df.iterrows()):
        with col:
            # Находим все картинки для товара
            image_names = str(row["image"]).split()
            found_images = [image_dict[name] for name in image_names if name in image_dict]

            # Показываем первую картинку или заглушку
            if found_images:
                img = Image.open(found_images[0])
                st.image(img, use_container_width=True)
            else:
                st.image("data/images/no_image.jpg", use_container_width=True)

            # Карточка с описанием
            st.markdown(
                f"""
                <div style="
                    border:1px solid #eee;
                    border-radius:16px;
                    padding:12px;
                    margin-top:8px;
                    background-color:#fff;
                    box-shadow:0 2px 8px rgba(0,0,0,0.05);
                    text-align:center;
                ">
                    <h4 style="margin:4px 0;">{row['brand']} {row['model']}</h4>
                    <p style="color:gray; font-size:13px; margin:2px 0;">{row['color']} | {row['gender']}</p>
                    <p style="font-weight:bold; color:#111; margin:4px 0;">{int(row['price'])} ₸</p>
                    <p style="font-size:13px; color:{'green' if row['in stock'] == 'yes' else 'red'};">
                        {'В наличии' if row['in stock'] == 'yes' else 'Нет в наличии'}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

st.divider()
st.caption("© DENE Store 2025")