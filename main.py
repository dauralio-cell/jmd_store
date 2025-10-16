import streamlit as st
import pandas as pd
import re
import os

# --- Путь к файлу ---
file_path = "data/catalog.xlsx"

# --- Загрузка данных ---
if not os.path.exists(file_path):
    st.error(f"❌ Файл не найден: {file_path}")
else:
    df = pd.read_excel(file_path)

    st.title("🛍 Каталог товаров")

    # --- Преобразуем preorder ---
    df["status"] = df["preorder"].apply(lambda x: "🕓 Предзаказ" if str(x).lower() == "yes" else "✅ В наличии")

    # --- Извлекаем размер и пол из model ---
    def extract_size(text):
        if not isinstance(text, str):
            return None
        match = re.search(r"\b(\d{2,3})\b", text)  # ищем размер (например, 38, 42)
        return match.group(1) if match else None

    def extract_gender(text):
        if not isinstance(text, str):
            return None
        text = text.lower()
        if "men" in text or "man" in text:
            return "Мужской"
        elif "women" in text or "woman" in text:
            return "Женский"
        elif "kids" in text or "child" in text:
            return "Детский"
        elif "unisex" in text:
            return "Унисекс"
        return "Не указан"

    df["size"] = df["model"].apply(extract_size)
    df["gender"] = df["model"].apply(extract_gender)

    # --- Боковая панель фильтров ---
    st.sidebar.header("🔍 Фильтр")
    search_model = st.sidebar.text_input("Поиск по названию модели")
    brand_filter = st.sidebar.multiselect("Бренд", sorted(df["brand"].dropna().unique()))
    size_filter = st.sidebar.multiselect("Размер", sorted(df["size"].dropna().unique()))
    gender_filter = st.sidebar.multiselect("Пол", sorted(df["gender"].dropna().unique()))
    stock_filter = st.sidebar.multiselect("Наличие", ["✅ В наличии", "🕓 Предзаказ"])

    # --- Применяем фильтры ---
    filtered = df.copy()

    if search_model:
        filtered = filtered[filtered["model"].str.contains(search_model, case=False, na=False)]
    if brand_filter:
        filtered = filtered[filtered["brand"].isin(brand_filter)]
    if size_filter:
        filtered = filtered[filtered["size"].isin(size_filter)]
    if gender_filter:
        filtered = filtered[filtered["gender"].isin(gender_filter)]
    if stock_filter:
        filtered = filtered[filtered["status"].isin(stock_filter)]

    # --- Вывод карточек ---
    if filtered.empty:
        st.warning("❌ Товары не найдены по выбранным фильтрам.")
    else:
        for _, row in filtered.iterrows():
            with st.container():
                st.subheader(row["model"])
                st.write(f"**Бренд:** {row['brand']}")
                st.write(f"**Артикул (SKU):** {row['SKU']}")
                st.write(f"**Пол:** {row['gender']}")
                st.write(f"**Размер:** {row['size'] if row['size'] else '—'}")
                st.write(f"**Статус:** {row['status']}")
                st.write(f"💰 **Цена:** {row['price']}")

                if st.button(f"🛒 Добавить в корзину ({row['SKU']})", key=row["SKU"]):
                    st.success(f"{row['model']} добавлен в корзину ✅")
                st.divider()
