def run_console():
import os
import json
from pathlib import Path
from core.logger import setup_logger
from core.safety import validate_root_path
from core.exclusions import ProjectGuard
from core.cleanup import CleanupModule

def main():
    logger = setup_logger()
    print("=== Запуск FileFlow v0.1 ===")
    
    # Загрузка настроек
    base_dir = Path(__file__).parent
    settings_path = base_dir / 'config' / 'settings.json'
    
    if not settings_path.exists():
        print("❌ Ошибка: Файл настроек не найден!")
        return

    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
        print(f"📛 Проект: {settings.get('project_name')}")

    # Тест безопасности (Системные файлы)
    test_path = input("\nВведите путь для проверки (или Enter для пропуска): ").strip()
    
    if test_path:
        # 1. Проверка на системные папки
        safe, msg = validate_root_path(test_path)
        if safe:
            print(f"✅ {msg}")
            logger.info(f"Проверка пути успешна: {test_path}")
            
            # 2. Тест защиты проектов
            if settings['project_guard']['enabled']:
                signatures = settings['project_guard']['signatures']
                guard = ProjectGuard(signatures)
                guard.scan(test_path)
                print(f"🛡️ Найдено защищенных проектов: {len(guard.protected_roots)}")
                if guard.protected_roots:
                    print("   Защищенные папки:", guard.protected_roots)
            
            # 3. Тест очистки
            if settings['cleanup']['enabled']:
                cleanup = CleanupModule(test_path, settings)
                
                # Список всех файлов для теста
                test_files = []
                for root, dirs, files in os.walk(test_path):
                    # Не заходим в карантин
                    if cleanup.quarantine in root:
                        continue
                    for f in files:
                        test_files.append(os.path.join(root, f))
                
                # Поиск мусора
                junk = cleanup.find_junk(test_files)
                print(f"🗑️ Найдено мусорных файлов: {len(junk)}")
                for j_file, reason in junk:
                    print(f"   - {os.path.basename(j_file)}")
                
                # Поиск старых файлов
                old = cleanup.find_old_files(test_files, settings['cleanup']['max_age_days'])
                print(f"📅 Найдено старых файлов: {len(old)}")
                for o_file, reason in old:
                    print(f"   - {os.path.basename(o_file)}")
                
                # Общая статистика
                print(f"\n📊 Всего файлов просканировано: {len(test_files)}")
                print(f"📊 Файлов в проектах (защищено): {sum(1 for f in test_files if guard.is_protected(f))}")
                
        else:
            print(f"❌ {msg}")
            logger.error(f"Проверка пути провалена: {test_path} - {msg}")
    
    print("\n=== Тест завершен ===")
def test_engine():
    """Тест полноценного движка сортировки"""
    base_dir = Path(__file__).parent
    config_path = base_dir / 'config' / 'rules.json'
    settings_path = base_dir / 'config' / 'settings.json'
    
    test_path = input("\nВведите путь для сортировки: ").strip()
    if not test_path:
        return
    
    mode = input("Режим: 1 - Dry Run (Тест), 2 - Live (Работа): ").strip()
    dry_run = (mode != '2')
    
    if dry_run:
        print("\n⚠️ ВНИМАНИЕ: Режим тестирования. Файлы не будут перемещены.")
    else:
        print("\n❗ ВНИМАНИЕ: Файлы будут перемещены реально!")
        confirm = input("Продолжить? (да/нет): ").strip().lower()
        if confirm != 'да':
            print("Отменено.")
            return
    
    from core.engine import FileFlowEngine
    engine = FileFlowEngine(config_path, settings_path)
    engine.run(test_path, dry_run=dry_run)
if __name__ == "__main__":
    main()  # Старый тест модулей
    
    choice = input("\nЗапустить движок сортировки? (да/нет): ").strip().lower()
    if choice == 'да':
        test_engine()

    pass

if __name__ == "__main__":
    run_console()