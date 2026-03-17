import customtkinter as ctk
import os
import sys
from pathlib import Path
from core.engine import FileFlowEngine
from core.logger import setup_logger
import json
import tkinter.messagebox as messagebox
from PIL import Image

logger = setup_logger()

# ═══════════════════════════════════════════════════════════════
# 🎨 ЦВЕТОВАЯ КОНФИГУРАЦИЯ ИНТЕРФЕЙСА
# ═══════════════════════════════════════════════════════════════
# Экспериментируй с цветами! Меняй HEX коды на свои.
# Пример: '#FF8C00' → '#00FF00' (зелёный)
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # Основные цвета
    'title_text': '#FF8C00',           # Оранжевый — заголовок
    'stats_title': '#9370DB',          # Фиолетовый — статистика
    
    # Кнопки
    'analyze_btn': '#2E8B57',          # Зелёный — Анализ
    'analyze_btn_hover': '#3CB371',    # Светло-зелёный
    
    'sort_btn': '#FF8C00',             # Оранжевый — Сортировка
    'sort_btn_hover': '#FFA500',       # Светло-оранжевый
    
    'logs_btn': '#8A2BE2',             # Фиолетовый — Логи
    'logs_btn_hover': '#9370DB',       # Светло-фиолетовый
    
    'expert_btn': '#8A2BE2',           # Фиолетовый — Редактор правил
    'expert_btn_hover': '#9370DB',
    
    'settings_btn': '#FF8C00',         # Оранжевый — Настройки
    'settings_btn_hover': '#FFA500',
    
    'undo_btn': '#FF6347',             # Красный — Отмена
    'undo_btn_hover': '#FF4500',
    
    # Заголовки окон
    'logs_title': '#8A2BE2',           # Фиолетовый
    'rules_title': '#8A2BE2',          # Фиолетовый
    
    # Цвета для статистики (диаграммы)
    'chart_colors': [
        '#00CED1',  # Бирюзовый
        '#FF8C00',  # Оранжевый
        '#8A2BE2',  # Фиолетовый
        '#FF6347',  # Красный
        '#32CD32',  # Зелёный
        '#FFD700',  # Жёлтый
        '#4169E1',  # Синий
        '#FF1493',  # Розовый
    ]
}


class FileFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 🎨 Автоматическая тема
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        self.title("FileFlow v0.5")  # ✅ Обнови версию
        
        # ✅ Путь к логотипу (работает и в .exe, и в Python)
        if getattr(sys, 'frozen', False):
            # Запущен из .exe
            self.logo_path = os.path.join(sys._MEIPASS, 'logo.png')
        else:
            # Запущен из Python
            self.logo_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'logo.png'
            )
        
        self.geometry("800x750")
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
        
        # ✅ ЛОГОТИП (справа)
        try:
            if os.path.exists(self.logo_path):
                self.logo_image = ctk.CTkImage(
                    light_image=Image.open(self.logo_path),
                    dark_image=Image.open(self.logo_path),
                    size=(250, 53)  # ✅ Твой размер логотипа
                )
                self.logo_label = ctk.CTkLabel(
                    self,
                    image=self.logo_image,
                    text=""
                )
                # ✅ Размещаем СПРАВА
                self.logo_label.pack(pady=15, padx=20, anchor="e")
            else:
                # Если логотип не найден — показываем текст
                self.title_label = ctk.CTkLabel(
                    self, 
                    text="FileFlow v0.3", 
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=COLORS['title_text']
                )
                self.title_label.pack(pady=15)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки логотипа: {e}")
            # Fallback на текст
            self.title_label = ctk.CTkLabel(
                self, 
                text="FileFlow v0.3", 
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=COLORS['title_text']
            )
            self.title_label.pack(pady=15)

        # Выбор папки
        self.path_frame = ctk.CTkFrame(self, corner_radius=8)
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
            width=120,
            corner_radius=8
        )
        self.browse_btn.pack(side="right", padx=10, pady=10)

        # Режим работы
        self.mode_frame = ctk.CTkFrame(self, corner_radius=8)
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
            text="Сортировать в подпапках (рекурсивно)",
            command=self.toggle_subfolders,
            onvalue=True,
            offvalue=False
        )
        self.subfolders_switch.select()
        self.subfolders_switch.pack(pady=10)

        # ✅ КОНТЕЙНЕР ДЛЯ КНОПОК (4 кнопки теперь)
        self.buttons_container = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_container.pack(pady=20, padx=20, fill="x")

        # ✅ Кнопка анализа (25% ширины)
        self.analyze_btn = ctk.CTkButton(
            self.buttons_container,
            text="Анализ",
            command=self.analyze_folder,
            height=40,
            corner_radius=8,
            fg_color=COLORS['analyze_btn'],
            hover_color=COLORS['analyze_btn_hover']
        )
        self.analyze_btn.pack(side="left", padx=(0, 3), fill="x", expand=True)

        # ✅ Кнопка поиска дубликатов (25% ширины) — НОВАЯ!
        self.duplicates_btn = ctk.CTkButton(
            self.buttons_container,
            text="Дубликаты",
            command=self.find_duplicates,
            height=40,
            corner_radius=8,
            fg_color="#DC143C",  # Красный
            hover_color="#FF1493"
        )
        self.duplicates_btn.pack(side="left", padx=(3, 3), fill="x", expand=True)

        # ✅ Кнопка запуска сортировки (25% ширины)
        self.start_btn = ctk.CTkButton(
            self.buttons_container,
            text="Сортировка",
            command=self.start_sorting,
            height=40,
            corner_radius=8,
            fg_color=COLORS['sort_btn'],
            hover_color=COLORS['sort_btn_hover']
        )
        self.start_btn.pack(side="left", padx=(3, 3), fill="x", expand=True)

        # ✅ Кнопка логи (25% ширины)
        self.logs_btn = ctk.CTkButton(
            self.buttons_container,
            text="Логи",
            command=self.show_logs_window,
            height=40,
            corner_radius=8,
            fg_color=COLORS['logs_btn'],
            hover_color=COLORS['logs_btn_hover'],
            width=80
        )
        self.logs_btn.pack(side="left", padx=(3, 0), fill="x", expand=True)

        # Прогресс-бар (скрыт по умолчанию)
        self.progress_bar = ctk.CTkProgressBar(self, width=600, corner_radius=4)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self, text="")

        # ✅ Кнопка отмены (скрыта по умолчанию)
        self.undo_btn = ctk.CTkButton(
            self, 
            text="Отменить последнюю сортировку", 
            command=self.undo_sorting,
            height=40,
            fg_color=COLORS['undo_btn'],
            hover_color=COLORS['undo_btn_hover'],
            corner_radius=8
        )
        # Не pack() — пока скрыта

        # ✅ ПАНЕЛЬ СТАТИСТИКИ (скрыта по умолчанию)
        self.stats_frame = ctk.CTkFrame(self, corner_radius=8)
        
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="Статистика",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['stats_title']
        )
        self.stats_label.pack(pady=5, padx=10, anchor="w")
        
        # ✅ Прокручиваемый контейнер для статистики (МАСШТАБИРУЕТСЯ!)
        self.stats_scroll = ctk.CTkScrollableFrame(
            self.stats_frame, 
            corner_radius=8  # ✅ Убрали фиксированную height
        )
        # ✅ Заполняет всё доступное пространство
        self.stats_scroll.pack(pady=5, padx=10, fill="both", expand=True)
        
        # ✅ Начальный текст
        self.stats_text_label = ctk.CTkLabel(
            self.stats_scroll,
            text="Выберите папку и нажмите «Анализ»",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.stats_text_label.pack(pady=5, padx=5, anchor="w")

        # ✅ Лог (текстовое поле) — НЕ ПОКАЗЫВАЕМ В ОСНОВНОМ ОКНЕ
        self.log_text = ctk.CTkTextbox(self, width=600, height=200, corner_radius=8)
        # Не pack() — скрыт!
        self.log_text.insert("0.0", "Готов к работе...\n")

    def browse_folder(self):
        """Открывает диалог выбора папки"""
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.selected_path = folder
            self.path_label.configure(text=folder)
            self.log(f"Выбрана папка: {folder}")

    def toggle_mode(self):
        """Переключает режим Dry Run / Live"""
        self.dry_run = self.mode_switch.get()
        if self.dry_run:
            self.log("Режим: Dry Run (тестовый)")
        else:
            self.log("Режим: Live (файлы будут перемещены!)")

    def toggle_subfolders(self):
        """Переключает режим сортировки подпапок"""
        self.recursive_mode = self.subfolders_switch.get()
        if self.recursive_mode:
            self.log("Режим: Сортировка с подпапками")
        else:
            self.log("Режим: Только текущая папка")

    def toggle_expert(self):
        """Включает экспертный режим"""
        self.is_expert_mode = self.expert_switch.get()
        if self.is_expert_mode:
            self.log("Экспертный режим включен")
            self.show_expert_widgets()
        else:
            self.log("Простой режим включен")
            self.hide_expert_widgets()

    def show_expert_widgets(self):
        """Показывает виджеты экспертного режима"""
        if not hasattr(self, 'expert_btn'):
            self.expert_btn = ctk.CTkButton(
                self,
                text="Редактор правил",
                command=self.edit_rules,
                fg_color=COLORS['expert_btn'],
                hover_color=COLORS['expert_btn_hover'],
                corner_radius=8
            )
            self.settings_btn = ctk.CTkButton(
                self,
                text="Настройки безопасности",
                command=self.view_settings,
                fg_color=COLORS['settings_btn'],
                hover_color=COLORS['settings_btn_hover'],
                corner_radius=8
            )
        
        self.expert_btn.pack(pady=5, padx=20, fill="x", before=self.buttons_container)
        self.settings_btn.pack(pady=5, padx=20, fill="x", before=self.buttons_container)
        
        # ✅ Показываем панель статистики
        self.stats_frame.pack(pady=10, padx=20, fill="both", expand=True, after=self.buttons_container)

    def hide_expert_widgets(self):
        """Скрывает виджеты экспертного режима"""
        if hasattr(self, 'expert_btn'):
            self.expert_btn.pack_forget()
            self.settings_btn.pack_forget()
        
        # Скрываем панель статистики
        self.stats_frame.pack_forget()

    def show_logs_window(self):
        """Открывает логи в отдельном окне"""
        # Создаем новое окно
        logs_window = ctk.CTkToplevel(self)
        logs_window.title("Логи FileFlow")
        logs_window.geometry("700x500")
        logs_window.resizable(True, True)

        # Заголовок
        title = ctk.CTkLabel(
            logs_window,
            text="Журнал событий",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['logs_title']
        )
        title.pack(pady=10, padx=10, anchor="w")

        # Текстовое поле с логами
        logs_text = ctk.CTkTextbox(logs_window, corner_radius=8)
        logs_text.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Копируем текущие логи
        logs_text.insert("0.0", self.log_text.get("0.0", "end"))
        logs_text.configure(state="disabled")
        
        # Кнопка обновления
        def refresh_logs():
            logs_text.configure(state="normal")
            logs_text.delete("0.0", "end")
            logs_text.insert("0.0", self.log_text.get("0.0", "end"))
            logs_text.configure(state="disabled")
            logs_text.see("end")

        # Кнопки
        btn_frame = ctk.CTkFrame(logs_window, fg_color="transparent")
        btn_frame.pack(pady=10, padx=10, fill="x")

        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="Обновить",
            command=refresh_logs,
            width=120,
            corner_radius=8
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Закрыть",
            command=logs_window.destroy,
            width=120,
            fg_color="gray",
            corner_radius=8
        )
        close_btn.pack(side="right")

        # Автопрокрутка вниз
        logs_text.see("end")

    def analyze_folder(self):
        """Анализирует папку и показывает статистику"""
        if not self.selected_path:
            self.log("Ошибка: Выберите папку!")
            return

        self.log("Анализ папки...")
        
        # Очищаем старую статистику
        for widget in self.stats_scroll.winfo_children():
            widget.destroy()

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

            # ✅ Сохраняем статистику
            self.statistics = stats

            # ✅ Заголовок "Всего файлов"
            total_label = ctk.CTkLabel(
                self.stats_scroll,
                text=f"Всего файлов: {total_files}",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            total_label.pack(pady=5, padx=5, anchor="w")
            
            # ✅ Разделитель
            separator = ctk.CTkFrame(self.stats_scroll, height=2, fg_color="#444444")
            separator.pack(pady=5, padx=5, fill="x")

            # ✅ Сортируем по количеству (убывание)
            sorted_stats = sorted(
                [(k, v) for k, v in stats.items() if v['count'] > 0],
                key=lambda x: x[1]['count'],
                reverse=True
            )

            # ✅ Показываем статистику ВЕРТИКАЛЬНО с визуализацией
            for i, (rule_id, data) in enumerate(sorted_stats):
                size_str = format_size(data['size'])
                percentage = (data['count'] / total_files * 100) if total_files > 0 else 0
                
                # Контейнер для одной категории
                category_frame = ctk.CTkFrame(self.stats_scroll, fg_color="transparent")
                category_frame.pack(pady=5, padx=5, fill="x")
                
                # Заголовок категории
                header_frame = ctk.CTkFrame(category_frame, fg_color="transparent")
                header_frame.pack(fill="x")
                
                # Цветной индикатор слева
                indicator = ctk.CTkFrame(
                    header_frame,
                    width=12,
                    height=20,
                    fg_color=COLORS['chart_colors'][i % len(COLORS['chart_colors'])],
                    corner_radius=3
                )
                indicator.pack(side="left", padx=(0, 10))
                
                # Название категории
                name_label = ctk.CTkLabel(
                    header_frame,
                    text=data['name'],
                    font=ctk.CTkFont(size=11, weight="bold"),
                    anchor="w"
                )
                name_label.pack(side="left", padx=(0, 10))
                
                # Количество и процент
                count_label = ctk.CTkLabel(
                    header_frame,
                    text=f"{data['count']} файлов ({percentage:.1f}%)",
                    font=ctk.CTkFont(size=10),
                    text_color="#AAAAAA",
                    anchor="w"
                )
                count_label.pack(side="left")
                
                # Размер файла (справа)
                size_label = ctk.CTkLabel(
                    header_frame,
                    text=size_str,
                    font=ctk.CTkFont(size=10),
                    text_color="#888888",
                    anchor="e"
                )
                size_label.pack(side="right", padx=(10, 0))
                
                # ✅ ВИЗУАЛЬНЫЙ БАР (диаграмма)
                bar_container = ctk.CTkFrame(
                    category_frame,
                    height=8,
                    fg_color="#2b2b2b",
                    corner_radius=4
                )
                bar_container.pack(pady=(5, 0), fill="x")
                
                # Заполненная часть бара (пропорционально проценту)
                bar_width = int(380 * percentage / 100) if percentage > 0 else 1
                bar_fill = ctk.CTkFrame(
                    bar_container,
                    height=8,
                    width=bar_width,
                    fg_color=COLORS['chart_colors'][i % len(COLORS['chart_colors'])],
                    corner_radius=4
                )
                bar_fill.pack(side="left", padx=0, pady=0)

            self.log(f"Анализ завершён: {total_files} файлов")

        except Exception as e:
            self.log(f"Ошибка анализа: {e}")
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
                text="Правила сортировки", 
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLORS['rules_title']
            )
            title.pack(pady=10)

            if self.is_expert_mode:
                hint = ctk.CTkLabel(
                    rules_window,
                    text="Экспертный режим: можно менять папку назначения или отключить сортировку",
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
                frame = ctk.CTkFrame(scroll_frame, corner_radius=8)
                frame.pack(pady=5, padx=10, fill="x")

                top_frame = ctk.CTkFrame(frame, fg_color="transparent")
                top_frame.pack(side="top", fill="x", padx=5, pady=5)

                cb = ctk.CTkCheckBox(
                    top_frame, 
                    text=rule['name'],
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
                        text="Не сортировать",
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
                
                if self.is_expert_mode and rule['id'] in self.rule_no_sort and self.rule_no_sort[rule['id']].get():
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

                if self.is_expert_mode and rule['id'] in self.rule_no_sort:
                    def toggle_entry(cb, entry):
                        def _toggle():
                            if cb.get():
                                entry.configure(state="disabled", fg_color="gray")
                            else:
                                entry.configure(state="normal")
                        return _toggle
                    
                    self.rule_no_sort[rule['id']].configure(command=toggle_entry(self.rule_no_sort[rule['id']], dest_entry))

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
                    
                    self.log("Правила сохранены!")
                    rules_window.destroy()
                except Exception as e:
                    self.log(f"Ошибка сохранения: {e}")

            save_btn = ctk.CTkButton(
                btn_frame, 
                text="Сохранить изменения", 
                command=save_rules,
                height=40,
                width=250,
                corner_radius=8
            )
            save_btn.pack(side="left", padx=20)

            cancel_btn = ctk.CTkButton(
                btn_frame, 
                text="Отмена", 
                command=rules_window.destroy,
                height=40,
                width=150,
                fg_color="gray",
                corner_radius=8
            )
            cancel_btn.pack(side="right", padx=20)

            self.log("Редактор правил открыт")
            
        except Exception as e:
            self.log(f"Ошибка открытия редактора: {e}")
            logger.error(f"Ошибка в edit_rules: {e}")
            import traceback
            traceback.print_exc()

    def view_settings(self):
        """Открывает окно с настройками безопасности"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки безопасности")
        settings_window.geometry("500x400")
        
        text_box = ctk.CTkTextbox(settings_window, width=480, height=350, corner_radius=8)
        text_box.pack(pady=10, padx=10)
        
        base_dir = Path(__file__).parent.parent
        settings_path = base_dir / 'config' / 'settings.json'
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        text_box.insert("0.0", settings_content)
        text_box.configure(state="disabled")
        
        self.log("Настройки открыты для просмотра")

    def update_progress(self, current, total):
        """Обновляет прогресс-бар"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{current}/{total} файлов")

    def start_sorting(self):
        """Запускает процесс сортировки"""
        if not self.selected_path:
            self.log("Ошибка: Выберите папку!")
            return
        
        # Скрываем кнопку отмены перед новой сортировкой
        if hasattr(self, 'undo_btn'):
            self.undo_btn.pack_forget()

        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_label.pack(pady=5)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подготовка...")

        self.log(f"\n=== Запуск сортировки ===")
        self.log(f"Путь: {self.selected_path}")
        self.log(f"Режим: {'Dry Run (Тест)' if self.dry_run else 'LIVE (Работа)'}")
        self.log(f"Подпапки: {'Да' if self.recursive_mode else 'Нет'}")
        self.log("-" * 30)

        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            settings_path = base_dir / 'config' / 'settings.json'

            engine = FileFlowEngine(config_path, settings_path)
            result = engine.run(self.selected_path, dry_run=self.dry_run, gui=self, recursive=self.recursive_mode)

            self.log("-" * 30)
            if result:
                self.log("Сортировка завершена успешно!")
                # Показываем кнопку отмены
                self.undo_btn.pack(pady=10, padx=20, fill="x")
            else:
                self.log("Сортировка прервана (ошибка безопасности)")
        except Exception as e:
            self.log(f"Критическая ошибка: {str(e)}")
            logger.error(f"Ошибка в GUI: {e}")
        finally:
            self.progress_bar.pack_forget()
            self.progress_label.pack_forget()

    def undo_sorting(self):
        """Отменяет последнюю сортировку"""
        if not self.selected_path:
            self.log("Ошибка: Выберите папку!")
            return
        
        # Подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите отменить последнюю сортировку?\n\n"
            "Все перемещённые файлы будут возвращены на исходные места."
        )
        
        if not confirm:
            return
        
        self.log("\n=== Отмена сортировки ===")
        
        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            settings_path = base_dir / 'config' / 'settings.json'
            
            engine = FileFlowEngine(config_path, settings_path)
            success, message = engine.undo_last_sort(self.selected_path)
            
            if success:
                self.log(f"{message}")
                self.log("Отмена завершена успешно!")
                # Скрываем кнопку после успешной отмены
                self.undo_btn.pack_forget()
            else:
                self.log(f"{message}")
                
        except Exception as e:
            self.log(f"Критическая ошибка: {str(e)}")
            logger.error(f"Ошибка отмены: {e}")

    def log(self, message):
        """Добавляет сообщение в лог-окно"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

        
    def find_duplicates(self):
        """Ищет и показывает дубликаты файлов"""
        if not self.selected_path:
            self.log("Ошибка: Выберите папку!")
            return

        self.log("Поиск дубликатов...")
        
        # Проверяем количество файлов
        file_count = 0
        try:
            for root, dirs, files in os.walk(self.selected_path):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__']]
                file_count += len(files)
        except:
            pass
        
        if file_count > 10000:
            confirm = messagebox.askyesno(
                "Много файлов",
                f"Найдено {file_count} файлов.\n\nПоиск может занять несколько минут.\nПродолжить?"
            )
            if not confirm:
                return
        
        self.log(f"Поиск дубликатов среди {file_count} файлов...")
        
        # ✅ Запускаем поиск БЕЗ окна прогресса (просто в потоке)
        import threading
        
        result = {'duplicates': None, 'error': None}
        
        def search_thread():
            try:
                from core.duplicates import DuplicateFinder
                finder = DuplicateFinder()
                duplicates = finder.find_duplicates(
                    self.selected_path, 
                    recursive=True,
                    min_size=10240  # 10KB минимум
                )
                result['duplicates'] = (finder, duplicates)
            except Exception as e:
                result['error'] = str(e)
                import traceback
                traceback.print_exc()
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
        
        # Показываем простое сообщение пока ждём
        self.log("Сканирование... Пожалуйста, подождите.")
        
        # Ждём завершения
        thread.join()
        
        # Проверяем результат
        if result['error']:
            self.log(f"Ошибка поиска: {result['error']}")
            messagebox.showerror("Ошибка", f"Не удалось найти дубликаты:\n{result['error']}")
            return
        
        if result['duplicates']:
            finder, duplicates = result['duplicates']
            if duplicates:
                dup_count = finder.get_duplicates_count()
                wasted = finder.get_wasted_space()
                self.log(f"Найдено дубликатов: {dup_count} файлов ({self.format_size(wasted)})")
                # ✅ Вызываем метод правильно
                self.show_duplicates_window(finder, duplicates)
            else:
                self.log("Дубликаты не найдены")
                messagebox.showinfo("Результат", "Дубликаты не найдены!")

    def show_duplicates_window(self, finder, duplicates):
        """Показывает окно с найденными дубликатами"""
        # ✅ Создаём окно
        dup_window = ctk.CTkToplevel(self)
        dup_window.title("Дубликаты файлов")
        dup_window.geometry("900x600")
        
        # Заголовок
        title = ctk.CTkLabel(
            dup_window,
            text="Найденные дубликаты",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#DC143C"
        )
        title.pack(pady=10)
        
        # Статистика
        wasted_space = finder.get_wasted_space()
        dup_count = finder.get_duplicates_count()
        
        stats_frame = ctk.CTkFrame(dup_window, corner_radius=8)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            stats_frame,
            text=f"Найдено дубликатов: {dup_count}",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=5)
        
        ctk.CTkLabel(
            stats_frame,
            text=f"Можно освободить: {self.format_size(wasted_space)}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#32CD32"
        ).pack(pady=5)
        
        # Прокручиваемый список дубликатов
        scroll_frame = ctk.CTkScrollableFrame(dup_window, corner_radius=8)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Чекбоксы для выбора
        checkboxes = {}
        
        # Группируем дубликаты
        group_num = 0
        for file_hash, files in duplicates.items():
            group_num += 1
            
            # Заголовок группы
            group_frame = ctk.CTkFrame(scroll_frame, fg_color="#2b2b2b", corner_radius=8)
            group_frame.pack(pady=5, padx=5, fill="x")
            
            ctk.CTkLabel(
                group_frame,
                text=f"Группа {group_num} ({len(files)} файлов)",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#FF8C00"
            ).pack(pady=5, padx=10, anchor="w")
            
            # Список файлов в группе
            for i, filepath in enumerate(files):
                file_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
                file_frame.pack(pady=2, padx=10, fill="x")
                
                # Чекбокс (не отмечать первый файл - он будет сохранён)
                cb = ctk.CTkCheckBox(
                    file_frame,
                    text="",
                    width=20,
                    onvalue=filepath,
                    offvalue=""
                )
                if i > 0:  # Не отмечать первый файл
                    cb.select()
                cb.pack(side="left", padx=5)
                checkboxes[filepath] = cb
                
                # Путь к файлу
                path_label = ctk.CTkLabel(
                    file_frame,
                    text=filepath,
                    font=ctk.CTkFont(size=10),
                    anchor="w"
                )
                path_label.pack(side="left", padx=5, fill="x", expand=True)
                
                # Размер файла
                try:
                    size = os.path.getsize(filepath)
                    size_label = ctk.CTkLabel(
                        file_frame,
                        text=self.format_size(size),
                        font=ctk.CTkFont(size=9),
                        text_color="#888888"
                    )
                    size_label.pack(side="right", padx=5)
                except:
                    pass
                
                # Кнопка "Открыть папку"
                def make_open_btn(path):
                    def open_folder():
                        os.startfile(os.path.dirname(path))
                    return open_folder
                
                open_btn = ctk.CTkButton(
                    file_frame,
                    text="",
                    width=30,
                    height=25,
                    corner_radius=4,
                    command=make_open_btn(filepath)
                )
                open_btn.pack(side="right", padx=2)
        
        # Кнопки действий
        btn_frame = ctk.CTkFrame(dup_window, fg_color="transparent")
        btn_frame.pack(pady=15, padx=20, fill="x")
        
        def delete_selected():
            to_delete = [cb.get() for cb in checkboxes.values() if cb.get()]
            if to_delete:
                confirm = messagebox.askyesno(
                    "Подтверждение",
                    f"Удалить {len(to_delete)} файлов?\n\nЭто действие нельзя отменить!"
                )
                if confirm:
                    deleted = 0
                    freed = 0
                    for filepath in to_delete:
                        try:
                            size = os.path.getsize(filepath)
                            os.remove(filepath)
                            deleted += 1
                            freed += size
                        except Exception as e:
                            self.log(f"Ошибка удаления {filepath}: {e}")
                    
                    self.log(f"Удалено {deleted} файлов, освобождено {self.format_size(freed)}")
                    dup_window.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Удалить выбранные",
            command=delete_selected,
            height=40,
            corner_radius=8,
            fg_color="#DC143C",
            hover_color="#FF1493",
            width=200
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Закрыть",
            command=dup_window.destroy,
            height=40,
            corner_radius=8,
            fg_color="gray",
            width=150
        ).pack(side="right", padx=10)
    
    def format_size(self, size_bytes: int) -> str:
        """Форматирует размер файла"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

def run_app():
    """Запуск приложения"""
    app = FileFlowApp()
    app.mainloop()