def create_simple_image_slider(image_paths, slider_id):
    """Создает простой слайдер изображений"""
    if not image_paths or len(image_paths) == 0:
        return "<div>No images</div>"
    
    images_base64 = [get_image_base64(img_path) for img_path in image_paths]
    
    if len(images_base64) == 1:
        # Если только одно изображение, просто показываем его
        return f"""
        <div style="width: 100%; border-radius: 12px; overflow: hidden;">
            <img src="data:image/jpeg;base64,{images_base64[0]}" 
                 style="width: 100%; height: 220px; object-fit: cover; border-radius: 12px;">
        </div>
        """
    
    # Для нескольких изображений создаем слайдер
    # Используем простой числовой идентификатор
    simple_slider_id = f"slider_{hash(slider_id) % 10000}"
    
    slider_html = f"""
    <div id="{simple_slider_id}" style="position: relative; width: 100%; margin: 0 auto; overflow: hidden; border-radius: 12px;">
        <div class="slides_{simple_slider_id}" style="display: flex; transition: transform 0.5s ease; width: {len(images_base64) * 100}%;">
    """
    
    for i, img_base64 in enumerate(images_base64):
        slider_html += f"""
            <div class="slide_{simple_slider_id}" style="width: {100/len(images_base64)}%; flex-shrink: 0;">
                <img src="data:image/jpeg;base64,{img_base64}" 
                     style="width: 100%; height: 220px; object-fit: cover; border-radius: 12px;">
            </div>
        """
    
    slider_html += f"""
        </div>
        
        <!-- Стрелки -->
        <button onclick="prevSlide_{simple_slider_id}()" 
                style="position: absolute; top: 50%; left: 10px; transform: translateY(-50%); 
                       background: rgba(255,255,255,0.7); border: none; border-radius: 50%; 
                       width: 35px; height: 35px; font-size: 18px; cursor: pointer; 
                       display: flex; align-items: center; justify-content: center;">
            ‹
        </button>
        <button onclick="nextSlide_{simple_slider_id}()" 
                style="position: absolute; top: 50%; right: 10px; transform: translateY(-50%); 
                       background: rgba(255,255,255,0.7); border: none; border-radius: 50%; 
                       width: 35px; height: 35px; font-size: 18px; cursor: pointer;
                       display: flex; align-items: center; justify-content: center;">
            ›
        </button>
        
        <!-- Точки-индикаторы -->
        <div style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); 
                    display: flex; gap: 5px;">
    """
    
    for i in range(len(images_base64)):
        slider_html += f"""
            <span onclick="goToSlide_{simple_slider_id}({i})"
                  style="width: 8px; height: 8px; background: {'#fff' if i == 0 else 'rgba(255,255,255,0.5)'}; 
                         border-radius: 50%; cursor: pointer; transition: background 0.3s;">
            </span>
        """
    
    slider_html += f"""
        </div>
    </div>
    
    <script>
    let currentSlide_{simple_slider_id} = 0;
    const totalSlides_{simple_slider_id} = {len(images_base64)};
    
    function updateSlider_{simple_slider_id}() {{
        const slides = document.querySelector('.slides_{simple_slider_id}');
        if (slides) {{
            slides.style.transform = `translateX(-${{currentSlide_{simple_slider_id} * (100 / totalSlides_{simple_slider_id})}}%)`;
            
            // Обновляем точки
            const dots = document.querySelectorAll('[onclick*="goToSlide_{simple_slider_id}"]');
            dots.forEach((dot, index) => {{
                dot.style.background = index === currentSlide_{simple_slider_id} ? '#fff' : 'rgba(255,255,255,0.5)';
            }});
        }}
    }}
    
    function nextSlide_{simple_slider_id}() {{
        currentSlide_{simple_slider_id} = (currentSlide_{simple_slider_id} + 1) % totalSlides_{simple_slider_id};
        updateSlider_{simple_slider_id}();
    }}
    
    function prevSlide_{simple_slider_id}() {{
        currentSlide_{simple_slider_id} = (currentSlide_{simple_slider_id} - 1 + totalSlides_{simple_slider_id}) % totalSlides_{simple_slider_id};
        updateSlider_{simple_slider_id}();
    }}
    
    function goToSlide_{simple_slider_id}(index) {{
        currentSlide_{simple_slider_id} = index;
        updateSlider_{simple_slider_id}();
    }}
    
    // Инициализация при загрузке
    document.addEventListener('DOMContentLoaded', function() {{
        updateSlider_{simple_slider_id}();
        
        // Добавляем обработчики свайпа
        const slider = document.getElementById('{simple_slider_id}');
        if (slider) {{
            let startX = 0;
            let endX = 0;
            
            slider.addEventListener('touchstart', (e) => {{
                startX = e.touches[0].clientX;
            }});
            
            slider.addEventListener('touchend', (e) => {{
                endX = e.changedTouches[0].clientX;
                
                if (startX - endX > 50) {{
                    nextSlide_{simple_slider_id}();
                }} else if (endX - startX > 50) {{
                    prevSlide_{simple_slider_id}();
                }}
            }});
        }}
    }});
    </script>
    """
    
    return slider_html