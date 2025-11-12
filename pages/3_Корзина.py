import streamlit as st
import glob
import os
import base64
import requests
import json

st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

# Пути
IMAGES_PATH = "data/images"

# --- Настройки Telegram бота ---
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

# --- Функции для изображений ---
def get_image_path(image_names, images_path="data/images"):
    """Ищет изображение по имени из колонки image"""
    if (image_names is None or 
        not image_names or 
        str(image_names).strip() == "" or
        str(image_names).lower() == "nan"):
        return os.path.join(images_path, "no_image.jpg")
    
    image_names_list = str(image_names).strip().split()
    if not image_names_list:
        return os.path.join(images_path, "no_image.jpg")
    
    first_image_name = image_names_list[0]
    
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(images_path, "**", f"{first_image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            return image_files[0]
        
        pattern_start = os.path.join(images_path, "**", f"{first_image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            return image_files[0]
    
    return os.path.join(images_path, "no_image.jpg")

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        fallback = os.path.join(IMAGES_PATH, "no_image.jpg")
        try:
            with open(fallback, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except:
            return ""

# --- Функция для отправки заказа в Telegram ---
def send_order_to_telegram(order_data):
    """Отправляет заказ в Telegram"""
    try:
        # Формируем сообщение
        message = f"🛍️ *НОВЫЙ ЗАКАЗ*\n\n"
        message += f"👤 *Клиент:* {order_data['customer_name']}\n"
        message += f"📞 *Телефон:* {order_data['customer_phone']}\n"
        message += f"📍 *Адрес:* {order_data['customer_address']}\n"
        
        if order_data.get('customer_email'):
            message += f"📧 *Email:* {order_data['customer_email']}\n"
        
        if order_data.get('customer_comment'):
            message += f"💬 *Комментарий:* {order_data['customer_comment']}\n"
        
        message += f"\n*Товары:*\n"
        
        total = 0
        for i, item in enumerate(order_data['items'], 1):
            item_total = item['price'] * item['quantity']
            total += item_total
            message += f"{i}. {item['brand']} {item['model']}\n"
            message += f"   Цвет: {item['color']}\n"
            message += f"   Размер: {item['size']}\n"
            message += f"   Цена: {item['price']:,} ₸ x {item['quantity']} = {item_total:,} ₸\n\n"
        
        message += f"💰 *ИТОГО: {total:,} ₸*".replace(",", " ")
        
        # Отправляем в Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload)
        return response.status_code == 200
        
    except Exception as e:
        st.error(f"Ошибка отправки заказа: {e}")
        return False

# --- Функция для форматирования цены ---
def format_price(price):
    """Округляет цену до тысяч и форматирует с разделителями"""
    try:
        price_num = float(price)
        rounded_price = round(price_num / 1000) * 1000
        return f"{int(rounded_price):,} ₸".replace(",", " ")
    except (ValueError, TypeError):
        return f"{0:,} ₸".replace(",", " ")

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
                    image_path = get_image_path(item['image'])
                    image_base64 = get_image_base64(image_path)
                    if image_base64:
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{image_base64}" style="width:100%; border-radius:8px; max-width:150px;">',
                            unsafe_allow_html=True
                        )
                    else:
                        st.image("https://via.placeholder.com/150x150/CCCCCC/666666?text=No+Image", width=120)
                except Exception as e:
                    st.image("https://via.placeholder.com/150x150/CCCCCC/666666?text=No+Image", width=120)
            else:
                st.image("https://via.placeholder.com/150x150/CCCCCC/666666?text=No+Image", width=120)
        
        with col2:
            # Информация о товаре
            brand = item.get('brand', '')
            model = item.get('model', '')
            st.subheader(f"{brand} {model}")
            st.write(f"**Цвет:** {item.get('color', 'Не указан')}")
            if item.get('size'):
                st.write(f"**Размер:** {item.get('size')}")
            formatted_price = format_price(item.get('price', 0))
            st.write(f"**Цена:** {formatted_price}")
        
        with col3:
            # Управление количеством и удаление
            current_quantity = item.get('quantity', 1)
            
            col_qty1, col_qty2, col_qty3 = st.columns([1, 2, 1])
            with col_qty1:
                if st.button("➖", key=f"dec_{i}", use_container_width=True):
                    update_quantity(i, current_quantity - 1)
            with col_qty2:
                st.markdown(f"<div style='text-align: center; padding: 8px; font-weight: bold;'>{current_quantity}</div>", 
                           unsafe_allow_html=True)
            with col_qty3:
                if st.button("➕", key=f"inc_{i}", use_container_width=True):
                    update_quantity(i, current_quantity + 1)
            
            if st.button("🗑️ Удалить", key=f"remove_{i}", type="secondary", use_container_width=True):
                remove_item(i)
        
        st.divider()

    # Расчет итогов
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in st.session_state.cart)
    formatted_total = format_price(total)

    # Основной футер с итогами
    st.subheader(f"Итого: {formatted_total}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")

    with col2:
        if st.button("Оформить заказ →", type="primary", use_container_width=True):
            st.session_state.show_order_form = True
            st.rerun()

# --- Форма оформления заказа ---
if st.session_state.get('show_order_form', False):
    st.divider()
    st.subheader("📋 Оформление заказа")
    
    with st.form("order_form"):
        st.write("**Контактная информация:**")
        
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Имя и фамилия *", placeholder="Иван Иванов")
        with col2:
            customer_phone = st.text_input("Телефон *", placeholder="+7 777 123 4567")
        
        customer_address = st.text_area("Адрес доставки *", placeholder="Город, улица, дом, квартира")
        customer_email = st.text_input("Email (необязательно)", placeholder="ivan@example.com")
        customer_comment = st.text_area("Комментарий к заказу (необязательно)", placeholder="Пожелания по доставке и т.д.")
        
        # Подтверждение заказа
        st.write("**Ваш заказ:**")
        for item in st.session_state.cart:
            st.write(f"- {item['brand']} {item['model']} ({item['color']}, размер {item['size']}) - {item['quantity']} шт.")
        
        st.write(f"**Общая сумма: {formatted_total}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("← Вернуться в корзину", type="secondary"):
                st.session_state.show_order_form = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("✅ Подтвердить заказ", type="primary"):
                # Проверка обязательных полей
                if not customer_name or not customer_phone or not customer_address:
                    st.error("Пожалуйста, заполните все обязательные поля (отмечены *)")
                else:
                    # Собираем данные заказа
                    order_data = {
                        'customer_name': customer_name,
                        'customer_phone': customer_phone,
                        'customer_address': customer_address,
                        'customer_email': customer_email if customer_email else "Не указан",
                        'customer_comment': customer_comment if customer_comment else "Нет комментария",
                        'items': st.session_state.cart.copy(),
                        'total': total
                    }
                    
                    # Отправляем заказ в Telegram
                    with st.spinner("Отправляем заказ..."):
                        success = send_order_to_telegram(order_data)
                    
                    if success:
                        st.success("🎉 Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.")
                        st.balloons()
                        
                        # Очищаем корзину после успешного оформления
                        st.session_state.cart = []
                        st.session_state.show_order_form = False
                        
                        # Добавляем кнопку для нового заказа
                        if st.button("🛍️ Сделать новый заказ", use_container_width=True):
                            st.switch_page("main.py")
                    else:
                        st.error("❌ Произошла ошибка при отправке заказа. Пожалуйста, попробуйте еще раз или свяжитесь с нами напрямую.")

# --- ТОЛЬКО ОДИН ФУТЕР ---
from components.documents import documents_footer
documents_footer()