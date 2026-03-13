import os

class ProjectGuard:
    def __init__(self, signatures):
        # Приводим все расширения к нижнему регистру для точного сравнения
        self.signatures = [s.lower() for s in signatures]
        self.protected_roots = set()

    def scan(self, root_path):
        """
        Находит папки с проектами по сигнатурным файлам.
        Эти папки будут защищены от сортировки.
        """
        for dirpath, dirnames, filenames in os.walk(root_path):
            for file in filenames:
                ext = os.path.splitext(file)[1].lower()
                # Если файл совпадает с сигнатурой — помечаем папку как защищенную
                if ext in self.signatures or file.lower() in self.signatures:
                    self.protected_roots.add(dirpath)
                    break # Достаточно одного файла, чтобы защитить всю папку
    
    def is_protected(self, filepath):
        """
        Проверяет, находится ли файл внутри защищенной зоны.
        """
        file_dir = os.path.dirname(filepath)
        for root in self.protected_roots:
            if file_dir.startswith(root):
                return True
        return False