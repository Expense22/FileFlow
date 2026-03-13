import sys
from pathlib import Path

def main():
    """Точка входа в приложение"""
    
    # Проверка аргументов командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        # Запуск консольной версии (для тестов)
        from main_console import run_console
        run_console()
    else:
        # Запуск графической версии
        from ui.main_window import run_app
        run_app()

if __name__ == "__main__":
    main()