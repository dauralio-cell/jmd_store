import streamlit as st
import pandas as pd
import os
import glob
import re
import base64

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
st.image("data/images/banner.jpg", use_container_width=True)
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Вспомогательные функции ---
def get_image_variants(image_name):
    """Находит все фото по имени image (например 1100_1, 1100_2, ...) в любых форматах"""
    if not image_name:
        return []
    base_name = os.path.splitext(str(image_name))[0]
    patterns = [
        os.path.join(IMAGES_PATH, "**", f"{base_name}_*.jpg"),
        os.path.join(IMAGES_PATH, "**", f"{base_name}_*.jpeg"),
        os.path.join(IMAGES_PATH, "**", f"{base_name}_*.png"),
        os.path.join(IMAGES_PATH, "**", f"{base_name}_*.webp"),
    ]
    image_files = []
    for p in patterns:
        image_files += glob.glob(p, recursive=True)
    return sorted(image_files, key=lambda x: int(re.findall(r"_(\d+)", x)[0]) if re.findall(r"_(\d+)", x) else 0)

def encode_image(image_path):
    """Конвертирует изображение в base64"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        with open(fallback, "rb") as f:
            return base64.b64encode(f.read()).decode()

@st.cache_data(show_spinner=False)
def load_data():
    """Загружает все листы из Excel и объединяет"""
    sheets = pd.read_excel(CATALOG_PATH, sheet_name=None)
    all_data = []
    for sheet_name, df in sheets.items():
        df = df.fillna("")

        # Добавляем недостающие колонки
        required_cols = ["SKU", "brand", "model", "gender", "color", "image", "sizes", "prices"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""

        # Если нет brand — берём имя листа
        if df["brand"].eq("").all():
            df["brand"] = sheet_name

        all_data.append(df)

    df = pd.concat(all_data, ignore_index=True)

    # Очистка модели
    df["model_clean"] = (
        df["model"].astype(str).str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()
    )
    df["sizes"] = df["sizes"].astype(str)
    df["prices"] = df["prices"].astype(str)

    return df

# --- Фильтры ---
st.divider()
st.markdown("### 🔎 Фильтр каталога")

col1, col2, col3 = st.columns(3)
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
filtered_df = df if brand_filter == "Все" else df[df["brand"] == brand_filter]

models = sorted(df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + models)
gender_filter = col3.selectbox("Пол", ["Все"] + sorted(df["gender"].dropna().unique().tolist()))

# --- Применяем фильтры ---
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]

st.divider()
st.markdown("## 👟 Каталог товаров")

# --- Группировка по цвету ---
if model_filter != "Все":
    grouped = filtered_df.groupby("color")
else:
    grouped = [(None, filtered_df)]

num_cols = 4
rows = []
for _, group in grouped:
    rows.extend([group.iloc[i:i+num_cols] for i in range(0, len(group), num_cols)])

# --- Отображение карточек ---
for row_df in rows:
    cols = st.columns(num_cols)
    for col, (_, row) in zip(cols, row_df.iterrows()):
        with col:
            images = get_image_variants(row["image"])
            if not images:
                images = [os.path.join(IMAGES_PATH, "no_image.jpg")]
            image_base64_list = [encode_image(p) for p in images]

            # HTML блок с изображениями и стрелками
            img_tags = "".join(
                [f"<img class='slide' src='data:image/jpeg;base64,{img}' style='width:100%;border-radius:12px;display:none;object-fit:cover;height:220px;'/>" for img in image_base64_list]
            )

            st.markdown(
                f"""
                <div style="position:relative;border:1px solid #eee;border-radius:16px;padding:12px;margin-bottom:16px;
                            background-color:#fff;box-shadow:0 2px 10px rgba(0,0,0,0.05);overflow:hidden;">
                    {img_tags}
                    <button onclick="prevSlide(this)" style="position:absolute;left:10px;top:50%;transform:translateY(-50%);
                            background:none;border:none;font-size:26px;color:black;cursor:pointer;">&#10094;</button>
                    <button onclick="nextSlide(this)" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);
                            background:none;border:none;font-size:26px;color:black;cursor:pointer;">&#10095;</button>

                    <h4 style="margin:10px 0 4px 0;">{row['brand']} {row['model_clean']}</h4>
                    <p style="color:gray;font-size:13px;margin:0;">{row['color'].capitalize()}</p>
                    <p style="font-size:14px;color:#555;">Размеры (EU): {row['sizes']}</p>
                    <p style="font-weight:bold;font-size:16px;margin-top:6px;">{row['prices']} ₸</p>
                </div>

                <script>
                const doc = window.parent.document;
                let indexMap = new WeakMap();
                function showSlide(btn, n) {{
                    const card = btn.parentElement;
                    const slides = card.querySelectorAll('.slide');
                    if (!indexMap.has(card)) indexMap.set(card, 0);
                    let i = indexMap.get(card) + n;
                    if (i >= slides.length) i = 0;
                    if (i < 0) i = slides.length - 1;
                    slides.forEach((s, k) => s.style.display = k === i ? 'block' : 'none');
                    indexMap.set(card, i);
                }}
                function nextSlide(btn) {{ showSlide(btn, 1); }}
                function prevSlide(btn) {{ showSlide(btn, -1); }}
                doc.querySelectorAll('.slide').forEach((s, i) => s.style.display = i % 1 === 0 ? 'block' : 'none');
                </script>
                """,
                unsafe_allow_html=True
            )

st.divider()
st.caption("© DENE Store 2025")