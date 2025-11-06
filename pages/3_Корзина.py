import streamlit as st

st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

st.title("🛒 Корзина")

if 'cart' not in st.session_state or len(st.session_state.cart) == 0:
    st.info("Ваша корзина пуста")
    if st.button("Вернуться в каталог"):
        st.switch_page("main.py")
else:
    total = 0
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.image("data/images/no_image.jpg", width=80)
        with col2:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"Цвет: {item['color']} | Размер: {item['size']}")
            st.write(f"Цена: {item['price']} ₸")
        with col3:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        total += item['price']
        st.divider()
    
    st.write(f"**Итого: {total} ₸**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")
    with col2:
        if st.button("Оформить заказ", type="primary", use_container_width=True):
            st.info("Функция оформления заказа в разработке")