import streamlit as st
import pandas as pd

# --- Обложка сайта ---
st.image("data/images/banner.jpg", use_container_width=True)

# --- Заголовок ---
st.markdown(
    """
    <h1 style='text-align: center; font-size: 48px; margin-top: -30px;'>
        DENE Store. Добро пожаловать!
    </h1>
    """,
    unsafe_allow_html=True
)

# --- Загружаем данные ---
@st.cache_data
def load_data():
    df = pd.read_excel("data/catalog.xlsx")
    df = df.fillna("")
    return df

df = load_data()

# --- Фильтры ---
brands = ["Все"] + sorted(df["brand"].unique().tolist())
selected_brand = st.selectbox("Выберите бренд", brands)

# Парсим размер и пол из model
# Извлекаем размер (одно число, иногда с .5)
df["size"] = df["model"].str.extract(r'(\d{1,2}(?:\.\d)?)')[0]

# Извлекаем пол (men, women, kids, unisex)
df["gender"] = df["model"].str.extract(r'\b(men|women|kids|unisex)\b', expand=False).fillna("")

sizes = ["Все"] + sorted(df["size"].dropna().unique().tolist())
genders = ["Все"] + sorted(df["gender"].dropna().unique().tolist())

col1, col2 = st.columns(2)
with col1:
    selected_size = st.selectbox("Размер", sizes)
with col2:
    selected_gender = st.selectbox("Пол", genders)

# --- Фильтрация ---
filtered = df.copy()
if selected_brand != "Все":
    filtered = filtered[filtered["brand"] == selected_brand]
if selected_size != "Все":
    filtered = filtered[filtered["size"] == selected_size]
if selected_gender != "Все":
    filtered = filtered[filtered["gender"] == selected_gender]

# --- Отображение товаров ---
st.divider()
if len(filtered) == 0:
    st.warning("⚠️ Товары не найдены. Попробуйте изменить фильтры.")
else:
    cols = st.columns(3)
    for idx, (_, row) in enumerate(filtered.iterrows()):
        with cols[idx % 3]:
            st.image("https://via.placeholder.com/300x200?text=Фото+товара", use_container_width=True)
            st.markdown(f"**{row['model']}**")
            st.markdown(f"💸 Цена: **{int(row['price'])} ₸**")
            if st.button("🛒 Добавить в корзину", key=f"btn_{idx}"):
                st.success(f"{row['model']} добавлен в корзину!")

# --- Стили ---
st.markdown("""
    <style>
        .stButton>button {
            background-color: black;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
        }
        .stButton>button:hover {
            background-color: #444;
        }
    </style>
""", unsafe_allow_html=True)
