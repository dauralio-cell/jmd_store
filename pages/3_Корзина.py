import streamlit as st
import pandas as pd

# --- Настройки страницы ---
st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

def main():
    st.title("🛒 Корзина")
    
    # Проверяем, есть ли товары в корзине
    if 'cart' not in st.session_state or len(st.session_state.cart) == 0:
        st.info("Ваша корзина пуста")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("← Вернуться в каталог", use_container_width=True):
                st.switch_page("main.py")
        return
    
    # Отображаем товары в корзине
    total = 0
    
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"**{item['brand']} {item['model']}**")
            st.markdown(f"Цвет: {item['color']}")
            if item.get('size'):
                st.markdown(f"Размер: {item['size']}")
        
        with col2:
            # ОКРУГЛЯЕМ ЦЕНУ ДО ТЫСЯЧ
            price = round(item['price'] / 1000) * 1000
            st.markdown(f"**Цена: {int(price):,} ₸**".replace(",", " "))
        
        with col3:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        
        st.divider()
        total += price
    
    # Итоговая сумма
    st.markdown(f"### Итого: {int(total):,} ₸".replace(",", " "))
    
    # Кнопки управления
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")
    
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