import os
import shutil
import json
import logging
import stat
from datetime import datetime
from core.safety import validate_root_path
from core.exclusions import ProjectGuard
from core.cleanup import CleanupModule

logger = logging.getLogger("FileFlow")


def is_program_folder(folder_path, files):
    """
    Проверяет, является ли папка распакованной программой.
    
    Признаки:
    - Есть .exe файлы
    - Есть .dll файлы
    - Есть конфиги программы (.cfg, .ini)
    - Комбинация файлов указывает на программу
    """
    exe_count = 0
    dll_count = 0
    has_config = False
    has_readme = False
    
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        name = file.lower()
        
        if ext == '.exe':
            exe_count += 1
        elif ext == '.dll':
            dll_count += 1
        elif ext in ['.cfg', '.ini', '.conf']:
            has_config = True
        elif name in ['readme.txt', 'readme.md', 'license.txt']:
            has_readme = True
    
    # Программа если есть хотя бы один .exe
    if exe_count > 0:
        return True, f"Найдено EXE файлов: {exe_count}"
    
    # Или DLL + конфиг
    if dll_count > 0 and has_config:
        return True, f"Найдено DLL: {dll_count}, есть конфиг"
    
    return False, None


class FileFlowEngine:
    def __init__(self, config_path, settings_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.rules = data.get('rules', [])
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        self.guard = ProjectGuard(self.settings['project_guard']['signatures'])
        self.cleanup = None
        self.move_history = []

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

    def _is_file_locked(self, filepath):
        """Проверяет, заблокирован ли файл"""
        try:
            with open(filepath, 'r+b'):
                return False
        except PermissionError:
            return True
        except:
            return False

    def _remove_readonly(self, filepath):
        """Снимает атрибут Read-Only"""
        try:
            os.chmod(filepath, stat.S_IWRITE | stat.S_IREAD)
            return True
        except:
            return False

    def run(self, root_path, dry_run=True, gui=None, recursive=True):
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
            # ✅ Пропускаем папки с маркером игнорирования
            if '.fileflow_ignore' in files:
                self._log(f"⏭️ Пропущено (маркер): {root}", gui)
                dirs.clear()
                continue
            
            # ✅ Проверяем, не является ли папка программой
            is_program, reason = is_program_folder(root, files)
            if is_program:
                folder_name = os.path.basename(root)
                self._log(f"🛡️ Защищено (программа): {folder_name} ({reason})", gui)
                self.guard.protected_roots.add(root.lower())
                dirs.clear()
                continue
            
            # Если рекурсия выключена — не идём глубже
            if not recursive:
                dirs.clear()
            
            # Не заходим в карантин
            if self.cleanup and self.cleanup.quarantine in root:
                continue
            
            for file in files:
                filepath = os.path.join(root, file)
                if self.guard.is_protected(filepath):
                    continue
                all_files.append(filepath)

        total_files = len(all_files)
        self._log(f"📁 Всего файлов на обработку: {total_files}", gui)
        if not recursive:
            self._log("📁 Режим: Только текущая папка (без подпапок)", gui)
        else:
            self._log("📂 Режим: С подпапками (рекурсивно)", gui)

        # 5. Очистка (Карантин)
        processed = 0
        skipped = 0
        errors = 0
        
        if self.cleanup:
            junk_list = self.cleanup.find_junk(all_files)
            self._log(f"🗑️ Найдено мусора: {len(junk_list)}", gui)
            
            for f, reason in junk_list:
                if self._is_file_locked(f):
                    self._log(f"⚠️ Пропущено (открыт): {os.path.basename(f)}", gui)
                    skipped += 1
                    processed += 1
                    self._update_progress(processed, total_files, gui)
                    continue
                
                if not dry_run:
                    success = self.cleanup.move_to_quarantine(f, reason)
                    if not success:
                        errors += 1
                        self._log(f"❌ Ошибка карантина: {os.path.basename(f)}", gui)
                else:
                    self._log(f"   [DRY] В карантин: {os.path.basename(f)}", gui)
                
                if f in all_files:
                    all_files.remove(f)
                processed += 1
                self._update_progress(processed, total_files, gui)

        # 6. Сортировка по правилам
        moved_count = 0
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
                
                # Проверка на коллизию имен
                if os.path.exists(new_path):
                    base, ext = os.path.splitext(new_path)
                    new_path = f"{base}_dup{ext}"

                if not dry_run:
                    if self._is_file_locked(filepath):
                        self._log(f"⚠️ Пропущено (открыт): {os.path.basename(filepath)}", gui)
                        skipped += 1
                        processed += 1
                        self._update_progress(processed, total_files, gui)
                        continue
                    
                    try:
                        shutil.move(filepath, new_path)
                        moved_count += 1
                        
                        # Сохраняем в историю
                        self.move_history.append({
                            'original': filepath,
                            'new': new_path,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        logger.info(f"Перемещено: {filepath} -> {new_path}")
                    except PermissionError as e:
                        self._log(f"❌ Нет прав: {os.path.basename(filepath)}", gui)
                        logger.error(f"Нет прав на файл {filepath}: {e}")
                        errors += 1
                    except shutil.Error as e:
                        self._log(f"❌ Ошибка перемещения: {os.path.basename(filepath)}", gui)
                        logger.error(f"Ошибка перемещения {filepath}: {e}")
                        errors += 1
                    except Exception as e:
                        self._log(f"❌ Неизвестная ошибка: {os.path.basename(filepath)}", gui)
                        logger.error(f"Неизвестная ошибка {filepath}: {e}")
                        errors += 1
                else:
                    self._log(f"   [DRY] {rule_name}: {os.path.basename(filepath)}", gui)
                    moved_count += 1
            
            processed += 1
            self._update_progress(processed, total_files, gui)

        # Сохраняем историю
        if not dry_run and self.move_history:
            self.save_history(root_path)

        # Итоговая статистика
        self._log(f"\n=== Готово ===", gui)
        self._log(f"✅ Обработано файлов: {moved_count}", gui)
        self._log(f"⚠️ Пропущено: {skipped}", gui)
        self._log(f"❌ Ошибок: {errors}", gui)
        
        if dry_run:
            self._log("⚠️ Режим Dry Run — файлы не были перемещены!", gui)
        
        self._update_progress(total_files, total_files, gui)
        
        return True

    def save_history(self, root_path):
        """Сохраняет историю перемещений"""
        if not self.move_history:
            return
        
        history_file = os.path.join(root_path, '.fileflow_history.json')
        
        # Загружаем предыдущую историю (если есть)
        previous_history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    previous_history = json.load(f)
            except:
                pass
        
        # Добавляем новую
        previous_history.extend(self.move_history)
        
        # Сохраняем
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(previous_history, f, indent=2, ensure_ascii=False)
        
        logger.info(f"История сохранена: {len(self.move_history)} записей")

    def undo_last_sort(self, root_path):
        """Отменяет последнюю сортировку"""
        history_file = os.path.join(root_path, '.fileflow_history.json')
        
        if not os.path.exists(history_file):
            logger.warning("История не найдена — нечего отменять")
            return False, "История не найдена"
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                return False, "История пуста"
            
            # Отменяем в обратном порядке
            undone = 0
            errors = 0
            
            for entry in reversed(history):
                original = entry['original']
                new_path = entry['new']
                
                if os.path.exists(new_path):
                    try:
                        # Создаём исходную папку если нет
                        os.makedirs(os.path.dirname(original), exist_ok=True)
                        
                        # Возвращаем файл
                        shutil.move(new_path, original)
                        undone += 1
                        logger.info(f"Возвращено: {new_path} -> {original}")
                    except Exception as e:
                        errors += 1
                        logger.error(f"Ошибка отмены {new_path}: {e}")
                else:
                    logger.warning(f"Файл не найден: {new_path}")
            
            # Очищаем историю после отмены
            os.remove(history_file)
            
            success = undone > 0 and errors == 0
            return success, f"Отменено: {undone}, Ошибок: {errors}"
            
        except Exception as e:
            logger.error(f"Ошибка отмены: {e}")
            return False, str(e)