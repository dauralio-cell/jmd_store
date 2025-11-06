import streamlit as st

st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

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
            # Здесь можно добавить изображение товара
            st.write("📷")  # Заглушка для изображения
        
        with col2:
            st.write(f"**{item['brand']} {item['model']}**")
            st.write(f"Цвет: {item['color']}")
            st.write(f"Размер: {item['size']}")
            st.write(f"Цена: {int(item['price'])} ₸")
        
        with col3:
            if st.button("❌ Удалить", key=f"remove_{i}", use_container_width=True):
                st.session_state.cart.pop(i)
                st.rerun()
        
        with col4:
            # Здесь можно добавить выбор количества
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