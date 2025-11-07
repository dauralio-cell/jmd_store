import streamlit as st

st.set_page_config(page_title="Корзина", layout="wide")

st.title("🛒 Корзина")

# Инициализация состояния корзины
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = [{
        'name': 'Mizuno Racer S',
        'color': 'white', 
        'size': '1',
        'price': 60000,
        'quantity': 1,
        'image': 'https://via.placeholder.com/150x150/CCCCCC/666666?text=Mizuno'
    }]

# Функция удаления товара
def remove_item(index):
    st.session_state.cart_items.pop(index)
    st.rerun()

# Отображение товаров в корзине
for i, item in enumerate(st.session_state.cart_items):
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.image(item['image'], width=120)
    
    with col2:
        st.subheader(item['name'])
        st.write(f"**Цвет:** {item['color']}")
        st.write(f"**Размер:** {item['size']}")
        st.write(f"**Цена:** {item['price']:,} ₸".replace(",", " "))
    
    with col3:
        quantity = st.number_input(
            "Кол-во:", 
            min_value=1, 
            value=item['quantity'],
            key=f"qty_{i}"
        )
        st.session_state.cart_items[i]['quantity'] = quantity
        
        if st.button("🗑️ Удалить", key=f"remove_{i}", type="secondary"):
            remove_item(i)
    
    st.divider()

# Расчет итогов
total = sum(item['price'] * item['quantity'] for item in st.session_state.cart_items)

# Футер с итогами и кнопками
st.subheader(f"Итого: {total:,} ₸".replace(",", " "))

col1, col2 = st.columns(2)

with col1:
    if st.button("← Продолжить покупки", use_container_width=True):
        st.success("Переходим к каталогу...")

with col2:
    if st.button("Оформить заказ →", type="primary", use_container_width=True):
        if st.session_state.cart_items:
            st.success("Заказ успешно оформлен!")
            st.balloons()
        else:
            st.error("Корзина пуста!")

# Сообщение если корзина пуста
if not st.session_state.cart_items:
    st.info("🛒 Ваша корзина пуста")
    if st.button("Вернуться к покупкам"):
        st.success("Переходим к каталогу...")