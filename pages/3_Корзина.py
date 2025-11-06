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

st.markdown("<h2 style='text-align: center;'>Корзина</h2>", unsafe_allow_html=True)

if 'cart' not in st.session_state or len(st.session_state.cart) == 0:
    st.info("Ваша корзина пуста")
else:
    total = 0
    
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        
        with col1:
            # Показываем изображение товара с рамкой - ИСПРАВЛЕННАЯ ЧАСТЬ
            image_path = get_image_path(item['image'])
            try:
                # Используем st.image с контейнером для рамки
                st.markdown(
                    """
                    <div style="border: 1px solid #eee; border-radius: 8px; padding: 8px; text-align: center; height: 120px; display: flex; align-items: center; justify-content: center;">
                    """,
                    unsafe_allow_html=True
                )
                st.image(image_path, width=100, use_container_width=False)
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                # Если ошибка, показываем no_image
                st.markdown(
                    """
                    <div style="border: 1px solid #eee; border-radius: 8px; padding: 8px; text-align: center; height: 120px; display: flex; align-items: center; justify-content: center;">
                    """,
                    unsafe_allow_html=True
                )
                st.image("data/images/no_image.jpg", width=100, use_container_width=False)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"**Цвет:** {item['color']}")
            st.write(f"**Размер:** {item['size']}")
            st.write(f"**Цена:** {int(item['price'])} ₸")
        
        with col3:
            # Аккуратная кнопка удаления
            if st.button("Удалить", key=f"remove_{i}", use_container_width=True, type="secondary"):
                st.session_state.cart.pop(i)
                st.rerun()
        
        with col4:
            # Симметрично кнопке удаления
            st.markdown(
                f"""
                <div style="text-align: center; padding: 8px; height: 120px; display: flex; align-items: center; justify-content: center;">
                    <p style="margin: 0; font-size: 14px; color: #666;">Кол-во: 1</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        total += item['price']
        st.divider()
    
    # Итого и кнопки
    st.markdown(f"### Итого: {int(total)} ₸")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")
    with col2:
        if st.button("Оформить заказ →", type="primary", use_container_width=True):
            st.info("Функция оформления заказа в разработке. Скоро вы сможете оплачивать заказы онлайн!")

# --- Информация о доставке ---
st.markdown("---")
st.markdown("### Информация о доставке")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Доставка**")
    st.markdown("Курьерская служба")
    st.markdown("10-21 день")
with col2:
    st.markdown("**Возврат**")
    st.markdown("14 дней с момента получения")
with col3:
    st.markdown("**Контакты**")
    st.markdown("+7 747 555 48 69")
    st.markdown("jmd.dene@gmail.com")
    st.markdown("[Instagram @jmd.dene](https://instagram.com/jmd.dene)")

# --- Футер ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 14px; line-height: 1.5;">
        <p><strong>© DENE Store 2025</strong></p>
        <p>+7 747 555 48 69</p>
        <p>jmd.dene@gmail.com</p>
        <p><a href="https://instagram.com/jmd.dene" target="_blank" style="color: #666; text-decoration: none;">Instagram @jmd.dene</a></p>
        <p style="margin-top: 10px;">
            <a href="#" style="color: #666; text-decoration: none; margin: 0 10px;">Публичная оферта</a> • 
            <a href="#" style="color: #666; text-decoration: none; margin: 0 10px;">Политика конфиденциальности</a> • 
            <a href="#" style="color: #666; text-decoration: none; margin: 0 10px;">Условия возврата</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)