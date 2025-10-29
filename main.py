import streamlit as st
import pandas as pd
import glob
import os
import re
from PIL import Image

# --- Настройки страницы ---
st.set_page_config(page_title="DENE Store", layout="wide")

# --- Обложка (не меняем дизайн) ---
BANNER_PATH = "data/images/banner.jpg"
if os.path.exists(BANNER_PATH):
    st.image(BANNER_PATH, width="stretch")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

# --- Пути (при необходимости поменяй) ---
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_PATH = "data/images"
NO_IMAGE = os.path.join(IMAGES_PATH, "no_image.jpg")

# --- Сессия ---
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None

# --- Утилиты для имён/ключей ---
def safe_key(*parts):
    """Сформировать безопасный ключ для st.widgets (без пробелов/точек)."""
    raw = "_".join([str(x) for x in parts if x is not None])
    return re.sub(r'[^0-9A-Za-z_\-]', '_', raw)

# --- Функция поиска изображений ---
def find_images_by_names(image_names):
    """
    image_names: строка, содержит одно или несколько имён, разделённых пробелом или запятой.
    Имена — без расширения, например: 100001_1 100001_2
    Ищем по всем подпапкам любые расширения.
    """
    found = []
    if not image_names or pd.isna(image_names):
        return found
    # split by commas or whitespace
    tokens = re.split(r'[,\s]+', str(image_names).strip())
    for t in tokens:
        if not t:
            continue
        # search any extension
        pattern = os.path.join(IMAGES_PATH, "**", f"{t}.*")
        matches = glob.glob(pattern, recursive=True)
        # keep image-like files only (common extensions)
        matches = [m for m in matches if m.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'))]
        matches.sort()
        for m in matches:
            if m not in found:
                found.append(m)
    return found

# --- Если нужно — искать по SKU (тоже во всех подпапках) ---
def find_images_by_sku(sku):
    if not sku or pd.isna(sku):
        return []
    sku_str = str(sku).split('.')[0]  # иногда чтение даёт 100001.0
    pattern = os.path.join(IMAGES_PATH, "**", f"{sku_str}_*.*")
    matches = glob.glob(pattern, recursive=True)
    matches = [m for m in matches if m.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'))]
    matches.sort()
    return matches

# --- Загрузка каталога (все листы) ---
@st.cache_data(ttl=120)
def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return pd.DataFrame()
    try:
        xls = pd.read_excel(CATALOG_PATH, sheet_name=None)  # dict of DataFrames
        df_list = []
        for sheet_name, df_sheet in xls.items():
            df_sheet = df_sheet.copy()
            df_sheet['__sheet_name'] = sheet_name
            df_list.append(df_sheet)
        df = pd.concat(df_list, ignore_index=True, sort=False)
    except Exception as e:
        # fallback: try default sheet
        df = pd.read_excel(CATALOG_PATH)

    # нормализуем названия колонок (strip)
    df.columns = [str(c).strip() for c in df.columns]

    # приводим нужные колонки в единый вид (если отсутствуют, создаём)
    expected = ['sku', 'brand', 'model', 'gender', 'color', 'image', 'size US', 'size EU', 'price', 'description', 'preorder', 'in stock']
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    # модель без артикула в скобках
    df['model_clean'] = df['model'].astype(str).apply(lambda x: re.sub(r'\([^)]*\)', '', x).strip())

    # заполним сверху-вниз (если данные модели/бренда указаны только в первой строке группы)
    for col in ['brand', 'model', 'model_clean', 'gender', 'color', 'image', 'price', 'description', 'preorder', 'in stock']:
        df[col] = df[col].ffill()

    # приведение размеров: у тебя в одной строке может быть список размеров; приводим в списки
    # ожидаем: "size US" и "size EU" могут содержать через запятую или пробел - делаем списки
    def to_list_cell(v):
        if pd.isna(v) or str(v).strip() == "":
            return []
        s = str(v)
        parts = re.split(r'[,\s;]+', s.strip())
        parts = [p.strip() for p in parts if p.strip()]
        return parts

    df['sizes_us_list'] = df['size US'].apply(to_list_cell)
    df['sizes_eu_list'] = df['size EU'].apply(to_list_cell)

    # price может быть строкой с запятой — приводим к числу если возможно, иначе сохраняем пустым
    def to_price(v):
        try:
            if pd.isna(v) or str(v).strip() == "":
                return None
            s = str(v).replace(' ', '').replace(',', '.')
            return float(s)
        except:
            return None
    df['price_val'] = df['price'].apply(to_price)

    # убираем строки без бренда/модели (на всякий случай)
    df = df[df['brand'].astype(str).str.strip() != ""]
    df = df[df['model_clean'].astype(str).str.strip() != ""]

    df = df.reset_index(drop=True)
    return df

df = load_catalog()
if df.empty:
    st.error("Каталог пуст или файл не найден: data/catalog.xlsx")
    st.stop()

# --- Функция: найти изображений (image column first, затем SKU) ---
def collect_images_for_row(row):
    imgs = []
    # сначала по колонке image — она содержит имена без расширений (через пробел/запятую)
    imgs = find_images_by_names(row.get('image', ""))
    # затем по SKU (если не найдено)
    if not imgs:
        imgs = find_images_by_sku(row.get('sku', ""))
    # fallback
    if not imgs and os.path.exists(NO_IMAGE):
        imgs = [NO_IMAGE]
    return imgs

# --- Группируем: хотим по модели и цвету показывать одну карточку (в карточке — список размеров для этого цветового варианта) ---
def group_products(df):
    # группируем по brand, model_clean, color
    groups = []
    grouped = df.groupby(['brand', 'model_clean', 'color'], sort=False)
    for (brand, model_clean, color), g in grouped:
        first = g.iloc[0]
        sku = first.get('sku', "")
        image_field = first.get('image', "")
        gender = first.get('gender', "")
        description = first.get('description', "")
        preorder = first.get('preorder', "")
        in_stock = first.get('in stock', "")

        # sizes aggregated (unique) — берём все size EU и US из подстрок
        sizes_us = []
        sizes_eu = []
        prices_map = {}  # map size->price (if available)
        for _, r in g.iterrows():
            sizes_us += r.get('sizes_us_list', []) if isinstance(r.get('sizes_us_list', []), list) else []
            sizes_eu += r.get('sizes_eu_list', []) if isinstance(r.get('sizes_eu_list', []), list) else []
            p = r.get('price_val')
            # if p present and sizes available in this row, map sizes->price (best-effort)
            if p:
                for s in (r.get('sizes_eu_list') or []):
                    prices_map[str(s)] = p

        # unique, sorted heuristics
        sizes_us = sorted(set(sizes_us), key=lambda x: float(x) if re.match(r'^\d+(\.\d+)?$', x) else x)
        sizes_eu = sorted(set(sizes_eu), key=lambda x: float(x) if re.match(r'^\d+(\.\d+)?$', x) else x)

        groups.append({
            'brand': brand,
            'model_clean': model_clean,
            'color': color,
            'sku': sku,
            'image_field': image_field,
            'gender': gender,
            'description': description,
            'preorder': preorder,
            'in_stock': in_stock,
            'sizes_us': sizes_us,
            'sizes_eu': sizes_eu,
            'price_map': prices_map,
            'price': first.get('price_val')  # primary price if exists
        })
    return groups

groups = group_products(df)

# --- Сайдбар: корзина, поиск, настройки ---
with st.sidebar:
    st.header("Корзина")
    if not st.session_state.cart:
        st.info("Корзина пуста")
    else:
        total = 0
        for i, it in enumerate(st.session_state.cart):
            st.write(f"**{it['brand']} {it['model_clean']}** — {it['color']} — {it['size_eu']} EU — {it['price']} ₸")
            if st.button("Удалить", key=safe_key("rm", i)):
                st.session_state.cart.pop(i)
                st.experimental_rerun()
            total += float(it.get('price') or 0)
        st.markdown(f"**Итого: {int(total)} ₸**")
        if st.button("Оформить заказ"):
            st.success("Заказ принят — с вами свяжутся")

    st.markdown("---")
    st.header("Поиск")
    search_q = st.text_input("Поиск по названию или бренду")

    st.markdown("---")
    st.header("Настройки")
    items_per_page = st.slider("Товаров на страницу", 4, 32, 16)

# --- Фильтры сверху (как просили) ---
st.markdown("### Фильтр каталога")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    brands = ["Все"] + sorted({g['brand'] for g in groups if g['brand']})
    brand_filter = st.selectbox("Бренд", brands)
with col2:
    # модели зависят от бренда
    models_all = [g['model_clean'] for g in groups if (brand_filter == "Все" or g['brand'] == brand_filter)]
    models = ["Все"] + sorted(list(set(models_all)))
    model_filter = st.selectbox("Модель", models)
with col3:
    sizes_eu_all = sorted({s for g in groups for s in g['sizes_eu']})
    sizes_eu = ["Все"] + sizes_eu_all
    size_filter = st.selectbox("Размер (EU)", sizes_eu)
with col4:
    genders = ["Все"] + sorted({g['gender'] or "unisex" for g in groups})
    gender_filter = st.selectbox("Пол", genders)
with col5:
    colors_all = sorted({g['color'] for g in groups if g['color']})
    colors = ["Все"] + colors_all
    color_filter = st.selectbox("Цвет", colors)

# --- Применяем фильтры ---
filtered = groups
if brand_filter != "Все":
    filtered = [g for g in filtered if g['brand'] == brand_filter]
if model_filter != "Все":
    filtered = [g for g in filtered if g['model_clean'] == model_filter]
if size_filter != "Все":
    filtered = [g for g in filtered if size_filter in g['sizes_eu']]
if gender_filter != "Все":
    filtered = [g for g in filtered if (g['gender'] == gender_filter)]
if color_filter != "Все":
    filtered = [g for g in filtered if g['color'] == color_filter]
if search_q:
    sq = search_q.lower()
    filtered = [g for g in filtered if sq in g['brand'].lower() or sq in g['model_clean'].lower()]

# --- Отображение карточек (4 в ряд) ---
st.markdown("## Каталог")
if not filtered:
    st.warning("Товары не найдены")
else:
    num_cols = 4
    rows = [filtered[i:i+num_cols] for i in range(0, len(filtered), num_cols)]
    for row_idx, row_block in enumerate(rows):
        cols = st.columns(num_cols)
        for col_idx, prod in enumerate(row_block):
            with cols[col_idx]:
                key_base = safe_key(prod['brand'], prod['model_clean'], prod['color'], row_idx, col_idx)
                # контейнер карточки (HTML wrapper kept minimal to preserve style)
                st.markdown("""
                    <div style="border:1px solid #eee;border-radius:16px;padding:12px;margin-bottom:16px;background-color:#fff;box-shadow:0 2px 10px rgba(0,0,0,0.05);">
                    """, unsafe_allow_html=True)
                # images
                image_paths = collect_images_for_row({'image': prod['image_field'], 'sku': prod['sku']})
                # selected index state
                sel_key = f"sel_{key_base}"
                if sel_key not in st.session_state:
                    st.session_state[sel_key] = 0
                # main image (single)
                if image_paths:
                    img_to_show = image_paths[st.session_state[sel_key] % len(image_paths)]
                    try:
                        st.image(img_to_show, use_container_width=True)
                    except:
                        st.image(NO_IMAGE, use_container_width=True)
                else:
                    st.image(NO_IMAGE, use_container_width=True)
                # thumbnails and arrows
                if len(image_paths) > 1:
                    left_key = f"left_{key_base}"
                    right_key = f"right_{key_base}"
                    col_l, col_c, col_r = st.columns([1,6,1])
                    with col_l:
                        if st.button("◀", key=left_key):
                            st.session_state[sel_key] = (st.session_state[sel_key] - 1) % len(image_paths)
                            st.experimental_rerun()
                    with col_c:
                        # thumbnails
                        thumbs_cols = st.columns(min(4, len(image_paths)))
                        for t_idx, cthumb in enumerate(thumbs_cols):
                            with cthumb:
                                thumb_key = f"thumb_{key_base}_{t_idx}"
                                thumb_path = image_paths[t_idx]
                                if st.button("", key=thumb_key):
                                    st.session_state[sel_key] = t_idx
                                    st.experimental_rerun()
                                try:
                                    st.image(thumb_path, width=80)
                                except:
                                    st.image(NO_IMAGE, width=80)
                    with col_r:
                        if st.button("▶", key=right_key):
                            st.session_state[sel_key] = (st.session_state[sel_key] + 1) % len(image_paths)
                            st.experimental_rerun()

                # информация
                st.markdown(f"**{prod['brand']} {prod['model_clean']}**")
                if prod['color']:
                    st.write(f"{prod['color']}  |  {prod['gender']}")
                # show EU sizes and US as needed
                if prod['sizes_eu']:
                    st.write("Размеры (EU): " + ", ".join(prod['sizes_eu']))
                else:
                    st.write("Размеры не указаны")
                # price decision: try map by first size or primary price
                display_price = ""
                if prod['price'] is not None:
                    display_price = f"**{int(prod['price'])} ₸**"
                    st.markdown(display_price)
                else:
                    st.write("Цена не указана")
                st.markdown("</div>", unsafe_allow_html=True)

                # кнопка "Подробнее" -> детальная страница
                detail_key = f"view_{key_base}"
                if st.button("Подробнее", key=detail_key, use_container_width=True):
                    # set selected product in session (store index to find in groups)
                    st.session_state.selected_product = prod
                    st.experimental_rerun()

# --- Детальная страница (если выбран продукт) ---
if st.session_state.selected_product:
    prod = st.session_state.selected_product
    st.markdown("---")
    if st.button("← Назад к каталогу"):
        st.session_state.selected_product = None
        st.experimental_rerun()
    cols = st.columns([2,1])
    with cols[0]:
        images = collect_images_for_row({'image': prod['image_field'], 'sku': prod['sku']})
        if not images:
            images = [NO_IMAGE]
        detail_key = safe_key("detail", prod['brand'], prod['model_clean'], prod['color'])
        sel_key = f"sel_{detail_key}"
        if sel_key not in st.session_state:
            st.session_state[sel_key] = 0
        # show main
        try:
            st.image(images[st.session_state[sel_key] % len(images)], use_container_width=True)
        except:
            st.image(NO_IMAGE, use_container_width=True)
        # arrows
        c1, c2, c3 = st.columns([1,8,1])
        with c1:
            if st.button("◀", key=f"det_left_{detail_key}"):
                st.session_state[sel_key] = (st.session_state[sel_key] - 1) % len(images)
                st.experimental_rerun()
        with c2:
            # clickable mini thumbs
            thumbs_cols = st.columns(min(4, len(images)))
            for t_idx, cthumb in enumerate(thumbs_cols):
                with cthumb:
                    if st.button("", key=f"det_thumb_{detail_key}_{t_idx}"):
                        st.session_state[sel_key] = t_idx
                        st.experimental_rerun()
                    try:
                        st.image(images[t_idx], width=80)
                    except:
                        st.image(NO_IMAGE, width=80)
        with c3:
            if st.button("▶", key=f"det_right_{detail_key}"):
                st.session_state[sel_key] = (st.session_state[sel_key] + 1) % len(images)
                st.experimental_rerun()

    with cols[1]:
        st.markdown(f"### {prod['brand']} {prod['model_clean']}")
        st.write(f"Цвет: {prod['color']}")
        st.write(f"Пол: {prod['gender']}")
        st.write(prod.get('description') or "")
        # size selector (EU)
        chosen_size = None
        if prod['sizes_eu']:
            chosen_size = st.selectbox("Размер (EU)", prod['sizes_eu'], key=safe_key("size", prod['sku']))
            # price adjust if price_map contains mapping for chosen_size
            price = prod['price']
            if chosen_size and chosen_size in prod.get('price_map', {}):
                price = prod['price_map'][chosen_size]
            if price:
                st.markdown(f"**{int(price)} ₸**")
            else:
                st.write("Цена не указана")
        else:
            if prod['price']:
                st.markdown(f"**{int(prod['price'])} ₸**")
            else:
                st.write("Цена не указана")
        # add to cart
        if st.button("Добавить в корзину", key=safe_key("add", prod['sku'])):
            st.session_state.cart.append({
                'brand': prod['brand'],
                'model_clean': prod['model_clean'],
                'color': prod['color'],
                'size_eu': chosen_size or "",
                'price': int(price) if price else 0
            })
            st.success("Товар добавлен в корзину")

st.markdown("---")
st.caption("© DENE Store 2025")
