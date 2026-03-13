import os
import hashlib
import shutil
import logging
from datetime import datetime

logger = logging.getLogger("FileFlow")

class CleanupModule:
    def __init__(self, root_path, settings):
        self.root = root_path
        # Папка карантина внутри сортируемой директории
        self.quarantine = os.path.join(root_path, settings['cleanup']['quarantine_folder'])
        self.settings = settings
        os.makedirs(self.quarantine, exist_ok=True)

    def get_hash(self, filepath):
        """Вычисляет MD5 хеш файла для поиска дубликатов"""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                for block in iter(lambda: f.read(4096), b''):
                    hasher.update(block)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Ошибка хеширования {filepath}: {e}")
            return None

    def find_junk(self, files):
        """Ищет файлы с мусорными расширениями"""
        junk_exts = self.settings['cleanup']['junk_extensions']
        junk_list = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in junk_exts:
                junk_list.append((f, "junk"))
        return junk_list

    def find_old_files(self, files, days_threshold):
        """Ищет файлы старше заданного порога"""
        old_list = []
        now = datetime.now()
        for f in files:
            try:
                mtime = os.path.getmtime(f)
                file_date = datetime.fromtimestamp(mtime)
                if (now - file_date).days > days_threshold:
                    old_list.append((f, "old"))
            except Exception as e:
                logger.error(f"Ошибка проверки даты {f}: {e}")
        return old_list

    def move_to_quarantine(self, filepath, reason):
        """Перемещает файл в карантин"""
        try:
            name = os.path.basename(filepath)
            # Добавляем метку к имени, чтобы не затереть файлы
            dest = os.path.join(self.quarantine, f"{reason}_{name}")
            shutil.move(filepath, dest)
            logger.info(f"Карантин: {name} ({reason})")
            return True
        except Exception as e:
            logger.error(f"Ошибка карантина {filepath}: {e}")
            return False