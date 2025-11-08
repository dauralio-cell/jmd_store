import streamlit as st
import os
import base64

DOCUMENTS_PATH = "data/documents"

def create_sample_documents():
    """Создает документы если они не существуют"""
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    
    # Публичная оферта
    public_offer = """
ДОГОВОР ПУБЛИЧНОЙ ОФЕРТЫ
интернет-магазина DENE Store

г. Астана "01" января 2025 г.

[Полный текст оферты...]
"""
    
    # Политика конфиденциальности  
    privacy_policy = """
ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ
интернет-магазина DENE Store

г. Астана "01" января 2025 г.

[Полный текст политики...]
"""
    
    # Условия возврата
    return_policy = """
УСЛОВИЯ ВОЗВРАТА ТОВАРА
интернет-магазина DENE Store

г. Астана "01" января 2025 г.

[Полный текст условий возврата...]
"""
    
    documents = {
        "public_offer.txt": public_offer,
        "privacy_policy.txt": privacy_policy, 
        "return_policy.txt": return_policy
    }
    
    for filename, content in documents.items():
        filepath = os.path.join(DOCUMENTS_PATH, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Создает ссылку для скачивания файла"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" style="color: #666; text-decoration: none;">{file_label}</a>'
    return href

def documents_footer():
    """Упрощенный футер только со ссылками для скачивания"""
    
    # Создаем документы при первом вызове
    create_sample_documents()
    
    st.markdown("---")
    
    # Простой футер как на картинке
    st.markdown(
        """
        <div style="text-align: center; color: #666; font-size: 14px; line-height: 1.5;">
            <p>© DENE Store 2025</p>
            <p>+7 747 555 48 69 • jmd.dene@gmail.com • Instagram @jmd.dene</p>
            <p>
                {offer_link} • {privacy_link} • {return_link}
            </p>
        </div>
        """.format(
            offer_link=get_binary_file_downloader_html(os.path.join(DOCUMENTS_PATH, "public_offer.txt"), "Публичная оферта"),
            privacy_link=get_binary_file_downloader_html(os.path.join(DOCUMENTS_PATH, "privacy_policy.txt"), "Политика конфиденциальности"),
            return_link=get_binary_file_downloader_html(os.path.join(DOCUMENTS_PATH, "return_policy.txt"), "Условия возврата")
        ),
        unsafe_allow_html=True
    )