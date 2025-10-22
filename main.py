# main.py
import streamlit as st
import pandas as pd
import glob
import os
import re

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Пути ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_ROOT = "data/images"
NO_IMAGE = os.path.join(IMAGES_ROOT, "no_image.jpg")

# --- Таблица конверсии EU <-> US (пример) ---
EU_TO_US = {
    "39": "6", "39.5": "6.5", "40": "7", "40.5": "7.5",
    "41": "8", "42": "8.5", "42.5": "9", "43": "9.5",
    "44": "10", "44.5": "10.5", "45": "11", "46": "11.5", "46.5": "12"
}
US_TO_EU = {v: k for k, v in EU_TO_US.items()}

# --- Утилиты ---
def read_all_sheets(excel_path):
    """Читает все листы в Excel и объединяет в один DataFrame."""
    if not os.path.exists(excel_path):
        st.error(f"Не найден файл каталога: {excel_path}")
        return pd.DataFrame()
    xls = pd.ExcelFile(excel_path)
    frames = []
    for name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=name)
        df["sheet_brand"] = name  # если бренд не в колонке, поможет
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

def clean_model_name(model_raw):
    """Очищает model: убирает артикулы/скобки и обрезает лишнее в конце."""
    if pd.isna(model_raw):
        return ""
    s = str(model_raw)
    # убрать содержимое в круглых скобках и сами скобки
    s = re.sub(r"\(.*?\)", "", s)
    # убрать лишние тире/слеши в конце, и лишние пробелы
    s = re.sub(r"[-/]+$", "", s).strip()
    # если есть артикул через запятую — оставим левую часть (часто "Model (ART), extra")
    if "," in s:
        s = s.split(",")[0].strip()
    return s

def parse_sizes(sizes_raw):
    """Ожидает строку с размерами, возвращает список уникальных EU-значений в виде строк.
       Поддерживает разделители , ; / пробел."""
    if pd.isna(sizes_raw):
        return []
    s = str(sizes_raw)
    # заменить запятые/точки/слэши на запятую, убрать пробелы вокруг
    tokens = re.split(r"[;,/]\s*|\s{2,}|\s(?=\d)", s)
    sizes = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # захват числа с возможной дробной частью
        m = re.search(r"(\d{1,2}(?:[.,]\d)?)", t)
        if m:
            sizes.append(m.group(1).replace(",", "."))
    # уникальные, отсортированные по числу
    try:
        sizes = sorted(set(sizes), key=lambda x: float(x))
    except Exception:
        sizes = sorted(set(sizes))
    return sizes

def find_images_for_sku(sku):
    """Ищет все файлы вида <sku>_*.jpg|jpeg|png|webp во всех подпапках; возвращает отсортированный список путей."""
    if not sku:
        return []
    exts = ["jpg", "jpeg", "png", "webp"]
    files = []
    pattern_root = os.path.join(IMAGES_ROOT, "**", f"{sku}_*.*")
    # recursive glob and then filter extensions
    for p in glob.glob(pattern_root, recursive=True):
        ext = os.path.splitext(p)[1].lower().lstrip(".")
        if ext in exts:
            files.append(p)
    # try also exact name without suffix, e.g. sku.jpg
    for ext in exts:
        p2 = os.path.join(IMAGES_ROOT, "**", f"{sku}.{ext}")
        files += glob.glob(p2, recursive=True)
    # sort by suffix number if exists (sku_1, sku_2)
    def sort_key(p):
        m = re.search(rf"{re.escape(sku)}[_\-]?(\d+)", os.path.basename(p))
        return int(m.group(1)) if m else 0
    files = sorted(set(files), key=sort_key)
    return files

def ensure_session_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# --- Загрузка и подготовка данных ---
df = read_all_sheets(CATALOG_PATH)
if df.empty:
    st.stop()

# нормализуем названия колонок (на случай разного регистра)
df.columns = [c.strip() for c in df.columns]

# Убедимся, что есть критические колонки; если что-то отсутствует — добавим пустые
for col in ("SKU","brand","model","gender","color","image","sizes","prices","description"):
    if col not in df.columns:
        df[col] = ""

# Заполним бренд из sheet_brand если brand пустой
df["brand"] = df["brand"].astype(str).fillna("")
df["brand"] = df.apply(lambda r: r["sheet_brand"] if not r["brand"].strip() else r["brand"], axis=1)

# Очистка модели (для фильтра — model_clean) — убрать артикулы/скобки
df["model_clean"] = df["model"].apply(clean_model_name)

# sizes: превратить в список EU размеров
df["sizes_list"] = df["sizes"].apply(parse_sizes)

# prices: ожидаем соответствие размерам; оставим как текст (пользователь хочет показывать и пустые)
df["prices_text"] = df["prices"].astype(str).fillna("")

# gender, color: если в колонках уже есть — используем, иначе попытаемся извлечь из model
df["gender"] = df["gender"].astype(str).fillna("")
df["gender"] = df.apply(lambda r: (r["gender"] if r["gender"].strip() else
                                   ("men" if "men" in str(r["model"]).lower() else ("women" if "women" in str(r["model"]).lower() else "unisex"))), axis=1)
df["color"] = df["color"].astype(str).fillna("")
# если color пуст — пробуем взять цвет из model (white/black/...)
color_rx = r"(white|black|blue|red|green|pink|gray|brown|beige|navy)"
df["color"] = df.apply(lambda r: (r["color"] if r["color"].strip() else
                                  (re.search(color_rx, str(r["model"]).lower()).group(1) if re.search(color_rx, str(r["model"]).lower()) else "other")), axis=1)

# Исключаем строки без SKU или без model_clean? Покажем фильтр даже если цены пустые. Но для отображения карточки нужны SKU и model_clean.
df = df[df["SKU"].astype(str).str.strip() != ""]

# --- Фильтры интерфейса ---
st.divider()
st.markdown("### Фильтр каталога")

col1, col2, col3, col4 = st.columns([2,2,2,2])
brands = ["Все"] + sorted(df["brand"].dropna().astype(str).unique().tolist())
brand_sel = col1.selectbox("Бренд", brands)

# модели — показываем уникальные model_clean по выбранному бренду (без повторов)
if brand_sel == "Все":
    models_list = sorted(df["model_clean"].unique().tolist())
else:
    models_list = sorted(df[df["brand"] == brand_sel]["model_clean"].unique().tolist())
models_opts = ["Все"] + models_list
model_sel = col2.selectbox("Модель", models_opts)

# размеры (EU)
all_eu = sorted({s for lst in df["sizes_list"] for s in lst}, key=lambda x: float(x) if x and x.replace(".","",1).isdigit() else 999)
size_eu_sel = col3.selectbox("Размер (EU)", ["Все"] + all_eu)

# пол
gender_opts = ["Все"] + sorted(df["gender"].dropna().unique().tolist())
gender_sel = col4.selectbox("Пол", gender_opts)

# --- Применение фильтров: сначала по бренду, потом по модели, полу и размеру ---
filtered = df.copy()
if brand_sel != "Все":
    filtered = filtered[filtered["brand"] == brand_sel]
if model_sel != "Все":
    # показываем все строки у которых model_clean == model_sel (но это могут быть разные цвета)
    filtered = filtered[filtered["model_clean"] == model_sel]
if gender_sel != "Все":
    filtered = filtered[filtered["gender"] == gender_sel]
if size_eu_sel != "Все":
    filtered = filtered[filtered["sizes_list"].apply(lambda lst: size_eu_sel in lst)]

# --- Отображение карточек: по каждой комбинации model_clean + color показываем карточку ---
st.divider()
st.markdown("Каталог")

# группируем так: (brand, model_clean, color) — чтобы по одной карточке разных цветов
grouped = filtered.groupby(["brand","model_clean","color"], sort=False, dropna=False)

num_cols = 4
rows = []
items = []
for (brand, model_clean, color), group in grouped:
    # возьмём representative row (первую строку) для этой комбинации
    rep = group.iloc[0]
    sku = str(rep["SKU"])
    sizes_list = rep["sizes_list"] if isinstance(rep["sizes_list"], list) else []
    prices_text = rep["prices_text"]
    description = rep.get("description", "") or ""
    # image reference may be in column 'image' (base name) — otherwise use SKU searching
    image_base = str(rep.get("image", "")).strip()
    if image_base:
        # if image column contains filename(s) separated by ; or , -> pick first token
        image_base = re.split(r"[;,/]\s*", image_base)[0]
        # if image base has ext, try direct; else treat as base like SKU
        if os.path.splitext(image_base)[1]:
            # has extension: search for that exact file under images
            found = glob.glob(os.path.join(IMAGES_ROOT, "**", image_base), recursive=True)
            images = found or []
        else:
            images = find_images_for_sku(image_base) or find_images_for_sku(sku)
    else:
        images = find_images_for_sku(sku)
    if not images:
        images = [NO_IMAGE]

    items.append({
        "brand": brand,
        "model_clean": model_clean,
        "color": color,
        "sku": sku,
        "sizes": sizes_list,
        "prices_text": prices_text,
        "description": description,
        "images": images
    })

# карточки в сетке
if not items:
    st.info("Товары по фильтру не найдены.")
else:
    for i in range(0, len(items), num_cols):
        cols = st.columns(num_cols)
        for col, item in zip(cols, items[i:i+num_cols]):
            with col:
                # session index key per SKU+color to track which image is visible
                key_idx = f"idx_{item['sku']}_{item['color']}"
                ensure_session_key(key_idx, 0)
                idx = st.session_state[key_idx]

                # image display
                img_list = item["images"]
                img_path = img_list[idx] if idx < len(img_list) else img_list[0]
                # Show image (use stretch)
                try:
                    st.image(img_path, use_column_width='always')
                except Exception:
                    # fallback to no image
                    st.image(NO_IMAGE, use_column_width='always')

                # arrows
                cols_ar = st.columns([1,4,1])
                with cols_ar[0]:
                    if st.button("◀", key=f"prev_{item['sku']}_{item['color']}"):
                        if st.session_state[key_idx] > 0:
                            st.session_state[key_idx] -= 1
                with cols_ar[2]:
                    if st.button("▶", key=f"next_{item['sku']}_{item['color']}"):
                        if st.session_state[key_idx] < len(img_list)-1:
                            st.session_state[key_idx] += 1

                st.markdown(f"**{item['brand']} {item['model_clean']}**")
                st.markdown(f"*{item['color'].capitalize()}*")
                # sizes: show EU and mapped US in row
                if item["sizes"]:
                    sizes_eu = ", ".join(item["sizes"])
                    sizes_us = ", ".join([US_TO_EU.get(s, "") for s in item["sizes"]])
                    st.markdown(f"Размеры (EU): {sizes_eu}")
                    st.markdown(f"Размеры (US): {sizes_us}")
                else:
                    st.markdown("Размеры: —")

                if item["prices_text"] and item["prices_text"].strip() != "":
                    st.markdown(f"**Цена:** {item['prices_text']}")
                else:
                    st.markdown("**Цена:** —")

                if item["description"]:
                    st.markdown(item["description"])
                # кнопка "Добавить в корзину" (пока просто уведомление)
                if st.button("Добавить в корзину", key=f"add_{item['sku']}_{item['color']}"):
                    st.success(f"Товар {item['brand']} {item['model_clean']} ({item['color']}) добавлен в корзину (тест).")

st.divider()
st.caption("© DENE Store")
