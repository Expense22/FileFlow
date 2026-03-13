import os
import json
from pathlib import Path
from core.logger import setup_logger
from core.safety import validate_root_path

def main():
    logger = setup_logger()
    print("=== Запуск FileFlow v0.1 ===")
    
    # Проверка конфигов
    base_dir = Path(__file__).parent
    settings_path = base_dir / 'config' / 'settings.json'
    
    if not settings_path.exists():
        print("❌ Ошибка: Файл настроек не найден!")
        return

    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
        print(f"📛 Проект: {settings.get('project_name')}")

    # Тест безопасности
    test_path = input("\nВведите путь для проверки (или Enter для пропуска): ").strip()
    
    if test_path:
        safe, msg = validate_root_path(test_path)
        if safe:
            print(f"✅ {msg}")
            logger.info(f"Проверка пути успешна: {test_path}")
        else:
            print(f"❌ {msg}")
            logger.error(f"Проверка пути провалена: {test_path} - {msg}")
    
    print("\n=== Тест завершен ===")

if __name__ == "__main__":
    main()