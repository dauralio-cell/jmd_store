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
        df_list = []
        for sheet_data in all_sheets.values():
            df_list.append(sheet_data)
        df = pd.concat(df_list, ignore_index=True)
        df = df.fillna("")
        
        # --- ДОБАВЛЕНО: обработка структуры модели и цветов ---
        df["model"] = df["model"].ffill()
        df["color"] = df["color"].ffill()

        # --- Группируем по модели и цвету ---
        group_cols = ["brand", "model", "color", "gender", "price", "description", "image"]
        df = (
            df.groupby(group_cols, dropna=False)
              .agg({
                  "size_us": lambda x: ", ".join(sorted(set(str(i) for i in x if i))),
                  "size_eu": lambda x: ", ".join(sorted(set(str(i) for i in x if i))),
              })
              .reset_index()
        )

        # Та же обработка данных что и в основном файле
        df["model_clean"] = (
            df["model"]
            .str.replace(r"\d{1,2}(\.\d)?(US|EU)", "", regex=True)
            .str.strip()
        )
        
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

def main():
    # Кнопка назад вверху
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Назад к каталогу", use_container_width=True):
            st.switch_page("main.py")
    
    # Получаем данные товара из session_state
    if "product_data" not in st.session_state:
        st.error("Товар не найден. Вернитесь в каталог и выберите товар.")
        return
    
    row = st.session_state.product_data
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Все изображения товара
        all_images = []
        if row["image"]:
            image_names_list = str(row["image"]).strip().split()
            for img_name in image_names_list:
                for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    pattern = os.path.join(IMAGES_PATH, "**", f"{img_name}*{ext}")
                    files = glob.glob(pattern, recursive=True)
                    all_images.extend(files)
        
        all_images = list(dict.fromkeys(all_images))
        
        if not all_images:
            all_images = [os.path.join(IMAGES_PATH, "no_image.jpg")]

        # Показываем все изображения
        for img_path in all_images:
            try:
                image_base64 = get_image_base64(img_path)
                st.markdown(
                    f'<img src="data:image/jpeg;base64,{image_base64}" style="width:100%; border-radius:12px; margin-bottom:20px; border: 1px solid #eee;">', 
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Ошибка загрузки изображения: {e}")
    
    with col2:
        st.markdown(f"# {row['brand']} {row['model_clean']}")
        st.markdown(f"**Цена:** {int(row['price'])} ₸")
        st.markdown(f"**Размеры:** US {row['size_us'] or '-'} | EU {row['size_eu'] or '-'}")
        st.markdown(f"**Пол:** {row['gender']}")
        st.markdown(f"**Цвет:** {row['color']}")
        st.markdown(f"**Описание:** {row['description']}")
        
        # Загружаем все данные для цветовых вариантов
        df = load_data()
        if not df.empty:
            # Цветовые варианты
            color_variants = df[df["model_clean"] == row["model_clean"]].drop_duplicates("color")
            if len(color_variants) > 1:
                st.markdown("---")
                st.markdown("**Другие цвета:**")
                
                # Показываем варианты цвета в строках по 4
                num_cols = 4
                color_rows = [color_variants.iloc[i:i + num_cols] for i in range(0, len(color_variants), num_cols)]
                
                for color_row in color_rows:
                    cols = st.columns(num_cols)
                    for col_idx, (col, (_, variant)) in enumerate(zip(cols, color_row.iterrows())):
                        with col:
                            img_path = get_image_path(variant["image"])
                            try:
                                image_base64 = get_image_base64(img_path)
                                st.markdown(
                                    f'<img src="data:image/jpeg;base64,{image_base64}" style="width:100%; border-radius:8px; border: 1px solid #ddd;">', 
                                    unsafe_allow_html=True
                                )
                                st.markdown(f"**{variant['color']}**")
                                st.markdown(f"<span style='font-size:13px;color:gray;'>US {variant['size_us']}</span>", unsafe_allow_html=True)
                            except Exception:
                                st.error("Ошибка загрузки изображения")

if __name__ == "__main__":
    main()
