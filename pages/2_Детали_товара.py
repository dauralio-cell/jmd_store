# --- Другие цвета этой модели ---
other_colors = unique_colors[unique_colors["color"] != current_color]
if not other_colors.empty:
    st.markdown("### Другие цвета")
    st.sidebar.write(f"🎨 Найдено других цветов: {len(other_colors)}")
    
    # Сетка цветов 2 колонки
    color_cols = st.columns(2)
    for idx, (_, variant) in enumerate(other_colors.iterrows()):
        with color_cols[idx % 2]:
            # Показываем уменьшенное изображение для цвета
            st.sidebar.write(f"🔍 Обрабатываем цвет: {variant['color']}")
            st.sidebar.write(f"   Изображения: {variant['image']}")
            
            img_path = get_image_path(variant["image"])
            image_base64 = get_image_base64(img_path)
            
            # Получаем минимальную цену для этого цвета (только размеры в наличии)
            color_sizes = df[
                (df["model_clean"] == variant["model_clean"]) & 
                (df["brand"] == variant["brand"]) &
                (df["color"] == variant["color"])
            ]
            # Фильтруем только размеры в наличии
            available_color_sizes = [
                row for _, row in color_sizes.iterrows()
                if str(row.get('in stock', 'yes')).strip().lower() == 'yes'
                and str(row['size US']).strip() and str(row['size US']).strip() != "nan"
            ]
            
            if available_color_sizes:
                # ОКРУГЛЯЕМ ЦЕНУ ДО ТЫСЯЧ
                min_color_price = min(round_price(row['price']) for row in available_color_sizes)
                
                # Карточка цвета
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 6px;
                        text-align: center;
                        margin-bottom: 8px;
                        background-color: white;
                    ">
                        <img src="data:image/jpeg;base64,{image_base64}" 
                             style="width:100%; border-radius:4px; height:80px; object-fit:cover;">
                        <div style="margin-top:6px; font-weight:bold; font-size:12px;">{variant['color'].capitalize()}</div>
                        <div style="font-size:11px; color:#666;">от {int(min_color_price):,} ₸</div>
                    </div>
                    """.replace(",", " "),
                    unsafe_allow_html=True
                )
                
                # Кнопка переключения на этот цвет
                if st.button(f"Выбрать", key=f"color_{variant['color']}", use_container_width=True):
                    st.session_state.selected_size = None  # Сбрасываем выбранный размер
                    st.session_state.selected_price = None
                    st.session_state.product_data = dict(variant)
                    st.rerun()