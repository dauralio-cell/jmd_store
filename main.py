# main.py
import streamlit as st
import pandas as pd
import os
import glob
import re

# -------------- Настройки --------------
st.set_page_config(page_title="DENE Store", layout="wide")
CATALOG_PATH = "data/catalog.xlsx"
IMAGES_ROOT = "data/images"
NO_IMAGE_PATH = os.path.join(IMAGES_ROOT, "no_image.jpg")

# -------------- Утилиты --------------
def find_images_by_name(name):
    """Ищет рекурсивно файлы, имя без расширения или с шаблоном.
       name может быть '100001_1' или '100001_1.jpg' или '100001_1 100001_2'."""
    if not name or str(name).strip() == "":
        return []
    # split possible multiple names separated by comma/space/;
    parts = re.split(r"[,\s;]+", str(name).strip())
    found = []
    exts = ["jpg", "jpeg", "png", "webp"]
    for p in parts:
        if not p:
            continue
        # if p contains extension, search exact pattern
        base, ext = os.path.splitext(p)
        if ext:
            patt = os.path.join(IMAGES_ROOT, "**", p)
            found += glob.glob(patt, recursive=True)
        else:
            # try with extensions
            for e in exts:
                patt = os.path.join(IMAGES_ROOT, "**", f"{p}.{e}")
                found += glob.glob(patt, recursive=True)
            # also try files starting with p (e.g. p_1, p_2)
            for e in exts:
                patt = os.path.join(IMAGES_ROOT, "**", f"{p}_*.{e}")
                found += glob.glob(patt, recursive=True)
    # unique and sorted
    uniq = []
    for f in found:
        if f not in uniq:
            uniq.append(f)
    return uniq

def first_image_for_row(row):
    # Prefer entries from 'image' column, else try SKU based
    img_col_candidates = [c for c in row.index if str(c).lower() == "image" or str(c).lower() == "images"]
    images = []
    if img_col_candidates:
        raw = row[img_col_candidates[0]]
        images = find_images_by_name(raw)
    if not images:
        # try SKU
        sku_cols = [c for c in row.index if str(c).lower() == "sku"]
        if sku_cols:
            sku = row[sku_cols[0]]
            if pd.notna(sku) and str(sku).strip() != "":
                # match by prefix SKU_*
                images = find_images_by_name(str(int(sku)) if isinstance(sku, (int,float)) and not pd.isna(sku) else str(sku))
    return images if images else [NO_IMAGE_PATH]

def normalize_colnames(df):
    # make common names lower-case with underscores
    mapping = {}
    for c in df.columns:
        cl = c.strip()
        cl_l = cl.lower().replace(" ", "_")
        mapping[c] = cl_l
    df = df.rename(columns=mapping)
    return df

def clean_model_name(s: str):
    if s is None or str(s).strip() == "":
        return ""
    s = str(s)
    # remove content in parentheses (article) and trailing SKU-like tokens
    s = re.sub(r"\(.*?\)", "", s).strip()
    s = re.sub(r"\s+\-?\s*\w+$", lambda m: m.group(0) if len(m.group(0).strip())>3 else "", s).strip()
    return s

# -------------- Загрузка данных (все листы) --------------
@st.cache_data(show_spinner=False)
def load_catalog(path):
    if not os.path.exists(path):
        st.error(f"Файл каталога не найден: {path}")
        return pd.DataFrame()
    xls = pd.ExcelFile(path)
    df_list = []
    for sheet in xls.sheet_names:
        tmp = pd.read_excel(xls, sheet_name=sheet)
        if tmp.empty:
            continue
        tmp = normalize_colnames(tmp)
        # ensure brand exists (sheet name as fallback)
        if "brand" not in tmp.columns or tmp["brand"].isnull().all():
            tmp["brand"] = sheet
        tmp["__sheet_name"] = sheet
        df_list.append(tmp)
    if not df_list:
        return pd.DataFrame()
    df = pd.concat(df_list, ignore_index=True, sort=False)
    # ensure important columns exist
    for col in ["sku", "model", "gender", "color", "image", "price", "preorder", "in_stock", "description", "size_us", "size_eu", "sizes"]:
        if col not in df.columns:
            df[col] = ""
    # clean and prepare
    df["model_clean"] = df["model"].apply(clean_model_name)
    # sizes fallback: if 'sizes' has comma-separated EU sizes try split into sizes list
    # We'll keep size_us and size_eu columns if present, else try to parse from 'sizes'
    df["size_eu"] = df["size_eu"].fillna("")
    df["size_us"] = df["size_us"].fillna("")
    # if size_eu empty and sizes column present, try to extract numbers like 40,41.5 etc.
    def sizes_from_field(r):
        if r["size_eu"] and str(r["size_eu"]).strip() != "":
            return r["size_eu"]
        s = str(r.get("sizes","") or "")
        if s:
            # return comma-separated list cleaned
            parts = re.split(r"[,\s;]+", s.strip())
            parts = [p for p in parts if p]
            return ",".join(parts)
        return ""
    df["size_eu"] = df.apply(sizes_from_field, axis=1)
    # price as number if possible
    def parse_price(x):
        if pd.isna(x) or str(x).strip()=="":
            return None
        try:
            return float(str(x).replace(" ", "").replace("₸","").replace(",",""))
        except:
            return None
    df["price_val"] = df["price"].apply(parse_price)
    # fill description
    df["description"] = df["description"].fillna("").astype(str)
    return df

df = load_catalog(CATALOG_PATH)
if df.empty:
    st.stop()

# -------------- Filters UI --------------
st.image("data/images/banner.jpg", width="stretch")
st.markdown("<h1 style='text-align:center; white-space: nowrap;'>DENE Store. Добро пожаловать!</h1>", unsafe_allow_html=True)

st.markdown("### Фильтры")
col1, col2, col3, col4 = st.columns([2,3,2,2])
brands = sorted(df["brand"].dropna().unique().tolist())
brand = col1.selectbox("Бренд", ["Все"] + brands)

# models: unique model_clean for selected brand (no duplicates)
if brand != "Все":
    df_brand = df[df["brand"] == brand]
else:
    df_brand = df
models_unique = sorted({clean_model_name(m) for m in df_brand["model_clean"].dropna().astype(str)})
model = col2.selectbox("Модель", ["Все"] + models_unique)

# size filter - collect all EU sizes across table (split commas)
all_sizes = set()
for s in df["size_eu"].astype(str).tolist():
    if s and s.strip():
        for part in re.split(r"[,\s;]+", s.strip()):
            if part:
                all_sizes.add(part)
sizes_list = sorted(all_sizes, key=lambda x: float(x) if re.match(r"^\d+(\.\d+)?$", x) else 999)
size_filter = col3.selectbox("Размер (EU)", ["Все"] + sizes_list)

gender_list = ["Все", "men", "women", "unisex"]
gender_filter = col4.selectbox("Пол", gender_list)

# apply filters
filtered = df.copy()
if brand != "Все":
    filtered = filtered[filtered["brand"] == brand]
if model != "Все":
    filtered = filtered[filtered["model_clean"].str.lower() == model.lower()]
if size_filter != "Все":
    filtered = filtered[filtered["size_eu"].astype(str).str.contains(rf"\b{re.escape(size_filter)}\b")]
if gender_filter != "Все":
    filtered = filtered[filtered["gender"].astype(str).str.lower() == gender_filter.lower()]

st.write("")  # gap

# -------------- Show results --------------
st.markdown("## Каталог")

# We want: after selecting a model -> show one card per color (unique color variants)
if model != "Все":
    # group by model_clean and color
    grouped = filtered.groupby(["model_clean", "color"], dropna=False)
    variants = []
    for (m, color), g in grouped:
        # For this variant we may have multiple SKUs (for different sizes)
        skus = g["sku"].astype(str).unique().tolist()
        price_vals = [p for p in g["price_val"].tolist() if p is not None]
        price_display = f"{int(min(price_vals))} ₸" if price_vals else "Цена уточняется"
        description = "; ".join([x for x in g["description"].astype(str).unique() if x.strip()])
        sizes_eu = ",".join(sorted({s for s_list in g["size_eu"].astype(str) for s in re.split(r'[,\s;]+', s_list) if s.strip()}))
        brand_name = g["brand"].iloc[0] if not g["brand"].empty else ""
        images_all = []
        # collect images from rows (image col), else try by sku
        for _, row in g.iterrows():
            imgs = find_images_by_name(row.get("image",""))
            if not imgs:
                # try by sku
                sku_val = row.get("sku","")
                if pd.notna(sku_val) and str(sku_val).strip() != "":
                    imgs = find_images_by_name(str(int(sku_val)) if isinstance(sku_val,(int,float)) and not pd.isna(sku_val) else str(sku_val))
            for im in imgs:
                if im not in images_all:
                    images_all.append(im)
        if not images_all:
            images_all = [NO_IMAGE_PATH]
        variants.append({
            "brand": brand_name,
            "model": m,
            "color": color,
            "skus": skus,
            "price": price_display,
            "sizes_eu": sizes_eu,
            "description": description if description else "",
            "images": images_all
        })
    # Render variants as grid (2 columns)
    cols_per_row = 2
    for i in range(0, len(variants), cols_per_row):
        cols = st.columns(cols_per_row)
        for col_obj, var in zip(cols, variants[i:i+cols_per_row]):
            with col_obj:
                # image gallery front: show first image and arrows (session_state per model+color)
                key = f"sel_{var['brand']}_{var['model']}_{var['color']}".replace(" ", "_")
                if key not in st.session_state:
                    st.session_state[key] = 0
                idx = st.session_state[key]
                images = var["images"]
                # show main image
                try:
                    st.image(images[idx], width=350)
                except:
                    st.image(NO_IMAGE_PATH, width=350)
                # arrows
                left, mid, right = st.columns([1,3,1])
                with left:
                    if st.button("◀", key=f"{key}_left"):
                        st.session_state[key] = max(0, st.session_state[key]-1)
                        st.experimental_rerun()
                with mid:
                    st.markdown(f"**{var['brand']} — {var['model']}**")
                    st.markdown(f"*{var['color']}*")
                    st.markdown(f"Размеры (EU): {var['sizes_eu'] or '-'}")
                    st.markdown(f"Цена: **{var['price']}**")
                    if var["description"]:
                        st.markdown(f"{var['description']}")
                with right:
                    if st.button("▶", key=f"{key}_right"):
                        st.session_state[key] = min(len(images)-1, st.session_state[key]+1)
                        st.experimental_rerun()
                # add to cart (simple notification)
                if st.button("Добавить в корзину", key=f"cart_{key}"):
                    st.success("Товар добавлен в корзину!")
                st.divider()
else:
    # model == "Все" -> show compact card grid (brand + model_clean + first image + price)
    num_cols = 4
    rows = [filtered.iloc[i:i+num_cols] for i in range(0, len(filtered), num_cols)]
    for r in rows:
        cols = st.columns(num_cols)
        for col_obj, (_, row) in zip(cols, r.iterrows()):
            with col_obj:
                brand = row.get("brand","")
                model_clean = row.get("model_clean","")
                price_val = row.get("price_val")
                price_display = f"{int(price_val)} ₸" if price_val is not None else "Цена уточняется"
                images = find_images_by_name(row.get("image",""))
                if not images:
                    images = find_images_by_name(row.get("sku",""))
                if not images:
                    images = [NO_IMAGE_PATH]
                try:
                    st.image(images[0], width=220)
                except:
                    st.image(NO_IMAGE_PATH, width=220)
                st.markdown(f"**{brand} — {model_clean}**")
                st.markdown(f"{price_display}")
                # button opens details: we simulate by filtering model via special query param - but simplest: set session and rerun
                btn_key = f"open_{brand}_{model_clean}".replace(" ", "_")
                if st.button("Открыть модель", key=btn_key):
                    # set session model and rerun; note: we don't change the selectbox value (can't), but we rerun with model set in session_state and show details section.
                    st.session_state["force_model"] = model_clean
                    st.experimental_rerun()
                st.divider()

# If user clicked "Открыть модель" via grid, set the selectbox visually (best-effort)
if "force_model" in st.session_state:
    # note: this won't change the selectbox widget value itself, but we force rendering the model details view:
    st.experimental_rerun()
