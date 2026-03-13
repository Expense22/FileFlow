import os
import shutil
import json
import logging
from core.safety import validate_root_path
from core.exclusions import ProjectGuard
from core.cleanup import CleanupModule

logger = logging.getLogger("FileFlow")

class FileFlowEngine:
    def __init__(self, config_path, settings_path):
        # Загрузка правил сортировки
        with open(config_path, 'r', encoding='utf-8') as f:
            self.rules = json.load(f)['rules']
        
        # Загрузка настроек
        with open(settings_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        # Инициализация модулей
        self.guard = ProjectGuard(self.settings['project_guard']['signatures'])
        self.cleanup = None

    def _log(self, message, gui=None):
        """
        Универсальная функция логов: пишет и в консоль, и в GUI (если есть)
        """
        print(message)  # В консоль
        if gui:
            gui.log(message)  # В окно программы
        logger.info(message)  # В файл логов

    def run(self, root_path, dry_run=True, gui=None):
        """
        Главный метод сортировки.
        dry_run=True — тестовый режим (без реального перемещения)
        gui — объект окна GUI для логирования (опционально)
        """
        self._log(f"=== Запуск FileFlow для: {root_path} ===", gui)
        
        # 1. Проверка безопасности
        safe, msg = validate_root_path(root_path)
        if not safe:
            error_msg = f"БЕЗОПАСНОСТЬ: {msg}"
            self._log(error_msg, gui)
            logger.error(error_msg)
            return False
        
        self._log(f"✅ Путь безопасен: {root_path}", gui)
        
        # 2. Сканирование проектов
        if self.settings['project_guard']['enabled']:
            self.guard.scan(root_path)
            self._log(f"🛡️ Защищено проектов: {len(self.guard.protected_roots)}", gui)

        # 3. Инициализация очистки
        if self.settings['cleanup']['enabled']:
            self.cleanup = CleanupModule(root_path, self.settings)

        # 4. Сбор всех файлов
        all_files = []
        for root, dirs, files in os.walk(root_path):
            # Не заходим в карантин
            if self.cleanup and self.cleanup.quarantine in root:
                continue
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Проверка защиты проектов
                if self.guard.is_protected(filepath):
                    logger.debug(f"Пропущено (проект): {filepath}")
                    continue
                
                all_files.append(filepath)

        self._log(f"📁 Всего файлов на обработку: {len(all_files)}", gui)

        # 5. Очистка (Карантин)
        if self.cleanup:
            junk_list = self.cleanup.find_junk(all_files)
            self._log(f"🗑️ Найдено мусора: {len(junk_list)}", gui)
            
            for f, reason in junk_list:
                if not dry_run:
                    self.cleanup.move_to_quarantine(f, reason)
                else:
                    self._log(f"   [DRY] В карантин: {os.path.basename(f)}", gui)
                # Удаляем из списка обработки
                if f in all_files:
                    all_files.remove(f)

        # 6. Сортировка по правилам
        moved_count = 0
        for filepath in all_files:
            ext = os.path.splitext(filepath)[1].lower()
            dest_folder = None
            
            # Поиск подходящего правила
            for rule in self.rules:
                if ext in rule['extensions']:
                    dest_folder = os.path.join(root_path, rule['destination'])
                    break
            
            if dest_folder:
                os.makedirs(dest_folder, exist_ok=True)
                new_path = os.path.join(dest_folder, os.path.basename(filepath))
                
                # Проверка на коллизию имен
                if os.path.exists(new_path):
                    base, ext = os.path.splitext(new_path)
                    new_path = f"{base}_dup{ext}"

                if not dry_run:
                    try:
                        shutil.move(filepath, new_path)
                        moved_count += 1
                        logger.info(f"Перемещено: {filepath} -> {new_path}")
                    except Exception as e:
                        error_msg = f"Ошибка перемещения {filepath}: {e}"
                        self._log(f"❌ {error_msg}", gui)
                        logger.error(error_msg)
                else:
                    self._log(f"   [DRY] Переместить: {os.path.basename(filepath)} -> {rule['destination']}", gui)
                    moved_count += 1

        self._log(f"\n=== Готово. Обработано файлов: {moved_count} ===", gui)
        if dry_run:
            self._log("⚠️ Режим Dry Run — файлы не были перемещены!", gui)
        
        return True