import streamlit as st
import pandas as pd
import glob
import os
import re

# --- Page config (дизайн сохраняем как было) ---
st.set_page_config(page_title="DENE Store", layout="wide")

# Обложка и заголовок (не меняем дизайн)
st.image("data/images/banner.jpg", width="stretch")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>",
            unsafe_allow_html=True)

# Пути
BASE_DIR = os.path.dirname(__file__)
CATALOG_PATH = os.path.join(BASE_DIR, "data", "catalog.xlsx")
IMAGES_ROOT = os.path.join(BASE_DIR, "data", "images")
NO_IMAGE_PATH = os.path.join(IMAGES_ROOT, "no_image.jpg")

# Поддерживаемые расширения образов
IMG_EXTS = ("*.jpg", "*.jpeg", "*.png", "*.webp")

# --- Вспомогательные функции ---
def find_images_for_token(token):
    """Ищет файлы, содержащие token в имени во всех подпапках images; возвращает отсортированный список путей."""
    if not token or str(token).strip() == "":
        return []
    token = str(token).strip()
    matches = []
    for ext in IMG_EXTS:
        pattern = os.path.join(IMAGES_ROOT, "**", f"*{token}*{ext[1:]}" )  # ext like '*.jpg' -> '.jpg'
        # using glob with recursive True
        matches += glob.glob(os.path.join(IMAGES_ROOT, "**", f"*{token}*.*"), recursive=True)
    # Filter unique and keep common image extensions only
    filtered = []
    for p in matches:
        lower = p.lower()
        if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
            filtered.append(p)
    # Deduplicate and sort (by filename to get order like sku_1, sku_2)
    filtered = sorted(list(dict.fromkeys(filtered)))
    return filtered

def image_for_row(row):
    """Определяет список изображений для строки: сначала по колонке image, затем по SKU, возвращает список или fallback."""
    imgs = []
    # Если в колонке image указаны имена через запятую — поддерживаем (например "100200_1,100200_2")
    img_token = ""
    if "image" in row and str(row["image"]).strip():
        img_token = str(row["image"]).strip()
    # попробуем искать по image token (может быть несколько, разделённых запятой/пробелами)
    if img_token:
        # если несколько токенов разделены запятой
        tokens = re.split(r"[,\s;]+", img_token)
        for t in tokens:
            if not t:
                continue
            found = find_images_for_token(t)
            if found:
                imgs.extend(found)
    # если не нашли, пробуем по SKU (часть имени)
    if not imgs and "SKU" in row and str(row["SKU"]).strip():
        imgs = find_images_for_token(str(row["SKU"]).strip())
    # uniq
    imgs = list(dict.fromkeys(imgs))
    if not imgs:
        return [NO_IMAGE_PATH]
    return imgs

def clean_model_name(name):
    """Убирает содержимое в скобках и артикулы; возвращает короткое имя модели."""
    if not name or str(name).strip() == "":
        return ""
    s = str(name)
    # удалить части в скобках
    s = re.sub(r"\(.*?\)", "", s).strip()
    # удалить лишние пробелы
    s = re.sub(r"\s{2,}", " ", s)
    return s

def ensure_session_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# --- Загрузка всех листов (каждый лист — бренд) ---
@st.cache_data(show_spinner=False)
def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return pd.DataFrame()
    try:
        xls = pd.ExcelFile(CATALOG_PATH)
    except Exception:
        # Попытка прочитать как старый формат
        xls = pd.ExcelFile(CATALOG_PATH)
    frames = []
    for sheet in xls.sheet_names:
        df_sheet = pd.read_excel(xls, sheet_name=sheet)
        # Нормализуем имена колонок в нижний регистр и без BOM пробелов
        df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
        frames.append(df_sheet)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True, sort=False).fillna("")
    # Убедимся, что есть необходимые колонки; если нет — создаём
    for col in ("SKU","brand","model","gender","color","image","sizes","prices","description"):
        if col not in df.columns:
            df[col] = ""
    # Приводим к строкам
    df["SKU"] = df["SKU"].astype(str).str.strip()
    df["brand"] = df["brand"].astype(str).str.strip()
    df["model_raw"] = df["model"].astype(str).str.strip()
    # model_clean — без скобок/артикулов
    df["model_clean"] = df["model_raw"].apply(clean_model_name)
    # sizes, prices — оставляем как строки; если массивы через запятую — позже можно парсить
    df["sizes"] = df["sizes"].astype(str)
    df["prices"] = df["prices"].astype(str)
    # gender и color — уже есть в колонках, но если пусто — попытаемся из model_raw догадаться
    df["gender"] = df["gender"].astype(str).fillna("").apply(lambda x: x if x else (
        "men" if "men" in str(x).lower() else ""
    ))
    # description
    if "description" not in df.columns:
        df["description"] = ""
    # Фильтруем: продукты без SKU или без model_clean допускаются (нужно по задаче — но можно исключать пустые модели)
    return df

# Загружаем
df = load_catalog()

if df.empty:
    st.warning("Каталог пуст или не найден файл data/catalog.xlsx. Проверьте путь и загрузите файл.")
    st.stop()

# --- Фильтры (как было) ---
st.divider()
# верх: фильтры колонками — не меняем визуально
col1, col2, col3, col4, col5, col6 = st.columns(6)

brands = sorted([b for b in df["brand"].unique().tolist() if b])
brand_filter = col1.selectbox("Бренд", ["Все"] + brands)
# модели: показываем уникальные model_clean для выбранного бренда, без дублей
if brand_filter == "Все":
    models_list = sorted({m for m in df["model_clean"].unique().tolist() if m})
else:
    models_list = sorted({m for m in df[df["brand"] == brand_filter]["model_clean"].unique().tolist() if m})
model_filter = col2.selectbox("Модель", ["Все"] + models_list)

# Для размеров возьмём единый список: из колонки sizes, где значения могут быть "42,43,44" или "EU:42;US:9"
# Сейчас отображаем raw варианты — пользователь просил показывать фильтр по размерам (EU и US).
# Простая стратегия: собрать все числовые токены в колонке sizes и из model_raw.
size_tokens = set()
for s in df["sizes"].astype(str).tolist() + df["model_raw"].astype(str).tolist():
    for m in re.findall(r"(\d{1,2}(?:[.,]\d)?)", s):
        size_tokens.add(m.replace(",", "."))
sizes_sorted = sorted(size_tokens, key=lambda x: float(x) if x.replace(".", "", 1).isdigit() else 999)
size_filter = col3.selectbox("Размер (EU/US)", ["Все"] + sizes_sorted)

gender_opts = ["Все"] + sorted({g for g in df["gender"].astype(str).tolist() if g} | {"men","women","unisex"})
gender_filter = col4.selectbox("Пол", gender_opts)

color_opts = ["Все"] + sorted({c for c in df["color"].astype(str).tolist() if c})
color_filter = col5.selectbox("Цвет", color_opts)

st.divider()

# --- Применяем фильтры (не меняем внешний вид) ---
filtered = df.copy()
if brand_filter != "Все":
    filtered = filtered[filtered["brand"] == brand_filter]
if model_filter != "Все":
    filtered = filtered[filtered["model_clean"] == model_filter]
if size_filter != "Все":
    # фильтруем по вхождению токена размера в sizes или model_raw
    filtered = filtered[filtered["sizes"].str.contains(re.escape(size_filter)) | filtered["model_raw"].str.contains(re.escape(size_filter))]
if gender_filter != "Все":
    filtered = filtered[filtered["gender"].str.lower() == gender_filter.lower()]
if color_filter != "Все":
    filtered = filtered[filtered["color"].str.lower() == color_filter.lower()]

# --- Сетка карточек товаров (сохраняем стили как у тебя) ---
st.markdown("## Каталог товаров")

num_cols = 4
rows = [filtered.iloc[i:i+num_cols] for i in range(0, len(filtered), num_cols)]

# Инициализация сессионных счётчиков для картинок по SKU (чтобы стрелки работали)
for sku in filtered["SKU"].unique().tolist():
    key = f"img_idx_{sku}"
    ensure_session_key(key, 0)

for row_df in rows:
    cols = st.columns(num_cols)
    for col, (_, row) in zip(cols, row_df.iterrows()):
        with col:
            sku = str(row["SKU"])
            images = image_for_row(row)  # список путей
            # session key
            key = f"img_idx_{sku}"
            ensure_session_key(key, 0)
            idx = st.session_state[key]
            if idx < 0 or idx >= len(images):
                st.session_state[key] = 0
                idx = 0

            # Отрисовка карточки — не менять дизайн, только добавить стрелки вокруг картинки
            left_col, mid_col, right_col = st.columns([1, 6, 1])
            with left_col:
                if st.button("◀", key=f"left_{sku}"):
                    st.session_state[key] = max(0, st.session_state[key] - 1)
            with mid_col:
                # показываем изображение (используем путь, Streamlit сам покажет webp/jpg/png)
                image_path = images[st.session_state[key]] if images else NO_IMAGE_PATH
                st.image(image_path, width="stretch")
            with right_col:
                if st.button("▶", key=f"right_{sku}"):
                    st.session_state[key] = min(len(images)-1, st.session_state[key] + 1)

            # Текстовая часть карточки (в твоём стиле)
            brand = row.get("brand", "")
            model_clean = row.get("model_clean", "")
            color = row.get("color", "")
            # размеры и цены выводим как есть (если нет — не показываем)
            sizes = row.get("sizes", "")
            prices = row.get("prices", "")
            description = row.get("description", "")

            st.markdown(
                f"""
                <div style="
                    border:1px solid #eee;
                    border-radius:16px;
                    padding:10px;
                    margin-bottom:14px;
                    background-color:#fff;
                ">
                    <h4 style="margin:6px 0 4px 0;">{brand} {model_clean}</h4>
                    <p style="color:gray;font-size:13px;margin:0;">{color}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if sizes and str(sizes).strip():
                st.markdown(f"<p style='font-size:14px;color:#333;margin:0;'>Размеры: {sizes}</p>", unsafe_allow_html=True)
            if prices and str(prices).strip():
                st.markdown(f"<p style='font-weight:bold;font-size:16px;margin-top:6px;'>{prices} ₸</p>", unsafe_allow_html=True)
            if description and str(description).strip():
                st.markdown(f"<p style='font-size:13px;color:#555'>{description}</p>", unsafe_allow_html=True)

st.divider()
st.caption("© DENE Store 2025")
