import customtkinter as ctk
import os
from pathlib import Path
from core.engine import FileFlowEngine
from core.logger import setup_logger

logger = setup_logger()

class FileFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FileFlow v0.1")
        self.geometry("600x500")
        self.resizable(False, False)

        self.selected_path = ""
        self.is_expert_mode = False
        self.dry_run = True

        self.create_widgets()

    def create_widgets(self):
        """Создает все элементы интерфейса"""
        
        self.title_label = ctk.CTkLabel(
            self, 
            text="🗂️ FileFlow", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

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
        self.mode_switch.select()
        self.mode_switch.pack(side="left", padx=10)

        self.expert_switch = ctk.CTkSwitch(
            self, 
            text="Экспертный режим", 
            command=self.toggle_expert
        )
        self.expert_switch.pack(pady=10)

        self.start_btn = ctk.CTkButton(
            self, 
            text="🚀 Запустить сортировку", 
            command=self.start_sorting,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.start_btn.pack(pady=20, padx=20, fill="x")

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
            self.show_expert_widgets()
        else:
            self.log("📱 Простой режим включен")
            self.hide_expert_widgets()

    def show_expert_widgets(self):
        """Показывает виджеты экспертного режима"""
        if not hasattr(self, 'expert_btn'):
            self.expert_btn = ctk.CTkButton(
                self,
                text="📄 Просмотр правил (JSON)",
                command=self.view_rules,
                fg_color="gray"
            )
            self.settings_btn = ctk.CTkButton(
                self,
                text="⚙️ Настройки безопасности",
                command=self.view_settings,
                fg_color="gray"
            )
        
        self.expert_btn.pack(pady=5, padx=20, fill="x", before=self.start_btn)
        self.settings_btn.pack(pady=5, padx=20, fill="x", before=self.start_btn)

    def hide_expert_widgets(self):
        """Скрывает виджеты экспертного режима"""
        if hasattr(self, 'expert_btn'):
            self.expert_btn.pack_forget()
            self.settings_btn.pack_forget()

    def view_rules(self):
        """Открывает окно с правилами сортировки"""
        rules_window = ctk.CTkToplevel(self)
        rules_window.title("Правила сортировки")
        rules_window.geometry("500x400")
        
        text_box = ctk.CTkTextbox(rules_window, width=480, height=350)
        text_box.pack(pady=10, padx=10)
        
        base_dir = Path(__file__).parent.parent
        rules_path = base_dir / 'config' / 'rules.json'
        
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules_content = f.read()
        
        text_box.insert("0.0", rules_content)
        text_box.configure(state="disabled")
        
        self.log("📄 Правила открыты для просмотра")

    def view_settings(self):
        """Открывает окно с настройками безопасности"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки безопасности")
        settings_window.geometry("500x400")
        
        text_box = ctk.CTkTextbox(settings_window, width=480, height=350)
        text_box.pack(pady=10, padx=10)
        
        base_dir = Path(__file__).parent.parent
        settings_path = base_dir / 'config' / 'settings.json'
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        text_box.insert("0.0", settings_content)
        text_box.configure(state="disabled")
        
        self.log("⚙️ Настройки открыты для просмотра")

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
        self.log_text.see("end")

def run_app():
    """Запуск приложения"""
    app = FileFlowApp()
    app.mainloop()