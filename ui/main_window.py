import customtkinter as ctk
import os
from pathlib import Path
from core.engine import FileFlowEngine
from core.logger import setup_logger

logger = setup_logger()

class FileFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Настройки окна
        self.title("FileFlow v0.1")
        self.geometry("600x500")
        self.resizable(False, False)

        # Переменные
        self.selected_path = ""
        self.is_expert_mode = False
        self.dry_run = True

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        """Создает все элементы интерфейса"""
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self, 
            text="🗂️ FileFlow", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # Выбор папки
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(pady=10, padx=20, fill="x")

        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="Папка не выбрана", 
            width=400,
            anchor="w"
        )
        self.path_label.pack(side="left", padx=10, pady=10)

        self.browse_btn = ctk.CTkButton(
            self.path_frame, 
            text="Выбрать папку", 
            command=self.browse_folder,
            width=120
        )
        self.browse_btn.pack(side="right", padx=10, pady=10)

        # Режим работы
        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=10, padx=20, fill="x")

        self.mode_label = ctk.CTkLabel(
            self.mode_frame, 
            text="Режим работы:"
        )
        self.mode_label.pack(side="left", padx=10)

        self.mode_switch = ctk.CTkSwitch(
            self.mode_frame, 
            text="Dry Run (Тест)", 
            command=self.toggle_mode,
            onvalue=True,
            offvalue=False
        )
        self.mode_switch.select()  # Включено по умолчанию
        self.mode_switch.pack(side="left", padx=10)

        # Экспертный режим
        self.expert_switch = ctk.CTkSwitch(
            self, 
            text="Экспертный режим", 
            command=self.toggle_expert
        )
        self.expert_switch.pack(pady=10)

        # Кнопка запуска
        self.start_btn = ctk.CTkButton(
            self, 
            text="🚀 Запустить сортировку", 
            command=self.start_sorting,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.start_btn.pack(pady=20, padx=20, fill="x")

        # Лог (текстовое поле)
        self.log_text = ctk.CTkTextbox(self, width=550, height=150)
        self.log_text.pack(pady=10, padx=20)
        self.log_text.insert("0.0", "Готов к работе...\n")

    def browse_folder(self):
        """Открывает диалог выбора папки"""
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.selected_path = folder
            self.path_label.configure(text=folder)
            self.log(f"✅ Выбрана папка: {folder}")

    def toggle_mode(self):
        """Переключает режим Dry Run / Live"""
        self.dry_run = self.mode_switch.get()
        if self.dry_run:
            self.log("📋 Режим: Dry Run (тестовый)")
        else:
            self.log("⚠️ Режим: Live (файлы будут перемещены!)")

    def toggle_expert(self):
        """Включает экспертный режим"""
        self.is_expert_mode = self.expert_switch.get()
        if self.is_expert_mode:
            self.log("🔧 Экспертный режим включен")
        else:
            self.log("📱 Простой режим включен")

    def start_sorting(self):
        """Запускает процесс сортировки"""
        if not self.selected_path:
            self.log("❌ Ошибка: Выберите папку!")
            return

        self.log(f"\n=== Запуск сортировки ===")
        self.log(f"Путь: {self.selected_path}")
        self.log(f"Режим: {'Dry Run (Тест)' if self.dry_run else 'LIVE (Работа)'}")
        self.log("-" * 30)

        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            settings_path = base_dir / 'config' / 'settings.json'

            engine = FileFlowEngine(config_path, settings_path)
            
            # Запускаем с передачей self для логирования
            result = engine.run(self.selected_path, dry_run=self.dry_run, gui=self)

            self.log("-" * 30)
            if result:
                self.log("✅ Сортировка завершена успешно!")
            else:
                self.log("❌ Сортировка прервана (ошибка безопасности)")
        except Exception as e:
            self.log(f"❌ Критическая ошибка: {str(e)}")
            logger.error(f"Ошибка в GUI: {e}")

    def log(self, message):
        """Добавляет сообщение в лог-окно"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")  # Прокрутка вниз

def run_app():
    """Запуск приложения"""
    app = FileFlowApp()
    app.mainloop()