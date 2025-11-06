import streamlit as st
import pandas as pd
import glob
import os
import base64

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

def get_image_base64(image_path):
    """Возвращает изображение в base64 для вставки в HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        # Если ошибка, возвращаем no_image
        fallback = os.path.join("data/images", "no_image.jpg")
        with open(fallback, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

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
        # Используем HTML для красивого отображения
        image_path = get_image_path(item['image'])
        image_base64 = get_image_base64(image_path)
        
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; padding: 16px 0; border-bottom: 1px solid #eee;">
                <!-- Фото товара -->
                <div style="flex: 1; text-align: center;">
                    <img src="data:image/jpeg;base64,{image_base64}" 
                         style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px; border: 1px solid #eee;">
                </div>
                
                <!-- Информация о товаре -->
                <div style="flex: 3; padding: 0 20px;">
                    <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">
                        {item['brand']} {item['model']}
                    </div>
                    <div style="color: #666; font-size: 14px; margin-bottom: 4px;">
                        Цвет: {item['color']}
                    </div>
                    <div style="color: #666; font-size: 14px; margin-bottom: 4px;">
                        Размер: {item['size']}
                    </div>
                    <div style="font-weight: bold; font-size: 16px; color: #000;">
                        {int(item['price'])} ₸
                    </div>
                </div>
                
                <!-- Кнопка удаления и количество -->
                <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 10px;">
                    <div style="text-align: center;">
                        <span style="color: #666; font-size: 14px;">Кол-во: 1</span>
                    </div>
                    <button onclick="removeItem({i})" 
                            style="padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; 
                                   background: white; color: #ff4444; cursor: pointer; font-size: 14px;">
                        Удалить
                    </button>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        total += item['price']
    
    # Итого и кнопки
    st.markdown(f"### Итого: {int(total)} ₸")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Продолжить покупки", use_container_width=True):
            st.switch_page("main.py")
    with col2:
        if st.button("Оформить заказ →", type="primary", use_container_width=True):
            st.info("Функция оформления заказа в разработке. Скоро вы сможете оплачивать заказы онлайн!")

    # JavaScript для удаления товаров
    st.markdown(
        f"""
        <script>
        function removeItem(index) {{
            // Отправляем запрос на удаление товара
            fetch('/?remove_index=' + index, {{method: 'POST'}}).then(() => {{
                window.location.reload();
            }});
        }}
        </script>
        """,
        unsafe_allow_html=True
    )

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