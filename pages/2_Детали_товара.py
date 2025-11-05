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

# --- Функции для изображений ---
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
        df = pd.concat(all_sheets.values(), ignore_index=True).fillna("")
        
        # Определяем колонки с размерами
        size_us_col = next((c for c in df.columns if "size" in c.lower() and "us" in c.lower()), None)
        size_eu_col = next((c for c in df.columns if "size" in c.lower() and "eu" in c.lower()), None)
        
        df["size_us"] = df[size_us_col] if size_us_col else ""
        df["size_eu"] = df[size_eu_col] if size_eu_col else ""

        df["model_clean"] = (
            df["model"].astype(str)
            .str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True)
            .str.strip()
        )

        # Группируем все размеры и цвета для одной модели
        grouped = (
            df.groupby(["brand", "model_clean", "color"], as_index=False)
            .agg({
                "price": "first",
                "description": "first",
                "size_us": lambda x: ", ".join(sorted(set(str(i) for i in x if i))),
                "size_eu": lambda x: ", ".join(sorted(set(str(i) for i in x if i))),
                "image": "first",
                "gender": "first",
            })
        )

        return grouped
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

# --- Основная функция ---
def main():
    # Кнопка назад
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Назад к каталогу", use_container_width=True):
            st.switch_page("main.py")

    # Проверяем, есть ли выбранный товар
    if "product_data" not in st.session_state:
        st.error("❌ Товар не найден. Вернитесь в каталог и выберите товар.")
        return

    row = st.session_state.product_data
    df = load_data()

    # Отбираем все варианты той же модели
    same_model_df = df[df["model_clean"] == row["model_clean"]]

    # Выбираем текущий цвет
    current_color = row["color"]
    current_item = same_model_df[same_model_df["color"] == current_color].iloc[0]

    st.markdown(f"## {row['brand']} {row['model_clean']} — {current_color.capitalize()}")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Показываем изображения
        all_images = []
        if current_item["image"]:
            image_names_list = str(current_item["image"]).strip().split()
            for img_name in image_names_list:
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    pattern = os.path.join(IMAGES_PATH, "**", f"{img_name}*{ext}")
                    files = glob.glob(pattern, recursive=True)
                    all_images.extend(files)

        all_images = list(dict.fromkeys(all_images))
        if not all_images:
            all_images = [os.path.join(IMAGES_PATH, "no_image.jpg")]

        for img_path in all_images:
            image_base64 = get_image_base64(img_path)
            st.markdown(
                f'<img src="data:image/jpeg;base64,{image_base64}" '
                f'style="width:100%; border-radius:12px; margin-bottom:15px; border:1px solid #eee;">',
                unsafe_allow_html=True
            )

    with col2:
        st.markdown(f"**Цена:** {int(current_item['price'])} ₸")
        st.markdown(f"**Пол:** {current_item['gender']}")
        st.markdown(f"**Цвет:** {current_item['color']}")
        st.markdown(f"**Описание:** {current_item['description']}")

        # Показываем размеры
        st.markdown("---")
        st.markdown("### 📏 Доступные размеры")
        if current_item["size_us"]:
            st.markdown(f"**US:** {current_item['size_us']}")
            st.markdown(f"**EU:** {current_item['size_eu']}")
        else:
            st.info("Размеры для этого цвета не указаны.")

        # Другие цвета
        other_colors = same_model_df[same_model_df["color"] != current_color]
        if not other_colors.empty:
            st.markdown("---")
            st.markdown("### 🎨 Другие цвета:")

            cols = st.columns(min(4, len(other_colors)))
            for col, (_, variant) in zip(cols, other_colors.iterrows()):
                with col:
                    img_path = get_image_path(variant["image"])
                    image_base64 = get_image_base64(img_path)
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{image_base64}" '
                        f'style="width:100%; border-radius:8px; border:1px solid #ddd;">',
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**{variant['color']}**")

if __name__ == "__main__":
    main()
