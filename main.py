df = load_data()

# --- ДЕТАЛЬНАЯ ДИАГНОСТИКА ---
st.sidebar.write("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА:")
st.sidebar.write("Доступные столбцы:", df.columns.tolist())
st.sidebar.write("Всего товаров:", len(df))

# Проверяем колонку image
if "image" in df.columns:
    st.sidebar.write("---")
    st.sidebar.write("📷 АНАЛИЗ КОЛОНКИ IMAGE:")
    st.sidebar.write("Примеры значений:", df["image"].head(5).tolist())
    st.sidebar.write("Пустые значения:", df["image"].isna().sum())
    
    # Проверяем структуру папки с изображениями
    st.sidebar.write("---")
    st.sidebar.write("📁 СТРУКТУРА ПАПКИ С ИЗОБРАЖЕНИЯМИ:")
    all_image_files = glob.glob(os.path.join(IMAGES_PATH, "**", "*"), recursive=True)
    image_files = [f for f in all_image_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    st.sidebar.write(f"Всего изображений в папке: {len(image_files)}")
    
    if image_files:
        st.sidebar.write("Примеры файлов:")
        for f in image_files[:5]:
            st.sidebar.write(f" - {os.path.basename(f)}")
    
    # Тестируем поиск для первых 3 товаров
    st.sidebar.write("---")
    st.sidebar.write("🔎 ТЕСТ ПОИСКА ФАЙЛОВ:")
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        image_name = row["image"]
        st.sidebar.write(f"Товар {i+1}: '{image_name}'")
        
        if image_name and str(image_name).strip():
            # Показываем все варианты поиска
            image_name = str(image_name).strip()
            
            # Вариант 1: точное совпадение с расширениями
            found_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                pattern = os.path.join(IMAGES_PATH, "**", f"{image_name}{ext}")
                files = glob.glob(pattern, recursive=True)
                found_files.extend(files)
                
                # Вариант 2: файлы начинающиеся с этого имени
                pattern_start = os.path.join(IMAGES_PATH, "**", f"{image_name}*{ext}")
                files_start = glob.glob(pattern_start, recursive=True)
                found_files.extend(files_start)
            
            if found_files:
                st.sidebar.write(f"  ✅ Найдены файлы:")
                for f in found_files:
                    st.sidebar.write(f"    - {os.path.basename(f)}")
            else:
                st.sidebar.write(f"  ❌ Файлы не найдены")
                # Показываем что есть в папке
                similar_files = [f for f in image_files if image_name in os.path.basename(f).lower()]
                if similar_files:
                    st.sidebar.write(f"  Похожие файлы в папке:")
                    for f in similar_files[:3]:
                        st.sidebar.write(f"    - {os.path.basename(f)}")
        else:
            st.sidebar.write(f"  ⚠️ Пустое значение")

# --- Функция для поиска файлов с логированием ---
def debug_get_image_path(image_name):
    """Версия функции с логированием для отладки"""
    if not image_name or pd.isna(image_name) or str(image_name).strip() == "":
        st.sidebar.write(f"🔍 DEBUG: Пустое имя файла, возвращаем no_image")
        return os.path.join(IMAGES_PATH, "no_image.jpg")
    
    image_name = str(image_name).strip()
    st.sidebar.write(f"🔍 DEBUG: Поиск файла '{image_name}'")
    
    # Ищем файл с разными расширениями
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        pattern = os.path.join(IMAGES_PATH, "**", f"{image_name}{ext}")
        image_files = glob.glob(pattern, recursive=True)
        if image_files:
            st.sidebar.write(f"✅ DEBUG: Найден файл {image_files[0]}")
            return image_files[0]
        
        # Также ищем файлы, которые начинаются с этого имени
        pattern_start = os.path.join(IMAGES_PATH, "**", f"{image_name}*{ext}")
        image_files = glob.glob(pattern_start, recursive=True)
        if image_files:
            st.sidebar.write(f"✅ DEBUG: Найден файл по шаблону {image_files[0]}")
            return image_files[0]
    
    st.sidebar.write(f"❌ DEBUG: Файл '{image_name}' не найден")
    return os.path.join(IMAGES_PATH, "no_image.jpg")

# Временно используем отладочную функцию
get_image_path = debug_get_image_path

# --- Остальной код фильтров и отображения ---
st.divider()
st.markdown("### 🔎 Фильтр каталога")

col1, col2, col3, col4, col5, col6 = st.columns(6)
brand_filter = col1.selectbox("Бренд", ["Все"] + sorted(df["brand"].unique().tolist()))

# ... остальной код без изменений