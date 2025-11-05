import streamlit as st
import pandas as pd
import glob
import os
import base64

# --- Настройки страницы ---
st.set_page_config(page_title="Детали товара - DENE Store", layout="wide")

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"

# --- Функции для работы с изображениями ---
def get_image_path(image_names, images_path="data/images"):
    """Ищет изображение по имени из колонки image"""
    if not image_names or pd.isna(image_names) or str(image_names).strip() == "":
        return os.path.join(images_path, "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(images_path, "no_image.jpg")
    
    first_image_name = image_names_list[0]
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(images_path, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        pattern_start = os.path.join(images_path, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    return os.path.join(images_path, "no_image.jpg")

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        with open(fallback, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

# --- Загрузка данных ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
        all_sheets = pd.read_excel(CATALOG_PATH, sheet_name=None)
        df = pd.concat(all_sheets.values(), ignore_index=True)
        df = df.fillna("")
        df.columns = [c.strip().lower() for c in df.columns]

        # Убедимся, что есть колонки для размеров
        if "size us" in df.columns:
            df.rename(columns={"size us": "size_us"}, inplace=True)
        if "size eu" in df.columns:
            df.rename(columns={"size eu": "size_eu"}, inplace=True)

        # Модель без размеров
        df["model_clean"] = (
            df["model"]
            .astype(str)
            .str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True)
            .str.strip()
        )

        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

# --- Основная логика ---
def main():
    # Кнопка "Назад"
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Назад к каталогу", use_container_width=True):
            st.switch_page("main.py")

    # Проверяем, выбран ли товар
    if "product_data" not in st.session_state:
        st.error("Товар не найден. Вернитесь в каталог и выберите товар.")
        return

    row = st.session_state.product_data

    # Заголовок товара
    st.markdown(f"## {row['brand']} {row['model_clean']}")

    df = load_data()
    if df.empty:
        st.warning("Не удалось загрузить данные о товаре.")
        return

    # Фильтруем по выбранной модели и бренду
    model_variants = df[
        (df["model_clean"] == row["model_clean"]) &
        (df["brand"] == row["brand"])
    ]

    # --- Основной блок: изображение + описание ---
    col1, col2 = st.columns([1, 2])

    with col1:
        image_path = get_image_path(row.get("image", ""))
        image_base64 = get_image_base64(image_path)
        st.markdown(
            f"""
            <img src="data:image/jpeg;base64,{image_base64}" 
                 style="width:100%; border-radius:12px; border:1px solid #eee; margin-bottom:10px;">
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(f"**Цена:** {int(row['price'])} ₸")
        st.markdown(f"**Пол:** {row.get('gender', '-')}")
        st.markdown(f"**Цвет:** {row.get('color', '-')}")
        st.markdown(f"**Описание:** {row.get('description', 'Описание отсутствует.')}")
        st.divider()

        # --- Доступные размеры для этого цвета ---
        color_df = model_variants[model_variants["color"] == row["color"]]
        sizes_us = sorted(set(color_df["size_us"].dropna().astype(str).tolist()))
        sizes_eu = sorted(set(color_df["size_eu"].dropna().astype(str).tolist()))

        if sizes_us or sizes_eu:
            st.markdown("### Доступные размеры:")
            size_str = ", ".join([f"US {us} / EU {eu}" for us, eu in zip(sizes_us, sizes_eu)]) or "-"
            st.markdown(size_str)
        else:
            st.info("Размеры для этого цвета не указаны.")

        # --- Другие цвета этой модели ---
        st.divider()
        color_variants = model_variants.drop_duplicates(subset=["color"])
        if len(color_variants) > 1:
            st.markdown("### Другие цвета:")
            cols = st.columns(4)
            for i, (_, variant) in enumerate(color_variants.iterrows()):
                with cols[i % 4]:
                    img_path = get_image_path(variant.get("image", ""))
                    img_b64 = get_image_base64(img_path)
                    st.markdown(
                        f"""
                        <img src="data:image/jpeg;base64,{img_b64}" 
                             style="width:100%; border-radius:8px; border:1px solid #ddd; margin-bottom:4px;">
                        <p style="text-align:center; font-weight:500;">{variant['color']}</p>
                        """,
                        unsafe_allow_html=True
                    )

if __name__ == "__main__":
    main()