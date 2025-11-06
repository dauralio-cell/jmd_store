# ... (импорты и функции остаются без изменений) ...

# В основной функции после блока с другими цветами:

    # --- Информация о доставке и возврате ---
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

# УБРАТЬ эти блоки:
# --- Публичная оферта ---
# --- Кнопка онлайн оплаты ---