import streamlit as st

def cart_item(name, color, size, price, quantity=1):
    """Компонент товара в корзине"""
    
    # Используем columns для расположения как в вашем HTML
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Информация о товаре
        st.markdown(f"""
        <div style="padding: 0 20px;">
            <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">
                {name}
            </div>
            <div style="color: #666; font-size: 14px; margin-bottom: 4px;">
                Цвет: {color}
            </div>
            <div style="color: #666; font-size: 14px; margin-bottom: 4px;">
                Размер: {size}
            </div>
            <div style="font-weight: bold; font-size: 16px; color: #000;">
                {price} ₸
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Количество и кнопка удаления
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
            <div style="text-align: center;">
                <span style="color: #666; font-size: 14px;">Кол-во: {quantity}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Удалить", key=f"remove_{name}", 
                    use_container_width=True, type="secondary"):
            st.warning(f"Товар {name} удален из корзины")
            return False
    return True

# Основной интерфейс
st.title("🛒 Корзина")

# Пример использования
st.divider()
if cart_item("Mizuno Racer S", "white", "1", "60 000"):
    st.write("Товар в корзине")

# Можно добавить несколько товаров
st.divider()
if cart_item("Nike Air Max", "black", "42", "45 000", 2):
    st.write("Товар в корзине")

# Итоговая сумма
st.divider()
st.subheader("Итого: 105 000 ₸")

col1, col2 = st.columns(2)
with col1:
    if st.button("← Продолжить покупки", use_container_width=True):
        st.success("Переходим к каталогу...")

with col2:
    if st.button("Оформить заказ →", type="primary", use_container_width=True):
        st.success("Заказ успешно оформлен!")