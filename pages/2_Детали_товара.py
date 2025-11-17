import streamlit as st
import pandas as pd
import glob
import os
import re
import base64

# --- Настройки страницы ---
st.set_page_config(page_title="Детали товара - DENE Store", layout="wide")

# --- Стили для кнопок размеров ---
st.markdown("""
<style>
/* Стили для кнопок размеров - автоматическая ширина */
.stButton button {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    padding: 8px 6px !important;
    font-size: 11px !important;
    line-height: 1.1 !important;
    height: auto !important;
    min-height: 36px !important;
    width: 100% !important;
}

/* Убираем лишние отступы вокруг кнопок */
.stButton {
    margin-bottom: 2px !important;
    padding: 0px !important;
    width: 100% !important;
}

/* Автоматическая ширина колонок */
[data-testid="column"] {
    padding: 0px 4px !important;
    width: 100% !important;
}

/* Контейнер для кнопок размеров */
.size-buttons-container {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# --- Остальной код БЕЗ ИЗМЕНЕНИЙ ---
# ... (весь остальной код остается точно таким же как было изначально)

# В секции с размерами просто оборачиваем в контейнер:
with col_right:
    st.markdown("### Доступные размеры")
    
    if sorted_sizes:
        # Инициализируем выбранный размер в session_state
        if 'selected_size' not in st.session_state:
            st.session_state.selected_size = None
        if 'selected_price' not in st.session_state:
            st.session_state.selected_price = None
        
        # Сетка размеров 2 колонки
        cols = st.columns(2)
        selected_size = st.session_state.selected_size
        
        for idx, size_data in enumerate(sorted_sizes):
            with cols[idx % 2]:
                us_size = size_data['us_size']
                eu_size = size_data['eu_size']
                price = size_data['price']
                
                is_selected = selected_size == us_size
                
                # ФОРМАТ КНОПКИ: US 7 / EU 40 - 45 000 ₸ (ВСЕ В ОДНУ СТРОКУ)
                if eu_size:
                    button_text = f"US {us_size}/EU {eu_size} - {int(price):,}₸".replace(",", " ")
                else:
                    button_text = f"US {us_size} - {int(price):,}₸".replace(",", " ")
                
                if st.button(button_text, 
                            key=f"size_{us_size}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"):
                    st.session_state.selected_size = us_size
                    st.session_state.selected_price = price
                    st.rerun()
        
        # ... остальной код без изменений