import streamlit as st
import pandas as pd
import glob
import os
import re

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка ---
st.image("data/images/banner.jpg", width="stretch")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Пути и константы ---
CATALOG_PATH = "data/catalog.xlsx"
df = pd.read_excel(CATALOG_PATH)

# --- Таблица конверсии размеров US ↔ EU ---
size_conversion = {
    "6": "39", "6.5": "39.5", "7": "40", "7.5": "40.5",
    "8": "41", "8.5": "42", "9": "42.5", "9.5": "43",
    "10": "44", "10.5": "44.5", "11": "45", "11.5": "46", "12": "46.5"
}
reverse_conversion = {v: k for k, v in size_conversion.items()}

# --- Автообновление Excel ---
def get_last_modified_time():
    return os.path.getmtime(CATALOG_PATH)

@st.cache_data(show_spinner=False)
def load_data(last_modified_time):
    df = pd.read_excel(CATALOG_PATH)
    df = df.fillna("")

    df["model_clean"] = (
        df["model"]
        .str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True)
        .str.strip()
    )

    df["size_us"] = df["model"].apply(lambda x: re.search(r"(\d{1,2}(\.\d)?)(?=US)", x))
    df["size_us"] = df["size_us"].apply(lambda m: m.group(1) if m else "")
    df["size_eu"] = df["model"].apply(lambda x: re.search(r"(\d{2}(\.\d)?)(?=EU)", x))
    df["size_eu"] = df["size_eu"].apply(lambda m: m.group(1) if m else "")

    df["size_eu"] = df.apply(
        lambda r: size_conversion.get(r["size_us"], r["size_eu"]), axis=1
    )
    df["size_us"] = df.apply(
        lambda r: reverse_conversion.get(r["size_eu"], r["size_us"]), axis=1
    )

    df["gender"] = df["model"].apply(
        lambda x: "men" if "men" in x.lower() else (
            "women" if "women" in x.lower() else "unisex"
        )
    )
    df["color"] = df["model"].str.extract(
        r"(white|black|blue|red|green|pink|gray|brown)", expand=False
    ).fillna("other")

    if "description" not in df.columns:
        df["description"] = "Описание временно недоступно."

    return df


# --- Загружаем данные ---
last_modified_time = get_last_modified_time()
df = load_data(last_modified_time)

# --- Фильтры ---
st.divider()
st.markdown("### 🔎 Фильтр каталога")

col1, col2, col3, col4, col5, col6 = st.columns(6)
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))
filtered_df = df if brand_filter == "Все" else df[df["brand"] == brand_filter]

models = sorted(filtered_df["model_clean"].unique().tolist())
model_filter = col2.selectbox("Модель", ["Все"] + models)

size_us_filter = col3.selectbox("Размер (US)", ["Все"] + sorted(df["size_us"].dropna().unique().tolist()))
size_eu_filter = col4.selectbox("Размер (EU)", ["Все"] + sorted(df["size_eu"].dropna().unique().tolist()))
gender_filter = col5.selectbox("Пол", ["Все", "men", "women", "unisex"])
color_filter = col6.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique().tolist()))

# --- Применяем фильтры ---
filtered_df = df.copy()
if brand_filter != "Все":
    filtered_df = filtered_df[filtered_df["brand"] == brand_filter]
if model_filter != "Все":
    filtered_df = filtered_df[filtered_df["model_clean"] == model_filter]
if size_us_filter != "Все":
    eu_equiv = size_conversion.get(size_us_filter, "")
    filtered_df = filtered_df[
        (filtered_df["size_us"] == size_us_filter) | (filtered_df["size_eu"] == eu_equiv)
    ]
if size_eu_filter != "Все":
    us_equiv = reverse_conversion.get(size_eu_filter, "")
    filtered_df = filtered_df[
        (filtered_df["size_eu"] == size_eu_filter) | (filtered_df["size_us"] == us_equiv)
    ]
if gender_filter != "Все":
    filtered_df = filtered_df[filtered_df["gender"] == gender_filter]
if color_filter != "Все":
    filtered_df = filtered_df[filtered_df["color"] == color_filter]

st.divider()

# --- 🔍 Новый блок: поиск фото во всех подпапках ---
def get_images_for_sku(sku):
    """Ищет изображения по SKU во всех подпапках (jpg, jpeg, png, webp)."""
    sku = str(sku).strip()
    base_dir = os.path.join("data", "images")

    if not sku:
        return [os.path.join(base_dir, "no_image.jpg")]

    patterns = [
        os.path.join(base_dir, "**", f"{sku}*.jpg"),
        os.path.join(base_dir, "**", f"{sku}*.jpeg"),
        os.path.join(base_dir, "**", f"{sku}*.png"),
        os.path.join(base_dir, "**", f"{sku}*.webp"),
    ]

    found_images = []
    for pattern in patterns:
        found_images.extend(glob.glob(pattern, recursive=True))

    def extract_number(filename):
        match = re.search(r"_(\d+)", filename)
        return int(match.group(1)) if match else 0

    found_images.sort(key=extract_number)

    if not found_images:
        return [os.path.join(base_dir, "no_image.jpg")]

    return found_images


# --- Каталог товаров ---
st.markdown("## 👟 Каталог товаров")

num_cols = 4
rows = [filtered_df.iloc[i:i+num_cols] for i in range(0, len(filtered_df), num_cols)]

for row_df in rows:
    cols = st.columns(num_cols)
    for col, (_, row) in zip(cols, row_df.iterrows()):
        if str(row["price"]).strip() == "" or str(row["model_clean"]).strip() == "":
            continue  # пропускаем пустые
        with col:
            images = get_images_for_sku(row["SKU"])
            image_path = images[0] if images else "data/images/no_image.jpg"

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
                    <img src='{image_path}' style='width:100%; border-radius:12px; object-fit:cover; height:220px;'>
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

st.divider()
st.caption("© DENE Store 2025
