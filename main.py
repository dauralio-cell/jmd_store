import streamlit as st
import pandas as pd
import os
import glob
import streamlit.components.v1 as components

st.set_page_config(page_title="JMD Store", layout="wide")

# === Загрузка данных из Excel ===
@st.cache_data
def load_data():
    excel_path = "data/catalog.xlsx"
    xls = pd.ExcelFile(excel_path)
    all_data = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df["brand"] = sheet_name
        all_data.append(df)
    df = pd.concat(all_data, ignore_index=True)
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# Проверяем наличие нужных колонок
for col in ["model", "gender", "color", "image"]:
    if col not in df.columns:
        st.error(f"Отсутствует колонка: {col}")
        st.stop()

# === Функция поиска изображений ===
def find_images(image_names):
    image_files = []
    for name in str(image_names).split():
        patterns = [f"data/images/**/*{name}*.{ext}" for ext in ["jpg", "jpeg", "png", "webp"]]
        for pattern in patterns:
            matches = glob.glob(pattern, recursive=True)
            image_files.extend(matches)
    return sorted(image_files)

# === Сайдбар фильтры ===
st.sidebar.header("Фильтры")
brand_filter = st.sidebar.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique()))
gender_filter = st.sidebar.selectbox("Пол", ["Все"] + sorted(df["gender"].dropna().unique()))
color_filter = st.sidebar.selectbox("Цвет", ["Все"] + sorted(df["color"].dropna().unique()))

size_eu_col = next((c for c in df.columns if "size eu" in c.lower()), None)
size_us_col = next((c for c in df.columns if "size us" in c.lower()), None)

size_filter = "Все"
if size_eu_col:
    all_sizes = {s.strip() for sub in df[size_eu_col].astype(str).str.split(",") for s in sub if s.strip()}
    size_filter = st.sidebar.selectbox("Размер (EU)", ["Все"] + sorted(all_sizes))

# === Применение фильтров ===
filtered = df.copy()
if brand_filter != "Все":
    filtered = filtered[filtered["brand"] == brand_filter]
if gender_filter != "Все":
    filtered = filtered[filtered["gender"] == gender_filter]
if color_filter != "Все":
    filtered = filtered[filtered["color"] == color_filter]
if size_filter != "Все" and size_eu_col:
    filtered = filtered[filtered[size_eu_col].astype(str).str.contains(size_filter)]

# === Отображение карточек ===
st.markdown("<h2 style='text-align:center;margin-top:10px;'>Каталог</h2>", unsafe_allow_html=True)

cols = st.columns(3)

for i, (_, row) in enumerate(filtered.iterrows()):
    col = cols[i % 3]
    with col:
        images = find_images(row["image"])
        if not images:
            st.warning(f"Нет фото для {row['image']}")
            continue

        sku = str(row.get("sku", row["image"]))
        if "img_index" not in st.session_state:
            st.session_state["img_index"] = {}
        if sku not in st.session_state["img_index"]:
            st.session_state["img_index"][sku] = 0

        current_index = st.session_state["img_index"][sku]
        img_path = images[current_index]

        # === HTML-блок со свайпом и стрелками ===
        html_code = f"""
        <div style="position:relative;text-align:center;">
            <img id="img_{sku}" src="{img_path}" style="width:100%;border-radius:8px;">
            <button id="left_{sku}" style="position:absolute;left:5px;top:45%;background:none;border:none;font-size:22px;color:black;">◀</button>
            <button id="right_{sku}" style="position:absolute;right:5px;top:45%;background:none;border:none;font-size:22px;color:black;">▶</button>
        </div>
        <script>
        const imgs_{sku} = {images};
        let index_{sku} = {current_index};
        const imgElem_{sku} = document.getElementById("img_{sku}");
        const leftBtn_{sku} = document.getElementById("left_{sku}");
        const rightBtn_{sku} = document.getElementById("right_{sku}");

        function showImage_{sku}(idx) {{
            if (idx < 0) idx = imgs_{sku}.length - 1;
            if (idx >= imgs_{sku}.length) idx = 0;
            index_{sku} = idx;
            imgElem_{sku}.src = imgs_{sku}[index_{sku}];
        }}

        leftBtn_{sku}.onclick = () => showImage_{sku}(index_{sku}-1);
        rightBtn_{sku}.onclick = () => showImage_{sku}(index_{sku}+1);

        let touchstartX = 0;
        let touchendX = 0;
        imgElem_{sku}.addEventListener('touchstart', e => touchstartX = e.changedTouches[0].screenX);
        imgElem_{sku}.addEventListener('touchend', e => {{
            touchendX = e.changedTouches[0].screenX;
            if (touchendX < touchstartX - 50) showImage_{sku}(index_{sku}+1);
            if (touchendX > touchstartX + 50) showImage_{sku}(index_{sku}-1);
        }});
        </script>
        """

        components.html(html_code, height=300)

        st.markdown(
            f"""
            <h4 style="margin:10px 0 4px 0;">{row.get("model", "")}</h4>
            <p style="color:gray;font-size:13px;margin:0;">{row.get("color", "")}</p>
            <p style="font-size:14px;color:#555;">Размеры (EU): {row.get(size_eu_col, "")}</p>
            <p style="font-size:14px;color:#555;">Размеры (US): {row.get(size_us_col, "")}</p>
            <p style="font-weight:bold;font-size:16px;margin-top:6px;">{row.get("price", "")} ₸</p>
            """,
            unsafe_allow_html=True
        )
