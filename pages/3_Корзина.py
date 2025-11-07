import streamlit as st

st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

# Кнопка назад
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("← Назад", use_container_width=True):
        st.switch_page("main.py")

st.title("Корзина")

# Инициализация состояния корзины
if 'cart' not in st.session_state:
    st.session_state.cart = []

# Функция удаления товара
def remove_item(index):
    st.session_state.cart.pop(index)
    st.rerun()

# Функция обновления количества
def update_quantity(index, new_quantity):
    if new_quantity >= 1:
        st.session_state.cart[index]['quantity'] = new_quantity
    st.rerun()

# Отображение товаров в корзине
if not st.session_state.cart:
    st.info("🛒 Ваша корзина пуста")
    if st.button("Вернуться к покупкам", use_container_width=True):
        st.switch_page("main.py")
else:
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # Показываем изображение товара
            if 'image' in item and item['image']:
                try:
                    from pages.2_Детали_товара import get_image_path, get_image_base64
                    image_path = get_image_path(item['image'])
                    image_base64 = get_image_base64(image_path)
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{image_base64}" style="width:100%; border-radius:8px;">',
                        unsafe_allow_html=True
                    )
                except:
                    st.image("https://via.placeholder.com/120x120/CCCCCC/666666?text=No+Image", width=120)
            else:
                st.image("https://via.placeholder.com/120x120/CCCCCC/666666?text=No+Image", width=120)
        
        with col2:
            # Информация о товаре
            st.subheader(f"{item.get('brand', '')} {item.get('model', '')}")
            st.write(f"**Цвет:** {item.get('color', 'Не указан')}")
            if item.get('size'):
                st.write(f"**Размер:** {item.get('size')}")
            st.write(f"**Цена:** {item.get('price', 0):,} ₸".replace(",", " "))
        
        with col3:
            # Управление количеством и удаление
            current_quantity = item.get('quantity', 1)
            
            col_qty1, col_qty2, col_qty3 = st.columns([1, 2, 1])
            with col_qty1:
                if st.button("➖", key=f"dec_{i}", use_container_width=True):
                    update_quantity(i, current_quantity - 1)
            with col_qty2:
                st.markdown(f"<div style='text-align: center; padding: 8px;'>{current_quantity}</div>", 
                           unsafe_allow_html=True)
            with col_qty3:
                if st.button("➕", key=f"inc_{i}", use_container_width=True):
                    update_quantity(i, current_quantity + 1)
            
            if st.button("🗑️ Удалить", key=f"remove_{i}", type="secondary", use_container_width=True):
                remove_item(i)
        
        st.divider()

    # Расчет итогов
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in st.session_state.cart)

    # Основной футер с итогами
    st.subheader(f"Итого: {total:,} ₸".replace(",", " "))

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")

    with col2:
        if st.button("Оформить заказ →", type="primary", use_container_width=True):
            st.success("Заказ успешно оформлен!")
            st.balloons()
            # Очищаем корзину после оформления
            st.session_state.cart = []

# --- ФУТЕР в стиле DENE Store ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 14px;">
        <p><strong>DENE Store</strong></p>
        <p>📞 +7 747 555 48 69 • ✉️ jmd.dene@gmail.com</p>
        <p>📷 <a href="https://instagram.com/jmd.dene" target="_blank">Instagram @jmd.dene</a></p>
        <p><strong>График работы:</strong> Пн-Пт: 9:00 - 18:00 • Сб-Вс: 10:00 - 16:00</p>
        <p><strong>Доставка:</strong> 10-21 день • <strong>Возврат:</strong> 14 дней с момента получения</p>
        <p>
            <a href="#">Публичная оферта</a> • 
            <a href="#">Политика конфиденциальности</a> • 
            <a href="#">Условия возврата</a>
        </p>
        <p>© 2024 DENE Store. Все права защищены.</p>
    </div>
    """,
    unsafe_allow_html=True
)