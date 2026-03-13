import customtkinter as ctk
import os
from pathlib import Path
from core.engine import FileFlowEngine
from core.logger import setup_logger
import json

logger = setup_logger()

class FileFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FileFlow v0.2")
        self.geometry("650x600")
        self.resizable(False, False)

        self.selected_path = ""
        self.is_expert_mode = False
        self.dry_run = True
        self.rule_states = {}

        self.create_widgets()

    def create_widgets(self):
        """Создает все элементы интерфейса"""
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self, 
            text="🗂️ FileFlow v0.2", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=15)

        # Выбор папки
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.pack(pady=10, padx=20, fill="x")

        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text="Папка не выбрана", 
            width=450,
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

        self.mode_label = ctk.CTkLabel(self.mode_frame, text="Режим работы:")
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

        # Экспертный режим
        self.expert_switch = ctk.CTkSwitch(
            self, 
            text="Экспертный режим", 
            command=self.toggle_expert
        )
        self.expert_switch.pack(pady=10)

        # Прогресс-бар (скрыт по умолчанию)
        self.progress_bar = ctk.CTkProgressBar(self, width=550)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self, text="")

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
            self.show_expert_widgets()
        else:
            self.log("📱 Простой режим включен")
            self.hide_expert_widgets()

    def show_expert_widgets(self):
        """Показывает виджеты экспертного режима"""
        if not hasattr(self, 'expert_btn'):
            self.expert_btn = ctk.CTkButton(
                self,
                text="⚙️ Редактор правил",
                command=self.edit_rules,
                fg_color="gray"
            )
            self.settings_btn = ctk.CTkButton(
                self,
                text="📄 Настройки безопасности",
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

    def edit_rules(self):
        """Открывает редактор правил с галочками"""
        try:
            rules_window = ctk.CTkToplevel(self)
            rules_window.title("Редактор правил")
            rules_window.geometry("600x550")
            rules_window.resizable(False, False)

            # Заголовок
            title = ctk.CTkLabel(
                rules_window, 
                text="📋 Правила сортировки", 
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=10)

            # Загрузка правил
            base_dir = Path(__file__).parent.parent
            rules_path = base_dir / 'config' / 'rules.json'
            
            self.log(f"🔍 Путь к правилам: {rules_path}")
            self.log(f"🔍 Файл существует: {rules_path.exists()}")
            
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)

            self.log(f"📄 Загружено правил: {len(rules_data.get('rules', []))}")

            # Фрейм для правил
            rules_frame = ctk.CTkFrame(rules_window)
            rules_frame.pack(pady=10, padx=20, fill="both", expand=True)

            self.rule_checkboxes = {}

            for i, rule in enumerate(rules_data['rules']):
                frame = ctk.CTkFrame(rules_frame)
                frame.pack(pady=3, padx=10, fill="x")

                # Галочка включения
                cb = ctk.CTkCheckBox(
                    frame, 
                    text=f"{rule['name']}",
                    width=200
                )
                if rule.get('enabled', True):
                    cb.select()
                else:
                    cb.deselect()
                cb.pack(side="left", padx=5, pady=5)

                self.rule_checkboxes[rule['id']] = cb

                # Расширения
                ext_text = ', '.join(rule['extensions'][:4])
                if len(rule['extensions']) > 4:
                    ext_text += '...'
                ext_label = ctk.CTkLabel(
                    frame, 
                    text=f"({ext_text})", 
                    width=250,
                    font=ctk.CTkFont(size=11)
                )
                ext_label.pack(side="left", padx=5, pady=5)

                # Папка назначения
                dest_label = ctk.CTkLabel(
                    frame, 
                    text=f"→ {rule['destination']}", 
                    width=150,
                    font=ctk.CTkFont(size=11)
                )
                dest_label.pack(side="right", padx=5, pady=5)

            # Кнопка сохранения
            def save_rules():
                try:
                    for rule in rules_data['rules']:
                        rule_id = rule['id']
                        if rule_id in self.rule_checkboxes:
                            rule['enabled'] = self.rule_checkboxes[rule_id].get()
                    
                    with open(rules_path, 'w', encoding='utf-8') as f:
                        json.dump(rules_data, f, indent=2, ensure_ascii=False)
                    
                    self.log("✅ Правила сохранены!")
                    rules_window.destroy()
                except Exception as e:
                    self.log(f"❌ Ошибка сохранения: {e}")

            save_btn = ctk.CTkButton(
                rules_window, 
                text="💾 Сохранить изменения", 
                command=save_rules,
                height=40,
                width=400
            )
            save_btn.pack(pady=15, padx=20)

            # Кнопка отмены
            cancel_btn = ctk.CTkButton(
                rules_window, 
                text="❌ Отмена", 
                command=rules_window.destroy,
                height=35,
                width=400,
                fg_color="gray"
            )
            cancel_btn.pack(pady=5, padx=20)

            self.log("📋 Редактор правил открыт")
            
        except Exception as e:
            self.log(f"❌ Ошибка открытия редактора: {e}")
            logger.error(f"Ошибка в edit_rules: {e}")
            import traceback
            traceback.print_exc()

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

    def update_progress(self, current, total):
        """Обновляет прогресс-бар"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{current}/{total} файлов")

    def start_sorting(self):
        """Запускает процесс сортировки"""
        if not self.selected_path:
            self.log("❌ Ошибка: Выберите папку!")
            return

        # Показываем прогресс-бар
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_label.pack(pady=5)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подготовка...")

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
        finally:
            # Скрываем прогресс-бар после завершения
            self.progress_bar.pack_forget()
            self.progress_label.pack_forget()

    def log(self, message):
        """Добавляет сообщение в лог-окно"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

def run_app():
    """Запуск приложения"""
    app = FileFlowApp()
    app.mainloop()