import streamlit as st

st.set_page_config(page_title="Контакты - DENE Store", layout="wide")

# Кнопка назад
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("← Назад", use_container_width=True):
        st.switch_page("main.py")

st.title("📞 Контакты")

col1, col2 = st.columns(2)

# В блоке контактов:
with col1:
    st.markdown("### Наши контакты")
    st.markdown("**Телефон:** +7 747 555 48 69")  # ← Обновленный номер
    st.markdown("**Email:** jmd.dene@gmail.com")
    # ... остальное без изменений
    st.markdown("**Instagram:** [@jmd.dene](https://instagram.com/jmd.dene)")
    
    st.markdown("### График работы")
    st.markdown("**Пн-Пт:** 9:00 - 18:00")
    st.markdown("**Сб-Вс:** 10:00 - 16:00")

with col2:
    st.markdown("### Доставка и возврат")
    st.markdown("**Срок доставки:** 10-21 день")
    st.markdown("**Возврат:** 14 дней с момента получения")
    st.markdown("**Способ доставки:** Курьерская служба")

st.markdown("---")
st.markdown("### Публичная оферта")
st.markdown("[Скачать договор публичной оферты](#)")
st.markdown("[Политика конфиденциальности](#)")
st.markdown("[Условия возврата](#)")