import pandas as pd
import json
import os
import glob

# --- Путь к Excel ---
catalog_path = "data/catalog.xlsx"

# --- Читаем все листы и объединяем ---
xls = pd.ExcelFile(catalog_path)
df_list = []
for sheet_name in xls.sheet_names:
    sheet_df = pd.read_excel(xls, sheet_name=sheet_name)
    sheet_df["brand_sheet"] = sheet_name
    df_list.append(sheet_df)
df = pd.concat(df_list, ignore_index=True)

# --- Заполняем пустые ячейки сверху вниз ---
for col in ["brand", "model", "gender", "color", "description"]:
    if col in df.columns:
        df[col].ffill(inplace=True)

# --- Поиск фото ---
def find_image(img_name):
    if not isinstance(img_name, str) or not img_name.strip():
        return None
    img_name = img_name.strip()
    extensions = ["png", "jpg", "jpeg", "webp"]
    for ext in extensions:
        files = glob.glob(f"data/images/**/*{img_name}*.{ext}", recursive=True)
        if files:
            # относительный путь
            return os.path.relpath(files[0], start="data").replace("\\", "/")
    return None

# --- Группировка по товарам ---
grouped = df.groupby(["brand", "model", "gender", "color"], dropna=True)

# --- Сбор каталога ---
catalog = []

for (brand, model, gender, color), group in grouped:
    first_row = group.iloc[0]

    # Собираем фото
    images = []
    if "image" in group.columns and pd.notna(first_row["image"]):
        for img_name in str(first_row["image"]).split():
            img_path = find_image(img_name)
            if img_path:
                images.append(f"data/{img_path}")

    # Размеры
    sizes_us = sorted(group["size US"].dropna().astype(str).unique()) if "size US" in group.columns else []
    sizes_eu = sorted(group["size EU"].dropna().astype(str).unique()) if "size EU" in group.columns else []

    # Наличие
    stock = "yes" if any(str(x).lower() == "yes" for x in group.get("in stock", [])) else "no"

    item = {
        "brand": brand,
        "model": model,
        "gender": gender,
        "color": color,
        "price": float(first_row["price"]) if "price" in group.columns and pd.notna(first_row["price"]) else 0,
        "description": str(first_row["description"]) if "description" in group.columns and pd.notna(first_row["description"]) else "",
        "images": images,
        "sizes": {
            "US": sizes_us,
            "EU": sizes_eu
        },
        "in_stock": stock
    }

    catalog.append(item)

# --- Сохраняем в JSON ---
output_path = "data/catalog.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f"✅ Готово! Каталог сохранён в {output_path}")
print(f"📦 Всего товаров: {len(catalog)}")
