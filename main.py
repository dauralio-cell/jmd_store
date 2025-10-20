import os 
import pandas as pd 
import streamlit as st 

# 📁 Пути к файлам
CATALOG_PATH = os.path.join("data", "catalog.xlsx") 
# Исправленный путь:
NO_IMAGE_PATH = os.path.join("data", "images", "no_image.jpg") 

# 🔄 Загрузка каталога
def load_catalog(): 
    df = pd.read_excel(CATALOG_PATH) 
    df.fillna('', inplace=True) 
    return df 

catalog = load_catalog() 

st.title("🛍 Каталог товаров") 

# 🧩 Вывод карточек
for _, row in catalog.iterrows(): 
    # --- Изображение ---
    image_path = str(row.get('image', '')).strip() 
    if not image_path: 
        image_path = NO_IMAGE_PATH 
        
    # --- Цена ---
    price = str(row.get('price', '')).strip() 
    price_html = f"<p style='font-size:16px; color:gray; margin:2px 0;'>{int(price)} ₸</p>" if price.isdigit() else "" 
    
    # --- Модель ---
    model = str(row.get('model', '')).strip() 
    model_html = f"<p style='font-size:15px; color:#555; margin:2px 0;'>Модель: {model}</p>" if model else "" 
    
    # --- Отображение карточки ---
    st.markdown(f""" 
    <div style="border:1px solid #ddd; border-radius:12px; padding:12px; margin:10px 0;"> 
        <img src="{image_path}" style="width:100%; border-radius:8px; margin-bottom:6px;"> 
        <p style="font-weight:bold; font-size:18px;">{row.get('name', '')}</p> 
        {model_html} 
        {price_html} 
    </div> 
    """, unsafe_allow_html=True)
