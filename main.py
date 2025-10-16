import streamlit as st
import pandas as pd
import re

# --- Обложка ---
st.image("data/images/banner.jpg", use_container_width=True)

# --- Заголовок ---
st.markdown(
    """
    <style>
    .welcome-text {
        text-align: center;
        white-space: nowrap;
        font-weight: 600;
        margin-top: 10px;
        font-size: 2rem;
    }

    @media (max-width: 768px) {
        .welcome-text {
            font-size: 1.5rem;
        }
    }

    @media (max-width: 480px) {
        .welcome-text {
            font-size: 1.2rem;
        }
    }
    </style>

    <h2 class="welcome-text">DENE Store. Добро пожаловать!</h2>
    """,
    unsafe_allow_html=True
)

# --- Загрузка данных ---
@st.cache_data
def load_data():
    df = pd.read_excel("data/catalog.xlsx")
    df = df.fillna("")

    # --- Разбор model ---
    df["brand"] = df["brand"].str.strip()

    # Извлекаем размер (например, 6.5, 42, 43.5)
    df["size"] = df["model"].apply(lambda x: re.search(r"\b\d{1,2}(\.\d)?\b", str(x)).group(0) if re.search(r"\b\d{1,2}(\.\d)?\b", str(x)) else "")

    # Извлекаем пол (men, women, kids и т.п.)
    df["gender"] = df["model"].apply(lambda x: "men" if "men" in str(x).lower() else ("women" if "women" in str(x).lower() else ""))

    # Извлекаем цвет (по словам типа white, black, red, blue и т.д.)
    colors = ["white", "black", "red", "blue", "green", "grey", "pink", "yellow", "brown", "beige", "purple", "orange"]
    df["color"] = df["model"].apply(lambda x: next((c for c in colors if c in str(x).lower()), ""))

    # Извлекаем название модели без бренда, размера и пола
    def clean_model(text):
        t = str(text)
        t = re.sub(r"(?i)\b(men|women|kids)\b", "", t)
        t = re.sub(r"\b\d{1,2}(\.\d)?\b", "", t)
        t = re.sub(r"\b(" + "|".join(colors) + r")\b", "", t, flags=re.IGNORECASE)
        return t.replace("  ", " ").strip()

    df["model_clean"] = df["model"].apply(clean_model)
    return df

df = load_data()

# --- Фильтры ---
st.sidebar.header("Фильтр товаров")

brands = ["Все"] + sorted(df["brand"].unique().tolist())
selected_brand = st.sidebar.selectbox("Бренд", brands)

# Появляется список моделей только после выбора бренда
if selected_brand != "Все":
    models = ["Все"] + sorted(df[df["brand"] == selected_brand]["model_clean"].unique().tolist())
else:
    models = ["Все"] + sorted(df["model_clean"].unique().tolist())
selected_model = st.sidebar.selectbox("Модель", models)

sizes = ["Все"] + sorted(df["size"].unique().tolist(), key=lambda x: (float(x) if x else 0))
selected_size = st.sidebar.selectbox("Размер", sizes)

genders = ["Все"] + sorted([g for g in df["gender"].unique() if g])
selected_gender = st.sidebar.selectbox("Пол", genders)

colors = ["Все"] + sorted([c for c in df["color"].unique() if c])
selected_color = st.sidebar.selectbox("Цвет", colors)

# --- Применение фильтров ---
filtered = df.copy()
if selected_brand != "Все":
    filtered = filtered[filtered["brand"] == selected_brand]
if selected_model != "Все":
    filtered = filtered[filtered["model_clean"] == selected_model]
if selected_size != "Все":
    filtered = filtered[filtered["size"] == selected_size]
if selected_gender != "Все":
    filtered = filtered[filtered["gender"] == selected_gender]
if selected_color != "Все":
    filtered = filtered[filtered["color"] == selected_color]

# --- Отображение каталога ---
st.markdown("### Каталог товаров")

if filtered.empty:
    st.info("Товары по выбранным параметрам не найдены 😢")
else:
    cols = st.columns(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with cols[i % 3]:
            image_path = f"data/images/{row['SKU']}.jpg"
            st.image(image_path, use_container_width=True, caption=row["model_clean"])
            st.write(f"**{row['brand']}** — {row['model_clean']}")
            st.write(f"💰 Цена: {int(row['price'])} ₸")
            st.button("🛒 Добавить в корзину", key=f"btn_{i}")
