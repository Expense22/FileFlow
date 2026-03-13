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
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.rules = data.get('rules', [])
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.guard = ProjectGuard(self.settings['project_guard']['signatures'])
        self.cleanup = None

    def _log(self, message, gui=None):
        """Универсальная функция логов"""
        print(message)
        if gui:
            gui.log(message)
        logger.info(message)

    def _update_progress(self, current, total, gui=None):
        """Обновляет прогресс-бар"""
        if gui and hasattr(gui, 'update_progress'):
            gui.update_progress(current, total)

    def run(self, root_path, dry_run=True, gui=None):
        """Главный метод сортировки"""
        self._log(f"=== Запуск FileFlow для: {root_path} ===", gui)
        
        # 1. Проверка безопасности
        safe, msg = validate_root_path(root_path)
        if not safe:
            self._log(f"❌ {msg}", gui)
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
            if self.cleanup and self.cleanup.quarantine in root:
                continue
            
            for file in files:
                filepath = os.path.join(root, file)
                if self.guard.is_protected(filepath):
                    continue
                all_files.append(filepath)

        total_files = len(all_files)
        self._log(f"📁 Всего файлов на обработку: {total_files}", gui)

        # 5. Очистка (Карантин)
        processed = 0
        if self.cleanup:
            junk_list = self.cleanup.find_junk(all_files)
            self._log(f"🗑️ Найдено мусора: {len(junk_list)}", gui)
            
            for f, reason in junk_list:
                if not dry_run:
                    self.cleanup.move_to_quarantine(f, reason)
                else:
                    self._log(f"   [DRY] В карантин: {os.path.basename(f)}", gui)
                if f in all_files:
                    all_files.remove(f)
                processed += 1
                self._update_progress(processed, total_files, gui)

        # 6. Сортировка по правилам
        moved_count = 0
        # Фильтруем только включённые правила
        active_rules = [r for r in self.rules if r.get('enabled', True)]
        
        for filepath in all_files:
            ext = os.path.splitext(filepath)[1].lower()
            dest_folder = None
            rule_name = None
            
            for rule in active_rules:
                if ext in rule['extensions']:
                    dest_folder = os.path.join(root_path, rule['destination'])
                    rule_name = rule['name']
                    break
            
            if dest_folder:
                os.makedirs(dest_folder, exist_ok=True)
                new_path = os.path.join(dest_folder, os.path.basename(filepath))
                
                if os.path.exists(new_path):
                    base, ext = os.path.splitext(new_path)
                    new_path = f"{base}_dup{ext}"

                if not dry_run:
                    try:
                        shutil.move(filepath, new_path)
                        moved_count += 1
                        logger.info(f"Перемещено: {filepath} -> {new_path}")
                    except Exception as e:
                        self._log(f"❌ Ошибка: {e}", gui)
                else:
                    self._log(f"   [DRY] {rule_name}: {os.path.basename(filepath)}", gui)
                    moved_count += 1
            
            processed += 1
            self._update_progress(processed, total_files, gui)

        self._log(f"\n=== Готово. Обработано файлов: {moved_count} ===", gui)
        if dry_run:
            self._log("⚠️ Режим Dry Run — файлы не были перемещены!", gui)
        
        # Завершаем прогресс
        self._update_progress(total_files, total_files, gui)
        
        return True