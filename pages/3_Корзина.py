import streamlit as st
import glob
import os
import base64

st.set_page_config(page_title="Корзина - DENE Store", layout="wide")

# Пути
IMAGES_PATH = "data/images"
DOCUMENTS_PATH = "data/documents"

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

# --- Функции для документов ---
def create_sample_documents():
    """Создает примеры документов если они не существуют"""
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    
    # Простые текстовые файлы с содержанием (временно вместо PDF)
    documents = {
        "public_offer.txt": """
        ДОГОВОР ПУБЛИЧНОЙ ОФЕРТЫ
        интернет-магазина DENE Store
        
        1. ОБЩИЕ ПОЛОЖЕНИЯ
        1.1. Настоящий договор является официальным предложением (публичной офертой) 
        интернет-магазина DENE Store заключить договор купли-продажи товаров.
        
        2. ПОРЯДОК ЗАКЛЮЧЕНИЯ ДОГОВОРА
        2.1. Покупатель принимает условия оферты путем оформления заказа на сайте.
        
        3. ДОСТАВКА И ОПЛАТА
        3.1. Срок доставки: 10-21 рабочий день.
        3.2. Оплата осуществляется при получении товара.
        
        4. ВОЗВРАТ ТОВАРА
        4.1. Возврат товара возможен в течение 14 дней с момента получения.
        
        Контакты: +7 747 555 48 69, jmd.dene@gmail.com
        """,
        
        "privacy_policy.txt": """
        ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ
        DENE Store
        
        1. СБОР ИНФОРМАЦИИ
        1.1. Мы собираем только необходимую информацию для обработки заказов.
        
        2. ИСПОЛЬЗОВАНИЕ ИНФОРМАЦИИ
        2.1. Информация используется исключительно для целей магазина.
        """,
        
        "return_policy.txt": """
        УСЛОВИЯ ВОЗВРАТА ТОВАРА
        DENE Store
        
        1. УСЛОВИЯ ВОЗВРАТА
        1.1. Товар должен быть в оригинальной упаковке.
        1.2. Возврат в течение 14 дней.
        """
    }
    
    for filename, content in documents.items():
        filepath = os.path.join(DOCUMENTS_PATH, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

def show_document(file_path):
    """Показывает содержимое документа"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        st.text_area("Содержание документа:", content, height=300)
    except Exception as e:
        st.error(f"Не удалось загрузить документ: {e}")

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Создает ссылку для скачивания файла"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" style="color: #666; text-decoration: none;">📥 {file_label}</a>'
    return href

# Создаем документы при запуске
create_sample_documents()

# --- ОСНОВНОЙ КОД КОРЗИНЫ ---

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
            st.write(f"**Цена:** {item.get('price', 0):,} ₸".replace(",", " "))
        
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

# --- ОБНОВЛЕННЫЙ ФУТЕР С ДОКУМЕНТАМИ ---
st.markdown("---")

# Информация о магазине
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 14px;">
        <p><strong>DENE Store</strong></p>
        <p>📞 +7 747 555 48 69 • ✉️ jmd.dene@gmail.com</p>
        <p>📷 <a href="https://instagram.com/jmd.dene" target="_blank" style="color: #666;">Instagram @jmd.dene</a></p>
        <p><strong>График работы:</strong> Пн-Пт: 9:00 - 18:00 • Сб-Вс: 10:00 - 16:00</p>
        <p><strong>Доставка:</strong> 10-21 день • <strong>Возврат:</strong> 14 дней с момента получения</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Документы
st.markdown("---")
st.markdown("### 📄 Документы")

# Кнопки для просмотра документов
doc_col1, doc_col2, doc_col3 = st.columns(3)

with doc_col1:
    if st.button("📋 Публичная оферта", use_container_width=True):
        st.session_state.show_doc = "public_offer"

with doc_col2:
    if st.button("🔒 Политика конфиденциальности", use_container_width=True):
        st.session_state.show_doc = "privacy_policy"

with doc_col3:
    if st.button("🔄 Условия возврата", use_container_width=True):
        st.session_state.show_doc = "return_policy"

# Показ выбранного документа
if 'show_doc' in st.session_state:
    st.markdown("---")
    doc_file = os.path.join(DOCUMENTS_PATH, f"{st.session_state.show_doc}.txt")
    show_document(doc_file)

# Ссылки для скачивания
st.markdown("### 📥 Скачать документы")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(get_binary_file_downloader_html(
        os.path.join(DOCUMENTS_PATH, "public_offer.txt"), 
        "Публичную оферту"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(get_binary_file_downloader_html(
        os.path.join(DOCUMENTS_PATH, "privacy_policy.txt"), 
        "Политику конфиденциальности"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(get_binary_file_downloader_html(
        os.path.join(DOCUMENTS_PATH, "return_policy.txt"), 
        "Условия возврата"
    ), unsafe_allow_html=True)

# Копирайт
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>© 2025 DENE Store. Все права защищены.</div>", 
            unsafe_allow_html=True)
# Добавьте в самый конец файла:
from components.documents import documents_footer

documents_footer()