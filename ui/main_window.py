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

        # 🎨 Автоматическая тема (мимикрия под Windows)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        self.title("FileFlow v0.3")
        self.geometry("800x700")
        self.resizable(True, True)
        self.minsize(700, 600)

        self.selected_path = ""
        self.is_expert_mode = False
        self.dry_run = True
        self.recursive_mode = True
        self.rule_states = {}
        self.statistics = {}
        self.system_theme = ctk.get_appearance_mode()

        self.create_widgets()

    def create_widgets(self):
        """Создает все элементы интерфейса"""
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self, 
            text="🗂️ FileFlow v0.3", 
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

        # Сортировка в подпапках
        self.subfolders_switch = ctk.CTkSwitch(
            self,
            text="📂 Сортировать в подпапках (рекурсивно)",
            command=self.toggle_subfolders,
            onvalue=True,
            offvalue=False
        )
        self.subfolders_switch.select()
        self.subfolders_switch.pack(pady=10)

        # Панель статистики (скрыта по умолчанию)
        self.stats_frame = ctk.CTkFrame(self)
        
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="📊 Статистика файлов:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.stats_label.pack(pady=5, padx=10, anchor="w")
        
        self.stats_text = ctk.CTkTextbox(
            self.stats_frame, 
            width=600, 
            height=100,
            font=ctk.CTkFont(size=11)
        )
        self.stats_text.pack(pady=5, padx=10, fill="both", expand=True)
        self.stats_text.insert("0.0", "Выберите папку и нажмите «Анализ»\n")
        self.stats_text.configure(state="disabled")

        # Кнопка анализа (создаётся ОДИН раз здесь)
        self.analyze_btn = ctk.CTkButton(
            self.stats_frame,
            text="🔍 Анализировать папку",
            command=self.analyze_folder,
            height=35
        )
        self.analyze_btn.pack(pady=10, padx=10, fill="x")

        # Прогресс-бар (скрыт по умолчанию)
        self.progress_bar = ctk.CTkProgressBar(self, width=600)
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

        # Лог (текстовое поле, растягивается)
        self.log_text = ctk.CTkTextbox(self, width=600, height=150)
        self.log_text.pack(pady=10, padx=20, fill="both", expand=True)
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

    def toggle_subfolders(self):
        """Переключает режим сортировки подпапок"""
        self.recursive_mode = self.subfolders_switch.get()
        if self.recursive_mode:
            self.log("📂 Режим: Сортировка с подпапками")
        else:
            self.log("📁 Режим: Только текущая папка")

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
        
        # Показываем статистику в экспертном режиме
        self.stats_frame.pack(pady=10, padx=20, fill="x")

    def hide_expert_widgets(self):
        """Скрывает виджеты экспертного режима"""
        if hasattr(self, 'expert_btn'):
            self.expert_btn.pack_forget()
            self.settings_btn.pack_forget()
        
        self.stats_frame.pack_forget()

    def analyze_folder(self):
        """Анализирует папку и показывает статистику"""
        if not self.selected_path:
            self.log("❌ Ошибка: Выберите папку!")
            return

        self.log("🔍 Анализ папки...")
        self.stats_text.configure(state="normal")
        self.stats_text.delete("0.0", "end")
        self.stats_text.insert("0.0", "Анализ...\n")
        self.stats_text.configure(state="disabled")

        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            
            with open(config_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)

            stats = {rule['id']: {'count': 0, 'size': 0, 'name': rule['name']} 
                     for rule in rules_data['rules']}
            stats['other'] = {'count': 0, 'size': 0, 'name': 'Другое'}

            total_files = 0
            for root, dirs, files in os.walk(self.selected_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        size = os.path.getsize(filepath)
                        ext = os.path.splitext(file)[1].lower()
                        
                        found = False
                        for rule in rules_data['rules']:
                            if ext in rule['extensions']:
                                stats[rule['id']]['count'] += 1
                                stats[rule['id']]['size'] += size
                                found = True
                                break
                        
                        if not found:
                            stats['other']['count'] += 1
                            stats['other']['size'] += size
                        
                        total_files += 1
                    except:
                        pass

            def format_size(size_bytes):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} PB"

            output = f"Всего файлов: {total_files}\n\n"
            for rule_id, data in stats.items():
                if data['count'] > 0:
                    output += f"{data['name']}: {data['count']} файлов ({format_size(data['size'])})\n"

            self.stats_text.configure(state="normal")
            self.stats_text.delete("0.0", "end")
            self.stats_text.insert("0.0", output)
            self.stats_text.configure(state="disabled")
            
            self.log(f"✅ Анализ завершён: {total_files} файлов")

        except Exception as e:
            self.log(f"❌ Ошибка анализа: {e}")
            logger.error(f"Ошибка анализа: {e}")

    def edit_rules(self):
        """Открывает редактор правил с галочками"""
        try:
            rules_window = ctk.CTkToplevel(self)
            rules_window.title("Редактор правил")
            rules_window.geometry("750x650")
            rules_window.resizable(False, False)

            title = ctk.CTkLabel(
                rules_window, 
                text="📋 Правила сортировки", 
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=10)

            if self.is_expert_mode:
                hint = ctk.CTkLabel(
                    rules_window,
                    text="💡 Экспертный режим: можно менять папку назначения или отключить сортировку",
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                )
                hint.pack(pady=5)

            base_dir = Path(__file__).parent.parent
            rules_path = base_dir / 'config' / 'rules.json'
            
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)

            scroll_frame = ctk.CTkScrollableFrame(rules_window, width=700, height=450)
            scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

            self.rule_checkboxes = {}
            self.rule_destinations = {}
            self.rule_no_sort = {}

            for i, rule in enumerate(rules_data['rules']):
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(pady=5, padx=10, fill="x")

                top_frame = ctk.CTkFrame(frame, fg_color="transparent")
                top_frame.pack(side="top", fill="x", padx=5, pady=5)

                cb = ctk.CTkCheckBox(
                    top_frame, 
                    text=f"{rule['name']}",
                    width=150
                )
                if rule.get('enabled', True):
                    cb.select()
                else:
                    cb.deselect()
                cb.pack(side="left", padx=5)

                self.rule_checkboxes[rule['id']] = cb

                ext_text = ', '.join(rule['extensions'][:4])
                if len(rule['extensions']) > 4:
                    ext_text += '...'
                ext_label = ctk.CTkLabel(
                    top_frame, 
                    text=f"({ext_text})", 
                    width=200,
                    font=ctk.CTkFont(size=11),
                    text_color="gray"
                )
                ext_label.pack(side="left", padx=10)

                bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
                bottom_frame.pack(side="bottom", fill="x", padx=5, pady=5)

                if self.is_expert_mode:
                    no_sort_cb = ctk.CTkCheckBox(
                        bottom_frame,
                        text="⛔ Не сортировать",
                        width=130,
                        font=ctk.CTkFont(size=11)
                    )
                    if not rule.get('destination', ''):
                        no_sort_cb.select()
                    no_sort_cb.pack(side="left", padx=5)
                    self.rule_no_sort[rule['id']] = no_sort_cb

                dest_entry = ctk.CTkEntry(
                    bottom_frame,
                    width=250,
                    height=28,
                    font=ctk.CTkFont(size=11)
                )
                dest_entry.insert(0, rule.get('destination', ''))
                
                if self.is_expert_mode and 'no_sort_cb' in locals() and no_sort_cb.get():
                    dest_entry.configure(state="disabled", fg_color="gray")
                
                dest_entry.pack(side="left", padx=5)
                self.rule_destinations[rule['id']] = dest_entry

                if self.is_expert_mode:
                    def make_change_btn(entry):
                        def change_folder():
                            folder = ctk.filedialog.askdirectory()
                            if folder:
                                entry.delete(0, 'end')
                                entry.insert(0, folder)
                        return change_folder
                    
                    browse_btn = ctk.CTkButton(
                        bottom_frame,
                        text="Обзор...",
                        width=80,
                        height=28,
                        command=make_change_btn(dest_entry)
                    )
                    browse_btn.pack(side="left", padx=5)

                if self.is_expert_mode and 'no_sort_cb' in locals():
                    def toggle_entry(cb, entry):
                        def _toggle():
                            if cb.get():
                                entry.configure(state="disabled", fg_color="gray")
                            else:
                                entry.configure(state="normal")
                        return _toggle
                    
                    no_sort_cb.configure(command=toggle_entry(no_sort_cb, dest_entry))

            btn_frame = ctk.CTkFrame(rules_window, fg_color="transparent")
            btn_frame.pack(pady=15, padx=20, fill="x")

            def save_rules():
                try:
                    for rule in rules_data['rules']:
                        rule_id = rule['id']
                        
                        if rule_id in self.rule_checkboxes:
                            rule['enabled'] = self.rule_checkboxes[rule_id].get()
                        
                        if rule_id in self.rule_destinations:
                            dest = self.rule_destinations[rule_id].get().strip()
                            
                            if rule_id in self.rule_no_sort and self.rule_no_sort[rule_id].get():
                                rule['destination'] = ""
                                rule['enabled'] = False
                            else:
                                rule['destination'] = dest
                    
                    with open(rules_path, 'w', encoding='utf-8') as f:
                        json.dump(rules_data, f, indent=2, ensure_ascii=False)
                    
                    self.log("✅ Правила сохранены!")
                    rules_window.destroy()
                except Exception as e:
                    self.log(f"❌ Ошибка сохранения: {e}")

            save_btn = ctk.CTkButton(
                btn_frame, 
                text="💾 Сохранить изменения", 
                command=save_rules,
                height=40,
                width=250
            )
            save_btn.pack(side="left", padx=20)

            cancel_btn = ctk.CTkButton(
                btn_frame, 
                text="❌ Отмена", 
                command=rules_window.destroy,
                height=40,
                width=150,
                fg_color="gray"
            )
            cancel_btn.pack(side="right", padx=20)

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

        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_label.pack(pady=5)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подготовка...")

        self.log(f"\n=== Запуск сортировки ===")
        self.log(f"Путь: {self.selected_path}")
        self.log(f"Режим: {'Dry Run (Тест)' if self.dry_run else 'LIVE (Работа)'}")
        self.log(f"Подпапки: {'✅ Да' if self.recursive_mode else '❌ Нет'}")
        self.log("-" * 30)

        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            settings_path = base_dir / 'config' / 'settings.json'

            engine = FileFlowEngine(config_path, settings_path)
            result = engine.run(self.selected_path, dry_run=self.dry_run, gui=self, recursive=self.recursive_mode)

            self.log("-" * 30)
            if result:
                self.log("✅ Сортировка завершена успешно!")
            else:
                self.log("❌ Сортировка прервана (ошибка безопасности)")
        except Exception as e:
            self.log(f"❌ Критическая ошибка: {str(e)}")
            logger.error(f"Ошибка в GUI: {e}")
        finally:
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