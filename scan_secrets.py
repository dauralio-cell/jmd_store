import os
import re

# Папка проекта
PROJECT_DIR = os.path.abspath(".")

# Регулярные выражения для поиска потенциальных секретов
patterns = {
    "API_KEY": r"(api[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"])",
    "TOKEN": r"(token\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"])",
    "SECRET": r"(secret\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"])",
    "PASSWORD": r"(password\s*=\s*['\"].+['\"])"
}

def scan_file(file_path):
    found = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for name, pattern in patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    found.append(name)
    except Exception as e:
        print(f"Не удалось прочитать {file_path}: {e}")
    return found

def scan_project():
    issues = {}
    for root, dirs, files in os.walk(PROJECT_DIR):
        # Пропускаем venv и скрытые папки
        if any(x in root for x in ['venv', '.git', '__pycache__']):
            continue
        for file in files:
            if file.endswith((".py", ".env", ".toml", ".txt", ".json", ".yaml", ".yml")):
                path = os.path.join(root, file)
                result = scan_file(path)
                if result:
                    issues[path] = result
    return issues

if __name__ == "__main__":
    found_secrets = scan_project()
    if not found_secrets:
        print("✅ Потенциальные секреты не найдены!")
    else:
        print("⚠️ Внимание! Найдены потенциальные секреты:")
        for path, types in found_secrets.items():
            print(f"{path}: {', '.join(types)}")
