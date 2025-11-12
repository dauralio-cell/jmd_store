import streamlit as st
import pandas as pd
import glob
import os
import base64

# --- Настройки страницы ---
st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

# --- Пути ---
IMAGES_PATH = "data/images"

# --- Функции для работы с изображениями (ТЕ ЖЕ САМЫЕ ЧТО И В ГЛАВНОЙ) ---
def get_image_path(image_names):
    """Ищет изображение по имени из колонки image (берет первое изображение из списка)"""
    if (image_names is pd.NA or 
        pd.isna(image_names) or 
        not image_names or 
        str(image_names).strip() == ""):
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    first_image_name = image_names_list[0]
    
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(IMAGES_PATH, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        
        pattern_start = os.path.join(IMAGES_PATH, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    return os.path.join(IMAGES_PATH, "no_image.jpg")

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        with open(fallback, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

# --- Функция округления цены ---
def round_price(price):
    """Округляет цену до тысяч"""
    try:
        return int(round(float(price) / 1000) * 1000)
    except:
        return int(price) if price else 0

def main():
    st.title("🛒 Корзина")
    
    # Кнопка назад
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Назад к каталогу", use_container_width=True):
            st.switch_page("main.py")
    
    # Проверяем, есть ли товары в корзине
    if 'cart' not in st.session_state or len(st.session_state.cart) == 0:
        st.info("Ваша корзина пуста")
        return
    
    # Отображаем товары в корзине
    total = 0
    
    for i, item in enumerate(st.session_state.cart):
        # Получаем изображение для товара
        image_path = get_image_path(item.get('image', ''))
        image_base64 = get_image_base64(image_path)
        
        # Создаем колонки для отображения товара
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        
        with col1:
            # Показываем изображение товара
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <img src="data:image/jpeg;base64,{image_base64}" 
                         style="width:80px; height:80px; object-fit:cover; border-radius:8px; border:1px solid #eee;">
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(f"**{item['brand']} {item['model']}**")
            st.markdown(f"Цвет: {item['color']}")
            if item.get('size'):
                st.markdown(f"Размер: {item['size']}")
        
        with col3:
            # ОКРУГЛЯЕМ ЦЕНУ ДО ТЫСЯЧ
            price = round_price(item['price'])
            st.markdown(f"**Цена: {price:,} ₸**".replace(",", " "))
        
        with col4:
            if st.button("🗑️ Удалить", key=f"delete_{i}", use_container_width=True):
                st.session_state.cart.pop(i)
                st.rerun()
        
        st.divider()
        total += price
    
    # Итоговая сумма
    st.markdown(f"### Итого: {total:,} ₸".replace(",", " "))
    
    # Кнопки управления
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")
    
    with col2:
        if st.button("🔄 Очистить корзину", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    
    with col3:
        if st.button("Оформить заказ →", type="primary", use_container_width=True):
            st.success("Заказ оформлен! С вами свяжутся для подтверждения.")
            st.session_state.cart = []
            st.rerun()

if __name__ == "__main__":
    main()

# --- ФУТЕР ---
from components.documents import documents_footer
documents_footer()