import streamlit as st

st.title("🛒 Корзина")

# Товар в корзине
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("Mizuno Racer S")
    st.write("Цвет: white")
    st.write("Размер: 1")
    st.write("**60 000 ₸**")

with col2:
    quantity = st.number_input("Кол-во", min_value=1, value=1, key="qty1")

with col3:
    st.write("")  # для выравнивания
    if st.button("🗑️ Удалить", key="remove1", type="secondary"):
        st.warning("Товар удален из корзины")

st.divider()

# Итоги
st.subheader("Итого: 60 000 ₸")

col_continue, col_order = st.columns(2)
with col_continue:
    st.button("← Продолжить покупки", use_container_width=True)

with col_order:
    st.button("Оформить заказ →", type="primary", use_container_width=True)