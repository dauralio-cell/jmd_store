# main.py
import streamlit as st
import pandas as pd
import os
import glob
from PIL import Image

# ----------------------
# Настройки
# ----------------------
st.set_page_config(page_title="JMD Store", layout="wide")
DATA_DIR = "data"
IMAGE_DIR = os.path.join(DATA_DIR, "images")
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.xlsx")
PLACEHOLDER = os.path.join(IMAGE_DIR, "no_image.jpg") if os.path.exists(os.path.join(IMAGE_DIR, "no_image.jpg")) else None

# ----------------------
# Вспомогательные функции
# ----------------------
def scan_images(image_dir):
    """Сканируем все файлы картинок и возвращаем dict: base_name_lower -> full_path"""
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif"]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(image_dir, "**", pat), recursive=True))
    image_map = {}
    for p in files:
        key = os.path.splitext(os.path.basename(p))[0].strip().lower()
        # если несколько файлов с одинаковым именем — оставим первый встретившийся
        if key not in image_map:
            image_map[key] = p
    return image_map

def first_existing_image(names_str, image_map):
    """names_str - строка типа '100001_1 100001_2' -> возвращаем список найденных путей (в порядке)"""
    if not names_str or str(names_str).strip() == "":
        return []
    out = []
    for nm in str(names_str).split():
        key = nm.strip().lower()
        if key in image_map:
            out.append(image_map[key])
    return out

def normalize_and_forward_fill(df):
    """Заполняем пустые ячейки предыдущими значениями для нужных столбцов"""
    cols_to_ffill = ["brand", "model", "gender", "color", "image", "price", "preorder", "in stock", "description"]
    # убедимся что все колонки есть
    for col in cols_to_ffill:
        if col not in df.columns:
            df[col] = ""
    # iterate rows and forward-fill by last seen
    last = {c: "" for c in cols_to_ffill}
    rows = []
    for _, r in df.iterrows():
        r = r.fillna("")  # ensure no NaN
        new = r.to_dict()
        for c in cols_to_ffill:
            val = str(new.get(c, "")).strip()
            if val == "":
                new[c] = last[c]
            else:
                new[c] = val
                last[c] = val
        rows.append(new)
    new_df = pd.DataFrame(rows)
    return new_df

# ----------------------
# Загрузка данных
# ----------------------
if not os.path.exists(CATALOG_PATH):
    st.error(f"Не найден файл {CATALOG_PATH}")
    st.stop()

# Load all sheets (each sheet -> brand)
xls = pd.ExcelFile(CATALOG_PATH)
dfs = []
for sheet_name in xls.sheet_names:
    sheet_df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
    # Если в листе нет колонки brand, проставим имя листа
    if "brand" not in sheet_df.columns.str.lower():
        sheet_df["brand"] = sheet_name
    dfs.append(sheet_df)

raw_df = pd.concat(dfs, ignore_index=True)
# Нормализуем заголовки
raw_df.columns = raw_df.columns.str.strip().str.lower()
raw_df = raw_df.fillna("")

# Приведём к ожидаемым колонкам и forward-fill по блокам
df_prepared = normalize_and_forward_fill(raw_df)

# Если size columns имеют другие имена, пробуем варианты:
if "size us" not in df_prepared.columns and "size" in df_prepared.columns:
    df_prepared["size us"] = df_prepared["size"]

# Сканируем картинки
image_map = scan_images(IMAGE_DIR)

# ----------------------
# Построение карточек: группировка по (brand, model, color)
# ----------------------
grouped_rows = []
group_cols = ["brand", "model", "gender", "color"]
if not all(c in df_prepared.columns for c in group_cols):
    st.error("В таблице отсутствуют обязательные колонки: brand / model / gender / color")
    st.stop()

for (brand, model, gender, color), group in df_prepared.groupby(group_cols, sort=False):
    # Собираем все уникальные image-строки в этой группе (обычно первая строка цвета содержит image)
    images_field = " ".join([str(x).strip() for x in group["image"].unique() if str(x).strip() != ""])
    # Собираем все размеры (US / EU) в списки
    sizes_us = [s for s in group["size us"].astype(str).tolist() if str(s).strip() != "" and str(s).strip() != "nan"]
    sizes_eu = [s for s in group.get("size eu", pd.Series([""] * len(group))).astype(str).tolist() if str(s).strip() != "" and str(s).strip() != "nan"]
    # price / preorder / in stock / description берем из первой строки в группе (она содержит их)
    first = group.iloc[0]
    price = first.get("price", "")
    preorder = first.get("preorder", "")
    in_stock = first.get("in stock", "")
    description = first.get("description", "")
    # соберём SKU-list (полезно)
    skus = group.get("sku", pd.Series([""] * len(group))).astype(str).tolist()
    grouped_rows.append({
        "brand": brand,
        "model": model,
        "gender": gender,
        "color": color,
        "images_field": images_field,
        "sizes_us": sorted(list(dict.fromkeys([s for s in sizes_us if s]))),
        "sizes_eu": sorted(list(dict.fromkeys([s for s in sizes_eu if s]))),
        "price": price,
        "preorder": preorder,
        "in_stock": in_stock,
        "description": description,
        "skus": skus
    })

cards_df = pd.DataFrame(grouped_rows)

# ----------------------
# Фильтры / Поиск
# ----------------------
st.markdown("")  # spacer
search_text = st.text_input("🔎 Поиск по бренду/модели/цвету").strip().lower()

col1, col2, col3, col4 = st.columns(4)
with col1:
    brands = ["Все"] + sorted(cards_df["brand"].dropna().unique().tolist())
    brand_sel = st.selectbox("Бренд", brands)
with col2:
    models = ["Все"] + sorted(cards_df["model"].dropna().unique().tolist())
    model_sel = st.selectbox("Модель", models)
with col3:
    genders = ["Все"] + sorted(cards_df["gender"].dropna().unique().tolist())
    gender_sel = st.selectbox("Пол", genders)
with col4:
    all_sizes = sorted({s for lst in cards_df["sizes_us"] for s in lst if s})
    sizes = ["Все"] + all_sizes
    size_sel = st.selectbox("Размер (US)", sizes)

# Применяем фильтры
filtered = cards_df.copy()
if brand_sel != "Все":
    filtered = filtered[filtered["brand"] == brand_sel]
if model_sel != "Все":
    filtered = filtered[filtered["model"] == model_sel]
if gender_sel != "Все":
    filtered = filtered[filtered["gender"] == gender_sel]
if size_sel != "Все":
    filtered = filtered[filtered["sizes_us"].apply(lambda lst: size_sel in lst)]

if search_text:
    filtered = filtered[filtered.apply(lambda r:
        search_text in str(r["brand"]).lower()
        or search_text in str(r["model"]).lower()
        or search_text in str(r["color"]).lower()
    , axis=1)]

st.markdown("---")

# ----------------------
# Карточки: сетка 4 на ряд
# ----------------------
if filtered.empty:
    st.info("По текущим фильтрам товары не найдены.")
else:
    cols = st.columns(4)
    for idx, r in filtered.reset_index(drop=True).iterrows():
        col = cols[idx % 4]
        with col:
            # получаем список существующих путей для images_field
            image_paths = first_existing_image(r["images_field"], image_map)
            if image_paths:
                # отображаем первую картинку
                try:
                    st.image(image_paths[0], use_container_width=True)
                except:
                    if PLACEHOLDER:
                        st.image(PLACEHOLDER, use_container_width=True)
                    else:
                        st.write("No image")
            else:
                if PLACEHOLDER:
                    st.image(PLACEHOLDER, use_container_width=True)
                else:
                    st.write("No image")

            st.markdown(f"**{r['brand']} — {r['model']}**")
            st.markdown(f"*Цвет:* {r['color']}")
            st.markdown(f"*Пол:* {r['gender']}")
            try:
                price_disp = int(float(r['price']))
            except:
                price_disp = r['price']
            st.markdown(f"**{price_disp} ₸**")

            in_stock_flag = str(r.get("in_stock", "")).strip().lower()
            if in_stock_flag in ["yes", "да", "в наличии", "true", "1"]:
                st.markdown("<p style='color:green;'>В наличии</p>", unsafe_allow_html=True)
            elif str(r.get("preorder", "")).strip().lower() in ["yes", "да", "true", "1"]:
                st.markdown("<p style='color:orange;'>Предзаказ</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:red;'>Нет в наличии</p>", unsafe_allow_html=True)

            # Кнопка "Подробнее" — открываем модальное окно через session_state
            if st.button("Подробнее", key=f"more_{idx}"):
                st.session_state["modal_target"] = {
                    "brand": r["brand"],
                    "model": r["model"],
                    "color": r["color"]
                }
                st.experimental_rerun()

# ----------------------
# Если открыт modal_target — показываем модальное окно
# ----------------------
if "modal_target" in st.session_state and st.session_state["modal_target"]:
    target = st.session_state["modal_target"]
    # найдём индекс соответствующей записи в filtered (по brand+model+color)
    match_idx = None
    filtered_list = filtered.reset_index(drop=True)
    for i, rr in filtered_list.iterrows():
        if (rr["brand"] == target["brand"] and rr["model"] == target["model"]
                and rr["color"] == target["color"]):
            match_idx = i
            break

    if match_idx is not None:
        prod = filtered_list.loc[match_idx]

        # Открываем modal
        with st.modal(f"{prod['brand']} — {prod['model']} ({prod['color']})"):
            # Галерея
            imgs = first_existing_image(prod["images_field"], image_map)
            if imgs:
                # показываем основную галерею (каждое изображение по очереди)
                for p in imgs:
                    try:
                        st.image(p, use_column_width=True)
                    except:
                        if PLACEHOLDER:
                            st.image(PLACEHOLDER, use_column_width=True)
                        else:
                            st.write("No image")
            else:
                if PLACEHOLDER:
                    st.image(PLACEHOLDER, use_column_width=True)
                else:
                    st.write("No image")

            # Информация и размеры
            st.markdown(f"**Цена:** {int(float(prod['price'])) if str(prod['price']) else prod['price']} ₸")
            in_stock_flag = str(prod.get("in_stock", "")).strip().lower()
            if in_stock_flag in ["yes", "да", "в наличии", "true", "1"]:
                st.markdown("<p style='color:green;'>В наличии</p>", unsafe_allow_html=True)
            elif str(prod.get("preorder", "")).strip().lower() in ["yes", "да", "true", "1"]:
                st.markdown("<p style='color:orange;'>Предзаказ</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:red;'>Нет в наличии</p>", unsafe_allow_html=True)

            # размеры
            sizes_us = prod.get("sizes_us", [])
            sizes_eu = prod.get("sizes_eu", [])
            if sizes_us:
                st.markdown("**Размеры (US):** " + ", ".join(map(str, sizes_us)))
            if sizes_eu:
                st.markdown("**Размеры (EU):** " + ", ".join(map(str, sizes_eu)))

            # описание
            if prod.get("description"):
                st.markdown("**Описание:**")
                st.write(prod.get("description"))

            st.markdown("---")
            # миниатюры других цветов той же модели
            same_model = filtered_list[filtered_list["model"] == prod["model"]]
            other_colors = same_model[same_model["color"] != prod["color"]]
            if not other_colors.empty:
                st.markdown("**Другие цвета:**")
                cols_thumb = st.columns(max(1, min(6, len(other_colors))))
                for i2, (_, rc) in enumerate(other_colors.iterrows()):
                    with cols_thumb[i2 % len(cols_thumb)]:
                        thumb_imgs = first_existing_image(rc["images_field"], image_map)
                        if thumb_imgs:
                            try:
                                st.image(thumb_imgs[0], width=120)
                            except:
                                if PLACEHOLDER:
                                    st.image(PLACEHOLDER, width=120)
                        else:
                            if PLACEHOLDER:
                                st.image(PLACEHOLDER, width=120)

                        # при нажатии миниатюры — открываем modal для этого цвета
                        if st.button(f"Открыть: {rc['color']}", key=f"thumb_{i2}"):
                            st.session_state["modal_target"] = {"brand": rc["brand"], "model": rc["model"], "color": rc["color"]}
                            st.experimental_rerun()

            # кнопка закрыть
            if st.button("Закрыть модальное окно"):
                st.session_state["modal_target"] = None
                st.experimental_rerun()
    else:
        # не найдено — очистим
        st.session_state["modal_target"] = None
