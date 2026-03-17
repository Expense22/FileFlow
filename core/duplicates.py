"""
Модуль поиска дубликатов файлов
FileFlow - Умная сортировка файлов
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


class DuplicateFinder:
    """Поиск дубликатов файлов по хешу содержимого"""
    
    def __init__(self, chunk_size=8192):
        """
        Инициализация поисковика дубликатов
        
        Args:
            chunk_size: Размер чанка для чтения файла (8KB по умолчанию)
        """
        self.chunk_size = chunk_size
        self.duplicates = {}
        self.total_space_waste = 0
        self.files_processed = 0
        self.total_files = 0
    
    def calculate_hash(self, filepath: str) -> str:
        """
        Вычисляет SHA-256 хеш файла
        
        Args:
            filepath: Путь к файлу
            
        Returns:
            HEX строка хеша или пустая строка при ошибке
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Ошибка хеширования {filepath}: {e}")
            return ""
    
    def find_duplicates(self, folder_path: str, recursive: bool = True, 
                       min_size: int = 10240, callback=None) -> Dict[str, List[str]]:
        """
        Ищет дубликаты файлов в папке
        
        Args:
            folder_path: Путь к папке для сканирования
            recursive: Искать в подпапках (True) или только в корневой (False)
            min_size: Минимальный размер файла в байтах (по умолчанию 10KB)
            callback: Функция обратного вызова для прогресса callback(current, total)
        
        Returns:
            Словарь {hash: [список путей к файлам-дубликатам]}
        """
        self.duplicates = {}
        self.total_space_waste = 0
        self.files_processed = 0
        self.total_files = 0
        
        # ═══════════════════════════════════════════════════
        # ШАГ 1: Собираем файлы и группируем по размеру
        # ═══════════════════════════════════════════════════
        size_groups = defaultdict(list)
        all_files = []
        
        # Папки для пропуска
        skip_folders = {
            'venv', '__pycache__', '.git', '.vscode', 
            'node_modules', '.idea', 'dist', 'build'
        }
        
        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    # Пропускаем системные папки
                    dirs[:] = [d for d in dirs if d not in skip_folders and not d.startswith('.')]
                    
                    for file in files:
                        filepath = os.path.join(root, file)
                        try:
                            size = os.path.getsize(filepath)
                            if size >= min_size:
                                size_groups[size].append(filepath)
                                all_files.append(filepath)
                        except (OSError, IOError):
                            pass
            else:
                for file in os.listdir(folder_path):
                    filepath = os.path.join(folder_path, file)
                    if os.path.isfile(filepath):
                        try:
                            size = os.path.getsize(filepath)
                            if size >= min_size:
                                size_groups[size].append(filepath)
                                all_files.append(filepath)
                        except (OSError, IOError):
                            pass
            
            self.total_files = len(all_files)
            
        except Exception as e:
            raise Exception(f"Ошибка сканирования папки: {e}")
        
        # ═══════════════════════════════════════════════════
        # ШАГ 2: Для файлов с одинаковым размером считаем хеш
        # ═══════════════════════════════════════════════════
        hash_groups = defaultdict(list)
        self.files_processed = 0
        
        # Обрабатываем только группы с потенциальными дубликатами (2+ файла)
        potential_duplicates = {size: files for size, files in size_groups.items() if len(files) > 1}
        
        for size, files in potential_duplicates.items():
            for filepath in files:
                try:
                    file_hash = self.calculate_hash(filepath)
                    if file_hash:
                        hash_groups[file_hash].append(filepath)
                except Exception:
                    pass
                
                self.files_processed += 1
                
                # ✅ Обновляем прогресс
                if callback and self.total_files > 0:
                    try:
                        callback(self.files_processed, self.total_files)
                    except:
                        pass
        
        # ═══════════════════════════════════════════════════
        # ШАГ 3: Оставляем только группы с дубликатами (2+ файла)
        # ═══════════════════════════════════════════════════
        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                self.duplicates[file_hash] = sorted(files)
                
                # Считаем wasted space
                try:
                    file_size = os.path.getsize(files[0])
                    self.total_space_waste += file_size * (len(files) - 1)
                except:
                    pass
        
        return self.duplicates
    
    def get_wasted_space(self) -> int:
        """Возвращает общий размер дубликатов в байтах"""
        return self.total_space_waste
    
    def get_duplicates_count(self) -> int:
        """Возвращает количество дубликатов (лишних копий)"""
        count = 0
        for files in self.duplicates.values():
            count += len(files) - 1
        return count
    
    def get_groups_count(self) -> int:
        """Возвращает количество групп дубликатов"""
        return len(self.duplicates)
    
    def get_total_files(self) -> int:
        """Возвращает общее количество обработанных файлов"""
        return self.total_files
    
    def delete_duplicates(self, files_to_delete: List[str]) -> Tuple[int, int]:
        """
        Удаляет указанные дубликаты
        
        Args:
            files_to_delete: Список путей к файлам для удаления
        
        Returns:
            Кортеж (удалено файлов, освобождено байт)
        """
        deleted_count = 0
        freed_space = 0
        
        for filepath in files_to_delete:
            try:
                size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted_count += 1
                freed_space += size
            except Exception as e:
                print(f"Ошибка удаления {filepath}: {e}")
        
        return deleted_count, freed_space
    
    def format_size(self, size_bytes: int) -> str:
        """Форматирует размер файла для отображения"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


# ═══════════════════════════════════════════════════════════
# Пример использования (для тестирования)
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    
    print("🔍 FileFlow Duplicate Finder")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("Введите путь к папке: ").strip('"')
    
    if not os.path.exists(folder):
        print(f"❌ Папка не найдена: {folder}")
        sys.exit(1)
    
    finder = DuplicateFinder()
    
    def progress(current, total):
        percent = (current / total * 100) if total > 0 else 0
        print(f"\r📊 Прогресс: {percent:.1f}% ({current}/{total})", end="", flush=True)
    
    print(f"\n🔍 Сканирование: {folder}")
    duplicates = finder.find_duplicates(folder, callback=progress)
    
    print(f"\n\n✅ Найдено групп дубликатов: {finder.get_groups_count()}")
    print(f"📁 Лишних файлов: {finder.get_duplicates_count()}")
    print(f"💾 Можно освободить: {finder.format_size(finder.get_wasted_space())}")