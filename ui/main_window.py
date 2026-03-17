import customtkinter as ctk
import os
import sys
import json
import webbrowser
import threading
from pathlib import Path
from datetime import datetime
import tkinter.messagebox as messagebox
from PIL import Image

# Импорты из ядра
from core.engine import FileFlowEngine
from core.logger import setup_logger
from core.duplicates import DuplicateFinder

logger = setup_logger()

# ═══════════════════════════════════════════════════════════════
# 🎨 ЦВЕТОВАЯ КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

COLORS = {
    'bg_primary': '#1a1a2e',
    'bg_secondary': '#16213e',
    'bg_card': '#0f3460',
    'accent': '#e94560',
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0a0',
    'sidebar_bg': '#0f3460',
    'sidebar_active': '#e94560',
    'sidebar_hover': '#1a1a2e',
    'icon_color': '#00CED1',
    'success': '#2E8B57',
    'warning': '#FFA500',
    'danger': '#DC143C',
    'info': '#4169E1',
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FileFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FileFlow v0.5")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        # Состояние приложения
        self.selected_path = ""
        self.dry_run = True
        self.recursive_mode = True
        self.current_page = "home"
        self.statistics = {}
        self.last_sort_data = None

        # Путь к логотипу
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')

        # Создаём интерфейс
        self.create_sidebar()
        self.create_main_area()
        
        # Показываем главную страницу
        self.show_page("home")

    def create_sidebar(self):
        """Создаёт боковое меню"""
        self.sidebar = ctk.CTkFrame(
            self, 
            width=250, 
            corner_radius=0,
            fg_color=COLORS['sidebar_bg']
        )
        self.sidebar.pack(side="left", fill="both", expand=False)
        self.sidebar.pack_propagate(False)

        # Логотип
        self.create_logo_section()

        # Разделитель
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS['accent']).pack(pady=10, padx=10, fill="x")

        # Меню
        self.create_menu()

        # Нижняя часть
        self.create_sidebar_footer()

    def create_logo_section(self):
        """Создаёт секцию с логотипом"""
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=170)
        logo_frame.pack(pady=10, padx=20, fill="x")
        logo_frame.pack_propagate(False)

        # Путь к логотипу
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')
        
        try:
            if os.path.exists(logo_path):
                # Загружаем логотип
                self.logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(230, 138)  # Чуть меньше 250x150 для отступов
                )
                
                ctk.CTkLabel(
                    logo_frame,
                    image=self.logo_image,
                    text=""
                ).pack(pady=10)
                
                print("✅ Логотип загружен успешно!")
            else:
                # Fallback на текст если логотип не найден
                ctk.CTkLabel(
                    logo_frame,
                    text="FILEFLOW",
                    font=ctk.CTkFont(size=22, weight="bold"),
                    text_color=COLORS['accent']
                ).pack(pady=10)
                
                print("⚠️ Логотип не найден, используем текст")
        except Exception as e:
            print(f"❌ Ошибка загрузки логотипа: {e}")
            # Fallback на текст
            ctk.CTkLabel(
                logo_frame,
                text="FILEFLOW",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=COLORS['accent']
            ).pack(pady=10)

        ctk.CTkLabel(
            logo_frame,
            text="v0.5",
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary']
        ).pack()

    def create_menu(self):
        """Создаёт текстовое меню навигации"""
        menu_items = [
            ("Главная", "home"),
            ("Настройки", "settings"),
            ("Правила", "rules"),
            ("Правка", "edit"),
            ("Справка", "help"),
        ]

        self.menu_buttons = {}

        for text, page_id in menu_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=ctk.CTkFont(size=14, weight="bold"),
                height=45,
                corner_radius=8,
                fg_color="transparent",
                hover_color=COLORS['sidebar_hover'],
                anchor="w",
                command=lambda p=page_id: self.show_page(p)
            )
            btn.pack(pady=5, padx=15, fill="x")
            self.menu_buttons[page_id] = btn

    def create_sidebar_footer(self):
        """Создаёт нижнюю часть сайдбара"""
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=20)

        ctk.CTkButton(
            footer_frame,
            text="GitHub ↗",
            font=ctk.CTkFont(size=11),
            height=35,
            corner_radius=6,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['accent'],
            command=lambda: webbrowser.open("https://github.com/Expense22/FileFlow")
        ).pack(pady=5, padx=15, fill="x")

        ctk.CTkLabel(
            footer_frame,
            text="FileFlow v0.5",
            font=ctk.CTkFont(size=9),
            text_color=COLORS['text_secondary']
        ).pack(pady=5)

    def create_main_area(self):
        """Создаёт основную область контента"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS['bg_primary'])
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.pages_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.create_home_page()
        self.create_settings_page()
        self.create_rules_page()
        self.create_edit_page()
        self.create_help_page()

    def show_page(self, page_id):
        """Показывает выбранную страницу"""
        # Скрываем все страницы
        for page in ["home", "settings", "rules", "edit", "help"]:
            if hasattr(self, f'page_{page}'):
                getattr(self, f'page_{page}').pack_forget()

        # Показываем нужную
        if hasattr(self, f'page_{page_id}'):
            getattr(self, f'page_{page_id}').pack(fill="both", expand=True)

        # Обновляем кнопки меню
        for pid, data in self.menu_buttons.items():
            # data - это кортеж (icon_label, text_label, btn)
            if isinstance(data, tuple) and len(data) >= 3:
                icon_label, text_label, btn = data
                if pid == page_id:
                    btn.configure(fg_color=COLORS['sidebar_active'])
                else:
                    btn.configure(fg_color="transparent")
            elif hasattr(data, 'configure'):
                # Если это просто кнопка (старый формат)
                if pid == page_id:
                    data.configure(fg_color=COLORS['sidebar_active'])
                else:
                    data.configure(fg_color="transparent")

        self.current_page = page_id
    def create_home_page(self):
        """Создаёт главную страницу"""
        self.page_home = ctk.CTkScrollableFrame(self.pages_container, fg_color=COLORS['bg_secondary'], corner_radius=12)
        
        header = ctk.CTkLabel(
            self.page_home,
            text="📁 Главная",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        )
        header.pack(pady=20, padx=20, fill="x")

        folder_card = ctk.CTkFrame(self.page_home, fg_color=COLORS['bg_card'], corner_radius=10)
        folder_card.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            folder_card,
            text="Выберите папку для работы",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_primary']
        ).pack(pady=10, padx=15, anchor="w")

        path_frame = ctk.CTkFrame(folder_card, fg_color="transparent")
        path_frame.pack(pady=10, padx=15, fill="x")

        self.path_entry = ctk.CTkEntry(
            path_frame,
            placeholder_text="Папка не выбрана",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            path_frame,
            text="Обзор...",
            command=self.browse_folder,
            width=100,
            height=40,
            corner_radius=8,
            fg_color=COLORS['accent']
        ).pack(side="right")

        actions_frame = ctk.CTkFrame(self.page_home, fg_color="transparent")
        actions_frame.pack(pady=20, padx=20, fill="x")

        self.create_action_card(
            actions_frame,
            "🔍 Анализ",
            "Анализировать папку",
            self.analyze_folder,
            COLORS['success'],
            side="left"
        )

        self.create_action_card(
            actions_frame,
            "🚀 Сортировка",
            "Запустить сортировку",
            self.start_sorting,
            COLORS['accent'],
            side="left"
        )

        self.create_action_card(
            actions_frame,
            "🔄 Дубликаты",
            "Найти дубликаты",
            self.find_duplicates,
            COLORS['danger'],
            side="left"
        )

        stats_card = ctk.CTkFrame(self.page_home, fg_color=COLORS['bg_card'], corner_radius=10)
        stats_card.pack(pady=10, padx=20, fill="both", expand=True)

        ctk.CTkLabel(
            stats_card,
            text="📊 Статистика",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=10, padx=15, anchor="w")

        self.stats_scroll = ctk.CTkScrollableFrame(stats_card, fg_color="transparent")
        self.stats_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(
            self.stats_scroll,
            text="Выберите папку и нажмите «Анализ»",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        ).pack(pady=20)

    def create_action_card(self, parent, title, btn_text, command, color, side="left"):
        """Создаёт карточку действия"""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=10, width=250, height=120)
        card.pack(side=side, padx=10, fill="x", expand=True)
        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=15)

        ctk.CTkButton(
            card,
            text=btn_text,
            command=command,
            height=35,
            corner_radius=8,
            fg_color=color
        ).pack(pady=10)

    def create_settings_page(self):
        """Создаёт страницу настроек"""
        self.page_settings = ctk.CTkScrollableFrame(self.pages_container, fg_color=COLORS['bg_secondary'], corner_radius=12)
        
        header = ctk.CTkLabel(
            self.page_settings,
            text="⚙️ Настройки",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        )
        header.pack(pady=20, padx=20, fill="x")

        settings_card = ctk.CTkFrame(self.page_settings, fg_color=COLORS['bg_card'], corner_radius=10)
        settings_card.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            settings_card,
            text="Основные настройки",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=15, padx=15, anchor="w")

        self.auto_close_var = ctk.BooleanVar(value=False)
        self.create_setting_toggle(
            settings_card,
            "Закрывать окна после завершения",
            "Автоматически закрывать окна после сортировки"
        )

        self.dry_run_var = ctk.BooleanVar(value=True)
        self.create_setting_toggle(
            settings_card,
            "Dry Run (тестовый режим)",
            "Не перемещать файлы, только показать"
        )

        self.recursive_var = ctk.BooleanVar(value=True)
        self.create_setting_toggle(
            settings_card,
            "Сортировать в подпапках",
            "Включать все вложенные папки"
        )

    def create_setting_toggle(self, parent, title, description):
        """Создаёт переключатель настройки"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=15, padx=15, fill="x")

        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_frame,
            text=description,
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary']
        ).pack(anchor="w")

        switch = ctk.CTkSwitch(
            frame,
            text="",
            onvalue=True,
            offvalue=False
        )
        switch.pack(side="right")
        return switch

    def create_rules_page(self):
        """Создаёт страницу правил сортировки"""
        self.page_rules = ctk.CTkFrame(self.pages_container, fg_color=COLORS['bg_secondary'], corner_radius=12)
        
        header_frame = ctk.CTkFrame(self.page_rules, fg_color="transparent")
        header_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(
            header_frame,
            text="📋 Правила сортировки",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="+ Добавить правило",
            command=self.add_rule,
            height=35,
            corner_radius=8,
            fg_color=COLORS['accent']
        ).pack(side="right")

        self.rules_scroll = ctk.CTkScrollableFrame(self.page_rules, fg_color=COLORS['bg_card'], corner_radius=10)
        self.rules_scroll.pack(pady=10, padx=20, fill="both", expand=True)

        self.load_rules()

    def load_rules(self):
        """Загружает правила из файла"""
        for widget in self.rules_scroll.winfo_children():
            widget.destroy()

        try:
            config_path = Path(__file__).parent.parent / 'config' / 'rules.json'
            with open(config_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)

            for i, rule in enumerate(rules_data.get('rules', [])):
                self.create_rule_item(rule, i)

        except Exception as e:
            ctk.CTkLabel(
                self.rules_scroll,
                text=f"Ошибка загрузки правил: {e}",
                text_color=COLORS['danger']
            ).pack(pady=20)

    def create_rule_item(self, rule, index):
        """Создаёт элемент правила"""
        rule_frame = ctk.CTkFrame(self.rules_scroll, fg_color=COLORS['bg_secondary'], corner_radius=8)
        rule_frame.pack(pady=5, padx=10, fill="x")

        left_frame = ctk.CTkFrame(rule_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            left_frame,
            text=rule['name'],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w")

        ext_text = ', '.join(rule.get('extensions', [])[:5])
        if len(rule.get('extensions', [])) > 5:
            ext_text += '...'
        
        ctk.CTkLabel(
            left_frame,
            text=f"Расширения: {ext_text}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary']
        ).pack(anchor="w")

        cb = ctk.CTkCheckBox(
            rule_frame,
            text="",
            onvalue=True,
            offvalue=False
        )
        if rule.get('enabled', True):
            cb.select()
        cb.pack(side="right", padx=10)

    def add_rule(self):
        """Диалог добавления правила"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить правило")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Название правила", font=ctk.CTkFont(size=12)).pack(pady=5, padx=20, anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=450, height=35)
        name_entry.pack(pady=5, padx=20)

        ctk.CTkLabel(dialog, text="Расширения (через запятую)", font=ctk.CTkFont(size=12)).pack(pady=5, padx=20, anchor="w")
        ext_entry = ctk.CTkEntry(dialog, width=450, height=35)
        ext_entry.pack(pady=5, padx=20)

        ctk.CTkLabel(dialog, text="Папка назначения", font=ctk.CTkFont(size=12)).pack(pady=5, padx=20, anchor="w")
        dest_entry = ctk.CTkEntry(dialog, width=450, height=35)
        dest_entry.pack(pady=5, padx=20)

        def save():
            try:
                name = name_entry.get().strip()
                extensions = [ext.strip() for ext in ext_entry.get().split(',') if ext.strip()]
                destination = dest_entry.get().strip()

                if not name or not extensions:
                    messagebox.showerror("Ошибка", "Название и расширения обязательны!")
                    return

                config_path = Path(__file__).parent.parent / 'config' / 'rules.json'
                with open(config_path, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)

                new_rule = {
                    "id": f"rule_{len(rules_data['rules']) + 1}",
                    "name": name,
                    "extensions": extensions,
                    "destination": destination if destination else name,
                    "enabled": True
                }

                rules_data['rules'].append(new_rule)

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)

                self.load_rules()
                dialog.destroy()
                messagebox.showinfo("Успех", "Правило добавлено!")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить правило: {e}")

        ctk.CTkButton(dialog, text="Сохранить", command=save, height=35, fg_color=COLORS['accent']).pack(pady=20)
        ctk.CTkButton(dialog, text="Отмена", command=dialog.destroy, height=35, fg_color="gray").pack(pady=5)

    def create_edit_page(self):
        """Создаёт страницу правки"""
        self.page_edit = ctk.CTkFrame(self.pages_container, fg_color=COLORS['bg_secondary'], corner_radius=12)
        
        header = ctk.CTkLabel(
            self.page_edit,
            text="↩️ Правка",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        )
        header.pack(pady=20, padx=20, fill="x")

        undo_card = ctk.CTkFrame(self.page_edit, fg_color=COLORS['bg_card'], corner_radius=10)
        undo_card.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(
            undo_card,
            text="Отменить последнюю сортировку",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_primary']
        ).pack(pady=15)

        ctk.CTkLabel(
            undo_card,
            text="Все перемещённые файлы будут возвращены",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        ).pack(pady=5)

        ctk.CTkButton(
            undo_card,
            text="↩️ Отменить",
            command=self.undo_sorting,
            height=40,
            corner_radius=8,
            fg_color=COLORS['warning'],
            width=250
        ).pack(pady=20)

    def create_help_page(self):
        """Создаёт страницу справки"""
        self.page_help = ctk.CTkScrollableFrame(self.pages_container, fg_color=COLORS['bg_secondary'], corner_radius=12)
        
        header = ctk.CTkLabel(
            self.page_help,
            text="❓ Справка",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        )
        header.pack(pady=20, padx=20, fill="x")

        info_card = ctk.CTkFrame(self.page_help, fg_color=COLORS['bg_card'], corner_radius=10)
        info_card.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            info_card,
            text="FileFlow v0.5",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['accent']
        ).pack(pady=10)

        ctk.CTkLabel(
            info_card,
            text="Умная сортировка файлов",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        ).pack(pady=5)

        btn_frame = ctk.CTkFrame(self.page_help, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="📖 Документация",
            command=lambda: webbrowser.open("https://github.com/Expense22/FileFlow/wiki"),
            height=35,
            corner_radius=8,
            fg_color=COLORS['bg_card'],
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🔍 Проверить обновления",
            command=self.check_updates,
            height=35,
            corner_radius=8,
            fg_color=COLORS['accent'],
            width=200
        ).pack(side="left", padx=5)

        btn_frame2 = ctk.CTkFrame(self.page_help, fg_color="transparent")
        btn_frame2.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            btn_frame2,
            text="⭐ GitHub",
            command=lambda: webbrowser.open("https://github.com/Expense22/FileFlow"),
            height=35,
            corner_radius=8,
            fg_color=COLORS['bg_card'],
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame2,
            text="🐛 Сообщить об ошибке",
            command=lambda: webbrowser.open("https://github.com/Expense22/FileFlow/issues"),
            height=35,
            corner_radius=8,
            fg_color=COLORS['bg_card'],
            width=200
        ).pack(side="left", padx=5)

    def browse_folder(self):
        """Выбор папки"""
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.selected_path = folder
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)
            self.log(f"Выбрана папка: {folder}")

    def analyze_folder(self):
        """Анализ папки"""
        if not self.selected_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку!")
            return

        self.log("Анализ папки...")
        
        for widget in self.stats_scroll.winfo_children():
            widget.destroy()

        try:
            config_path = Path(__file__).parent.parent / 'config' / 'rules.json'
            
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

            ctk.CTkLabel(
                self.stats_scroll,
                text=f"Всего файлов: {total_files}",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            ).pack(pady=5, padx=5, anchor="w")
            
            separator = ctk.CTkFrame(self.stats_scroll, height=2, fg_color="#444444")
            separator.pack(pady=5, padx=5, fill="x")

            sorted_stats = sorted(
                [(k, v) for k, v in stats.items() if v['count'] > 0],
                key=lambda x: x[1]['count'],
                reverse=True
            )

            color_palette = ['#00CED1', '#FF8C00', '#8A2BE2', '#FF6347', 
                           '#32CD32', '#FFD700', '#4169E1', '#FF1493']

            for i, (rule_id, data) in enumerate(sorted_stats):
                size_str = self.format_size(data['size'])
                percentage = (data['count'] / total_files * 100) if total_files > 0 else 0
                
                category_frame = ctk.CTkFrame(self.stats_scroll, fg_color="transparent")
                category_frame.pack(pady=5, padx=5, fill="x")
                
                header_frame = ctk.CTkFrame(category_frame, fg_color="transparent")
                header_frame.pack(fill="x")
                
                indicator = ctk.CTkFrame(
                    header_frame,
                    width=12,
                    height=20,
                    fg_color=color_palette[i % len(color_palette)],
                    corner_radius=3
                )
                indicator.pack(side="left", padx=(0, 10))
                
                ctk.CTkLabel(
                    header_frame,
                    text=data['name'],
                    font=ctk.CTkFont(size=11, weight="bold"),
                    anchor="w"
                ).pack(side="left", padx=(0, 10))
                
                ctk.CTkLabel(
                    header_frame,
                    text=f"{data['count']} файлов ({percentage:.1f}%)",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS['text_secondary'],
                    anchor="w"
                ).pack(side="left")
                
                ctk.CTkLabel(
                    header_frame,
                    text=size_str,
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS['text_secondary'],
                    anchor="e"
                ).pack(side="right", padx=(10, 0))
                
                bar_container = ctk.CTkFrame(
                    category_frame,
                    height=8,
                    fg_color="#2b2b2b",
                    corner_radius=4
                )
                bar_container.pack(pady=(5, 0), fill="x")
                
                bar_width = int(380 * percentage / 100) if percentage > 0 else 1
                ctk.CTkFrame(
                    bar_container,
                    height=8,
                    width=bar_width,
                    fg_color=color_palette[i % len(color_palette)],
                    corner_radius=4
                ).pack(side="left", padx=0, pady=0)

            self.statistics = stats
            self.log(f"Анализ завершён: {total_files} файлов")

        except Exception as e:
            self.log(f"Ошибка анализа: {e}")
            messagebox.showerror("Ошибка", f"Не удалось проанализировать папку:\n{e}")

    def start_sorting(self):
        """Запуск сортировки"""
        if not self.selected_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку!")
            return

        mode_text = "Dry Run (тест)" if self.dry_run else "LIVE"
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Запустить сортировку в режиме {mode_text}?\n\n"
            f"Папка: {self.selected_path}"
        )
        
        if not confirm:
            return

        self.log(f"Запуск сортировки ({mode_text})...")

        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            settings_path = base_dir / 'config' / 'settings.json'

            engine = FileFlowEngine(config_path, settings_path)
            result = engine.run(
                self.selected_path, 
                dry_run=self.dry_run, 
                gui=self, 
                recursive=self.recursive_mode
            )

            if result:
                self.log("Сортировка завершена успешно!")
                messagebox.showinfo("Успех", "Сортировка завершена успешно!")
                self.last_sort_data = {
                    'path': self.selected_path,
                    'timestamp': datetime.now()
                }
            else:
                self.log("Сортировка прервана")
                messagebox.showwarning("Внимание", "Сортировка прервана")

        except Exception as e:
            self.log(f"Ошибка сортировки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось выполнить сортировку:\n{e}")

    def find_duplicates(self):
        """Поиск дубликатов"""
        if not self.selected_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку!")
            return

        self.log("Поиск дубликатов...")
        
        # Окно прогресса
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Поиск дубликатов")
        progress_window.geometry("300x150")
        progress_window.transient(self)
        progress_window.attributes('-topmost', True)
        
        ctk.CTkLabel(
            progress_window,
            text="🔍 Сканирование...",
            font=ctk.CTkFont(size=14)
        ).pack(pady=20)

        progress_bar = ctk.CTkProgressBar(progress_window, width=250)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        status_label = ctk.CTkLabel(
            progress_window,
            text="Подготовка...",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        status_label.pack(pady=5)

        result = {'duplicates': None, 'error': None}
        window_closed = [False]
        
        def search_thread():
            try:
                finder = DuplicateFinder()
                duplicates = finder.find_duplicates(
                    self.selected_path, 
                    recursive=True,
                    min_size=10240
                )
                result['duplicates'] = (finder, duplicates)
            except Exception as e:
                result['error'] = str(e)
                import traceback
                traceback.print_exc()
            finally:
                try:
                    if not window_closed[0]:
                        window_closed[0] = True
                        progress_window.destroy()
                except:
                    pass
        
        def update_progress(current, total):
            try:
                if not window_closed[0] and total > 0:
                    progress = current / total
                    progress_bar.set(progress)
                    status_label.configure(text=f"Обработано: {current}/{total}")
                    progress_window.update()
            except:
                pass
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
        
        # Ждём завершения без блокировки
        while thread.is_alive():
            try:
                if not window_closed[0]:
                    progress_window.update()
                import time
                time.sleep(0.1)
            except:
                window_closed[0] = True
                break
        
        # Проверяем результат
        if result['error']:
            messagebox.showerror("Ошибка", f"Не удалось найти дубликаты:\n{result['error']}")
            return
        
        if result['duplicates']:
            finder, duplicates = result['duplicates']
            if duplicates:
                dup_count = finder.get_duplicates_count()
                wasted = finder.get_wasted_space()
                self.log(f"Найдено дубликатов: {dup_count} файлов ({self.format_size(wasted)})")
                self.show_duplicates_window(finder, duplicates)
            else:
                messagebox.showinfo("Результат", "Дубликаты не найдены!")

    def show_duplicates_window(self, finder, duplicates):
        """Окно с дубликатами"""
        dup_window = ctk.CTkToplevel(self)
        dup_window.title("Дубликаты файлов")
        dup_window.geometry("900x600")
        dup_window.transient(self)
        
        ctk.CTkLabel(
            dup_window,
            text="Найденные дубликаты",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['danger']
        ).pack(pady=10)
        
        wasted_space = finder.get_wasted_space()
        dup_count = finder.get_duplicates_count()
        
        stats_frame = ctk.CTkFrame(dup_window, fg_color=COLORS['bg_card'], corner_radius=8)
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
            text_color=COLORS['success']
        ).pack(pady=5)
        
        scroll_frame = ctk.CTkScrollableFrame(dup_window, fg_color=COLORS['bg_card'], corner_radius=8)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        checkboxes = {}
        group_num = 0
        
        for file_hash, files in duplicates.items():
            group_num += 1
            
            group_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS['bg_secondary'], corner_radius=8)
            group_frame.pack(pady=5, padx=5, fill="x")
            
            ctk.CTkLabel(
                group_frame,
                text=f"Группа {group_num} ({len(files)} файлов)",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS['warning']
            ).pack(pady=5, padx=10, anchor="w")
            
            for i, filepath in enumerate(files):
                file_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
                file_frame.pack(pady=2, padx=10, fill="x")
                
                cb = ctk.CTkCheckBox(
                    file_frame,
                    text="",
                    width=20,
                    onvalue=filepath,
                    offvalue=""
                )
                if i > 0:
                    cb.select()
                cb.pack(side="left", padx=5)
                checkboxes[filepath] = cb
                
                ctk.CTkLabel(
                    file_frame,
                    text=filepath,
                    font=ctk.CTkFont(size=9),
                    anchor="w"
                ).pack(side="left", padx=5, fill="x", expand=True)
                
                try:
                    size = os.path.getsize(filepath)
                    ctk.CTkLabel(
                        file_frame,
                        text=self.format_size(size),
                        font=ctk.CTkFont(size=8),
                        text_color=COLORS['text_secondary']
                    ).pack(side="right", padx=5)
                except:
                    pass
        
        btn_frame = ctk.CTkFrame(dup_window, fg_color="transparent")
        btn_frame.pack(pady=15, padx=20, fill="x")
        
        def delete_selected():
            to_delete = [cb.get() for cb in checkboxes.values() if cb.get()]
            if to_delete:
                confirm = messagebox.askyesno(
                    "Подтверждение",
                    f"Удалить {len(to_delete)} файлов?"
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
                    messagebox.showinfo("Успех", f"Удалено {deleted} файлов!")
        
        ctk.CTkButton(
            btn_frame,
            text="Удалить выбранные",
            command=delete_selected,
            height=40,
            corner_radius=8,
            fg_color=COLORS['danger'],
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

    def undo_sorting(self):
        """Отмена сортировки"""
        if not self.last_sort_data:
            messagebox.showinfo("Информация", "Нет последней сортировки для отмены")
            return
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Отменить последнюю сортировку?"
        )
        
        if not confirm:
            return
        
        self.log("Отмена сортировки...")
        
        try:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'rules.json'
            settings_path = base_dir / 'config' / 'settings.json'
            
            engine = FileFlowEngine(config_path, settings_path)
            success, message = engine.undo_last_sort(self.last_sort_data['path'])
            
            if success:
                self.log(f"Отмена завершена: {message}")
                messagebox.showinfo("Успех", f"Отмена завершена:\n{message}")
                self.last_sort_data = None
            else:
                self.log(f"Ошибка отмены: {message}")
                messagebox.showerror("Ошибка", f"Не удалось отменить:\n{message}")
                
        except Exception as e:
            self.log(f"Ошибка отмены: {e}")
            messagebox.showerror("Ошибка", f"Не удалось отменить:\n{e}")

    def check_updates(self):
        """Проверка обновлений"""
        self.log("Проверка обновлений...")
        messagebox.showinfo("Обновления", "Установлена последняя версия v0.5")

    def format_size(self, size_bytes: int) -> str:
        """Форматирование размера"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def log(self, message):
        """Логирование"""
        print(f"[FileFlow] {message}")
        logger.info(message)


def run_app():
    """Запуск приложения"""
    app = FileFlowApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()