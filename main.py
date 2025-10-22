import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Каталог", layout="wide")

# === Функция для загрузки данных ===
@st.cache_data
def load_data():
    excel_path = "catalog.xlsx"
    xls = pd.ExcelFile(excel_path)
    df_list = []
    for sheet in xls.sheet_names:
        sheet_df = pd.read_excel(xls, sheet_name=sheet)
        df_list.append(sheet_df)
    df = pd.concat(df_list, ignore_index=True)
    df = df.fillna(method="ffill")  # тянем значения модели, цвета, бренда и т.д. вниз
    df["model_clean"] = df["model"].astype(str).apply(lambda x: x.split("(")[0].strip())
    df["size EU"] = df["size EU"].astype(str)
    return df

df = load_data()

# === Фильтры ===
col1, col2, col3, col4 = st.columns(4)

brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
model_filter = col2.selectbox("Модель", ["Все"] + sorted(df["model_clean"].unique().tolist()))
gender_filter = col3.selectbox("Пол", ["Все"] + sorted(df["gender"].unique().tolist()))
size_filter = col4.selectbox("Размер (EU)", ["Все"] + sorted(df["size EU"].unique().tolist()))

filtered_df = df.copy()

if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if size_filter != "Все":
    filtered_df = filtered_df[filtered_df["size EU"] == size_filter]

# === Поиск файлов изображений ===
def find_images(sku_prefix):
    found = []
    for root, dirs, files in os.walk("data/images"):
        for f in files:
            name, ext = os.path.splitext(f)
            if ext.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                if name.startswith(str(sku_prefix)):
                    found.append(os.path.join(root, f))
    found.sort()
    return found

# === Кодирование картинки в base64 ===
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

# === Группировка карточек ===
grouped = filtered_df.groupby(["brand", "model_clean", "gender", "color"])

# === Отображение карточек ===
for (brand, model, gender, color), group in grouped:
    sizes = ", ".join(sorted(set(group["size EU"].astype(str))))
    price = group["price"].replace("", float("nan")).dropna().unique()
    price_text = f"{price[0]} ₸" if len(price) > 0 else "Уточнить"

    # Фото по SKU
    sku_first = group["sku"].iloc[0]
    image_files = find_images(sku_first)
    image_b64_list = [get_image_base64(p) for p in image_files if get_image_base64(p)]

    # HTML блок карточки
    if image_b64_list:
        image_slides = "".join(
            f'<div class="slide"><img src="data:image/jpeg;base64,{b}" style="width:100%;border-radius:10px;"/></div>'
            for b in image_b64_list
        )
    else:
        image_slides = '<div class="slide"><div style="width:100%;height:250px;background:#f0f0f0;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#888;">No Image</div></div>'

    st.markdown(
        f"""
        <div class="card">
            <div class="slider">
                {image_slides}
                <a class="prev">&#10094;</a>
                <a class="next">&#10095;</a>
            </div>
            <h4 style="margin:10px 0 4px 0;">{brand} {model}</h4>
            <p style="color:gray;font-size:13px;margin:0;">{color}</p>
            <p style="font-size:14px;color:#555;">Размеры (EU): {sizes}</p>
            <p style="font-weight:bold;font-size:16px;margin-top:6px;">{price_text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# === CSS + JS для стрелочного слайдера и свайпа ===
st.markdown(
    """
    <style>
    .card {
        border:1px solid #eee;
        border-radius:12px;
        padding:12px;
        margin-bottom:25px;
        box-shadow:0 2px 8px rgba(0,0,0,0.06);
        max-width:350px;
    }
    .slider {
        position: relative;
        overflow: hidden;
        border-radius:10px;
    }
    .slide {
        display: none;
        transition: transform 0.3s ease-in-out;
    }
    .slide.active {
        display: block;
    }
    .prev, .next {
        cursor: pointer;
        position: absolute;
        top: 50%;
        width: auto;
        padding: 6px;
        color: black;
        font-weight: bold;
        font-size: 18px;
        border-radius: 0 3px 3px 0;
        user-select: none;
        background: rgba(255,255,255,0.6);
        transform: translateY(-50%);
    }
    .next { right: 0; border-radius: 3px 0 0 3px; }
    .prev:hover, .next:hover { background: rgba(255,255,255,0.9); }
    </style>

    <script>
    const sliders = window.parent.document.querySelectorAll('.slider');
    sliders.forEach(slider => {
        let slideIndex = 0;
        const slides = slider.querySelectorAll('.slide');
        const prev = slider.querySelector('.prev');
        const next = slider.querySelector('.next');
        const showSlide = (n) => {
            slides.forEach((s, i) => s.classList.toggle('active', i === n));
        };
        showSlide(slideIndex);
        prev.addEventListener('click', () => {
            slideIndex = (slideIndex - 1 + slides.length) % slides.length;
            showSlide(slideIndex);
        });
        next.addEventListener('click', () => {
            slideIndex = (slideIndex + 1) % slides.length;
            showSlide(slideIndex);
        });
        // свайп
        let startX = 0;
        slider.addEventListener('touchstart', e => startX = e.touches[0].clientX);
        slider.addEventListener('touchend', e => {
            let endX = e.changedTouches[0].clientX;
            if (startX - endX > 50) next.click();
            else if (endX - startX > 50) prev.click();
        });
    });
    </script>
    """,
    unsafe_allow_html=True
)
