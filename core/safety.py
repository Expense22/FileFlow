import os
import logging

logger = logging.getLogger("FileFlow")

def validate_root_path(path):
    """
    Проверяет безопасность корневой папки.
    Возвращает: (True/False, Сообщение)
    """
    path_norm = os.path.normpath(path).lower()
    
    # 1. Запрет на корень диска
    if os.path.dirname(path) == path:
        return False, "Выбор корня диска запрещен."

    # 2. Проверка на системные папки
    system_drive = os.environ.get('SystemDrive', 'C:').lower()
    if path_norm.startswith(system_drive):
        relative = path_norm[len(system_drive):].lstrip('\\')
        parts = relative.split('\\')
        
        # Если первая папка системная — блокируем
        forbidden = ['windows', 'program files', 'program files (x86)', 'programdata']
        if parts and parts[0] in forbidden:
            return False, "Обнаружена системная папка ОС."

    # 3. Проверка на критические файлы
    critical_files = ['ntoskrnl.exe', 'pagefile.sys', 'bootmgr']
    try:
        for f in os.listdir(path):
            if f.lower() in critical_files:
                return False, f"Обнаружен системный файл: {f}"
    except PermissionError:
        pass

    return True, "OK"