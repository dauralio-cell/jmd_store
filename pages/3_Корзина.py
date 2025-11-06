import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

# --- Функции для изображений ---
def get_image_path(image_names):
    """Ищет изображение по имени из колонки image"""
    if (image_names is pd.NA or 
        pd.isna(image_names) or 
        not image_names or 
        str(image_names).strip() == ""):
        return os.path.join("data/images", "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join("data/images", "no_image.jpg")
    
    first_image_name = image_names_list[0]
    
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join("data/images", "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        
        pattern_start = os.path.join("data/images", "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    return os.path.join("data/images", "no_image.jpg")

# Кнопка назад
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("← Назад в каталог", use_container_width=True):
        st.switch_page("main.py")

st.title("🛒 Корзина")

if 'cart' not in st.session_state or len(st.session_state.cart) == 0:
    st.info("Ваша корзина пуста")
else:
    total = 0
    
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        
        with col1:
            # Показываем изображение товара
            image_path = get_image_path(item['image'])
            try:
                st.image(image_path, width=100)
            except:
                st.image("data/images/no_image.jpg", width=100)
        
        with col2:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"Цвет: {item['color']}")
            st.write(f"Размер: {item['size']}")
            st.write(f"Цена: {int(item['price'])} ₸")
        
        # В цикле отображения товаров в корзине замените блок с кнопкой удаления:

        with col3:
        if st.button("🗑️ Удалить", key=f"remove_{i}", use_container_width=True, 
                 type="secondary"):
        st.session_state.cart.pop(i)
        st.rerun()
        
        with col4:
            st.write("Кол-во: 1")
        
        total += item['price']
        st.divider()
    
    st.markdown(f"### Итого: {int(total)} ₸")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")
    with col2:
        if st.button("Оформить заказ", type="primary", use_container_width=True):
            st.info("Функция оформления заказа в разработке. Скоро вы сможете оплачивать заказы онлайн!")

# --- Информация о доставке ---
st.markdown("---")
st.markdown("### Информация о доставке")
st.markdown("**Курьерская служба:** 10-21 день")
st.markdown("**Возврат:** 14 дней с момента получения")
st.markdown("**Контакты:** +7 747 555 48 69 • jmd.dene@gmail.com")
st.markdown("[Instagram @jmd.dene](https://instagram.com/jmd.dene)")
st.markdown("[Публичная оферта](#)")