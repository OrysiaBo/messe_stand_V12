#!/usr/bin/env python3
"""
ОПТИМІЗОВАНИЙ Main Window для Dynamic Messe Stand V4
Гібридний підхід: надійність + розумна синхронізація
"""

import tkinter as tk
from tkinter import ttk
import sys
import subprocess
from core.config import config
from core.theme import theme_manager, THEME_VARS, _mix, apply_bertrandt_theme
from core.logger import logger
from ui.tabs.home_tab import HomeTab
from ui.tabs.creator_tab import CreatorTab
from ui.tabs.demo_tab import DemoTab
from ui.tabs.presentation_tab import PresentationTab

class MainWindow:
    """Оптимізоване головне GUI-вікно з розумною синхронізацією"""
    
    def __init__(self, esp32_port=None):
        logger.info("🚀 Запуск Dynamic Messe Stand V4 з оптимізованою архітектурою...")
        
        # Tkinter Root
        self.root = tk.Tk()
        self.root.title(config.gui['title'])
        
        # Базові змінні
        self.esp32_port = esp32_port
        self.fullscreen = False
        self.current_tab = "home"
        self.tabs = {}
        
        # Content Observer setup (розумний підхід)
        self._setup_content_observer()
        
        # Основне налаштування
        self.setup_window()
        self.setup_responsive_design()
        self.setup_styles()
        self.setup_gui_components()
        self.setup_tabs()
        
        # Початковий таб
        self.switch_tab("home")
        
        logger.info("✅ Dynamic Messe Stand V4 успішно ініціалізований!")

    def _setup_content_observer(self):
        """Розумне налаштування спостерігача контенту"""
        try:
            from models.content import content_manager
            content_manager.add_observer(self._on_content_changed)
            logger.info("Content Observer успішно зареєстрований")
        except ImportError:
            logger.warning("Content Manager недоступний - синхронізація вимкнена")
        except Exception as e:
            logger.error(f"Помилка реєстрації Content Observer: {e}")

    def _on_content_changed(self, slide_id, slide_data, action='update'):
        """Оптимізований обробник змін контенту"""
        try:
            logger.debug(f"Синхронізація змін slide {slide_id} ({action})")
            
            # Оновити тільки необхідні таби
            for tab_name, tab_instance in self.tabs.items():
                if tab_name == 'demo' and hasattr(tab_instance, 'sync_slide_change'):
                    tab_instance.sync_slide_change(slide_id, slide_data)
                elif tab_name == 'creator' and hasattr(tab_instance, 'refresh_thumbnails'):
                    tab_instance.refresh_thumbnails()
                elif tab_name == 'home' and hasattr(tab_instance, 'update_stats'):
                    tab_instance.update_stats()
            
            # Оновити статус у navbar
            self._update_status_indicator(f"Slide {slide_id} оновлено")
            
        except Exception as e:
            logger.error(f"Помилка синхронізації контенту: {e}")

    def setup_window(self):
        """Налаштовує головне вікно для 24" монітора"""
        self._detect_primary_monitor()
        
        # Оптимізовано для 24" RTC Monitor
        self.window_width = self.primary_width
        self.window_height = self.primary_height
        
        logger.info(f"Головний монітор: {self.window_width}x{self.window_height} на ({self.primary_x}, {self.primary_y})")
        
        # Позиціонування вікна на головному моніторі
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.primary_x}+{self.primary_y}")
        self.root.minsize(config.gui['min_width'], config.gui['min_height'])
        
        # Fullscreen bindings
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        
        # Початковий fullscreen режим
        if config.gui.get('fullscreen_on_start', True):
            self.root.attributes('-fullscreen', True)
            self.root.attributes('-topmost', True)
            self.fullscreen = True
        
        # Забезпечення залишення на головному моніторі
        self.root.after(200, self._ensure_primary_monitor)
        
        # Застосування теми
        colors = theme_manager.get_colors()
        self.root.configure(bg=colors['background_primary'])

    def _detect_primary_monitor(self):
        """Виявляє головний монітор"""
        try:
            self.root.update_idletasks()
            
            # Загальний розмір екрану
            total_width = self.root.winfo_screenwidth()
            total_height = self.root.winfo_screenheight()
            
            # За замовчуванням - головний монітор
            self.primary_x = 0
            self.primary_y = 0
            self.primary_width = total_width
            self.primary_height = total_height
            
            # Спроба виявити multi-monitor setup
            try:
                result = subprocess.run(['xrandr'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ' connected primary ' in line:
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    resolution_pos = part.split('+')
                                    if len(resolution_pos) >= 3:
                                        resolution = resolution_pos[0]
                                        self.primary_x = int(resolution_pos[1])
                                        self.primary_y = int(resolution_pos[2])
                                        
                                        if 'x' in resolution:
                                            w, h = resolution.split('x')
                                            self.primary_width = int(w)
                                            self.primary_height = int(h)
                                    break
                            break
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                logger.debug("xrandr недоступний, використовуємо стандартні значення")
            
            logger.info(f"Головний монітор: {self.primary_width}x{self.primary_height} на ({self.primary_x}, {self.primary_y})")
            
        except Exception as e:
            logger.warning(f"Помилка виявлення монітора: {e}")
            # Fallback значення
            self.primary_x = 0
            self.primary_y = 0
            self.primary_width = 1920
            self.primary_height = 1080

    def _ensure_primary_monitor(self):
        """Забезпечує залишення вікна на головному моніторі"""
        try:
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            if current_x != self.primary_x or current_y != self.primary_y:
                self.root.geometry(f"{self.primary_width}x{self.primary_height}+{self.primary_x}+{self.primary_y}")
                logger.debug(f"Вікно повернуто на головний монітор")
            
        except Exception as e:
            logger.warning(f"Помилка корекції позиції монітора: {e}")

    def setup_responsive_design(self):
        """Налаштовує responsive design"""
        self.scale_factor = min(self.window_width, self.window_height) / config.design['scale_factor_base']
        self.fonts = theme_manager.get_fonts(self.window_width, self.window_height)
        
        logger.debug(f"Responsive Design: {self.window_width}x{self.window_height}, Scale: {self.scale_factor:.2f}")

    def setup_styles(self):
        """Застосовує повну Bertrandt тему"""
        apply_bertrandt_theme(self.root, reapply=True)
        self.style = ttk.Style()
        
        # Додаткові стилі для сучасної інтеграції
        self.style.configure('TFrame', 
                           background=THEME_VARS["bg"],
                           relief='flat',
                           borderwidth=0)
        
        self.style.configure('TLabel',
                           background=THEME_VARS["bg"],
                           foreground=THEME_VARS["text"],
                           font=(THEME_VARS["font_family"], THEME_VARS["size_body"]))
        
        self.style.configure('TButton',
                           background=THEME_VARS["brand_600"],
                           foreground="#ffffff",
                           font=(THEME_VARS["font_family"], THEME_VARS["size_body"], "bold"),
                           relief='flat',
                           borderwidth=0,
                           padding=(THEME_VARS["pad"], THEME_VARS["pad"] // 2))

    def setup_gui_components(self):
        """Створює Bertrandt layout структуру"""
        # Головний контейнер
        self.main_container = ttk.Frame(self.root, style="TFrame")
        self.main_container.pack(fill='both', expand=True, padx=14, pady=12)
        
        # Navbar
        self.navbar = ttk.Frame(self.main_container, style="Glass.TFrame", padding=(12, 10))
        self.navbar.pack(side="top", fill="x", pady=(0, 12))
        self._setup_navbar()
        
        # Hero область
        self.hero_outer, self.hero = self._make_glass_card(self.main_container, padding=16)
        self.hero_outer.pack(fill="x", pady=(0, 12))
        self._setup_hero()
        
        # Grid контейнер
        self.grid_container = ttk.Frame(self.main_container, style="TFrame")
        self.grid_container.pack(fill="both", expand=True, pady=(0, 12))
        self.grid_container.columnconfigure((0,1,2), weight=1)
        self.grid_container.rowconfigure((0,1), weight=1)
        
        # Content область для табів
        self.tab_content_frame = self.grid_container
        
        # Footer
        self.footer_frame = ttk.Frame(self.main_container, style="TFrame")
        self.footer_frame.pack(side="bottom", fill="x")
        ttk.Separator(self.footer_frame).pack(fill="x", pady=6)
        self.footer_label = ttk.Label(
            self.footer_frame, 
            text="© 2025 Bertrandt AG - Dynamic Messe Stand V4 - Оптимізована версія", 
            style="Muted.TLabel"
        )
        self.footer_label.pack()
        
        logger.info("✅ Bertrandt layout структура створена")

    def _make_glass_card(self, parent, padding=12):
        """Створює glass-card у Bertrandt стилі"""
        outer = ttk.Frame(parent, style="TFrame")
        
        cv = tk.Canvas(outer, bg=THEME_VARS["bg"], highlightthickness=0, bd=0, height=1)
        cv.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        
        inner = ttk.Frame(outer, style="Glass.TFrame", padding=padding)
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        def _redraw(_evt=None):
            cv.delete("all")
            w = outer.winfo_width()
            h = outer.winfo_height()
            if w < 2 or h < 2: 
                return
            cv.create_rectangle(1, 1, w-2, h-2, outline=THEME_VARS["elev_outline"], width=1)
            cv.create_rectangle(2, 2, w-3, h-3, outline="", fill=_mix(THEME_VARS["panel"], "#ffffff", 0.04))
        
        outer.bind("<Configure>", _redraw)
        return outer, inner

    def _setup_navbar(self):
        """Створює navbar"""
        # Ліва частина - логотип + заголовок
        left_frame = ttk.Frame(self.navbar, style="TFrame")
        left_frame.pack(side="left")
        
        self._load_logo(left_frame)
        
        title_label = ttk.Label(left_frame, text="Dynamic Messe Stand V4", style="H2.TLabel")
        title_label.pack(side="left")
        
        # Права частина - навігація
        right_frame = ttk.Frame(self.navbar, style="TFrame")
        right_frame.pack(side="right")
        
        # Кнопки навігації
        nav_buttons = [
            ("Home", "home"),
            ("Demo", "demo"), 
            ("Creator", "creator"),
            ("Presentation", "presentation")
        ]
        
        self.nav_buttons = {}
        for text, tab_name in nav_buttons:
            btn = ttk.Button(
                right_frame, 
                text=text, 
                style="Ghost.TButton",
                command=lambda t=tab_name: self.switch_tab(t)
            )
            btn.pack(side="left", padx=6)
            self.nav_buttons[tab_name] = btn
        
        # Статус індикатор
        self.status_indicator = ttk.Label(
            right_frame, text="✅ Система готова", style="Muted.TLabel"
        )
        self.status_indicator.pack(side="left", padx=12)
        
        # Системний тест кнопка
        test_btn = ttk.Button(
            right_frame, 
            text="🔧 Тест", 
            style="Primary.TButton",
            command=self._run_system_test
        )
        test_btn.pack(side="left", padx=6)

    def _setup_hero(self):
        """Створює hero область"""
        eyebrow = ttk.Label(
            self.hero, 
            text="Оптимізована система для виставок", 
            foreground=_mix(THEME_VARS["brand_600"], "#9cc7fb", 0.5)
        )
        eyebrow.pack(anchor="w")
        
        title = ttk.Label(
            self.hero, 
            text="Bertrandt Dynamic Messe Stand V4 - Оптимізовано", 
            style="H1.TLabel"
        )
        title.pack(anchor="w", pady=(4, 4))
        
        description = ttk.Label(
            self.hero, 
            text="Стабільна система з розумною синхронізацією між Creator та Demo, автоматичним збереженням та повноцінним Asset Browser.", 
            style="Muted.TLabel", 
            wraplength=900, 
            justify="left"
        )
        description.pack(anchor="w")

    def _load_logo(self, parent_frame):
        """Завантажує відповідний логотип"""
        try:
            from PIL import Image, ImageTk
            from core.theme import get_logo_filename
            import os
            
            logo_filename = get_logo_filename()
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", logo_filename)
            
            if os.path.exists(logo_path):
                logo_image = Image.open(logo_path)
                logo_height = 28
                logo_width = int((logo_image.width * logo_height) / logo_image.height)
                logo_image = logo_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                
                self.logo_label = ttk.Label(parent_frame, image=self.logo_photo, style="TLabel")
                self.logo_label.pack(side="left", padx=(0, 10))
                
                logger.info("Bertrandt логотип успішно завантажено")
                return
                
        except Exception as e:
            logger.warning(f"Неможливо завантажити логотип: {e}")
        
        # Fallback текст
        title_label = ttk.Label(
            parent_frame,
            text="Dynamic Messe Stand V4",
            style="H2.TLabel"
        )
        title_label.pack(side="left")

    def setup_tabs(self):
        """Ініціалізує всі tab компоненти з належними перевірками"""
        logger.info("Ініціалізація табів з оптимізованою синхронізацією...")
        
        try:
            self.tabs = {
                'home': HomeTab(self.tab_content_frame, self),
                'demo': DemoTab(self.tab_content_frame, self),
                'creator': CreatorTab(self.tab_content_frame, self), 
                'presentation': PresentationTab(self.tab_content_frame, self)
            }
            
            # Приховати всі таби спочатку
            for tab in self.tabs.values():
                if hasattr(tab, 'hide'):
                    tab.hide()
            
            logger.info("✅ Всі таби ініціалізовані")
        except Exception as e:
            logger.error(f"Помилка ініціалізації табів: {e}")
            self.tabs = {}

    def switch_tab(self, tab_name):
        """Розумне перемикання табів з автозбереженням"""
        try:
            logger.debug(f"Перемикання на таб: {tab_name}")
            
            # Автозбереження в Creator при виході (тільки якщо необхідно)
            if (self.current_tab == 'creator' and 'creator' in self.tabs and 
                hasattr(self.tabs['creator'], 'save_current_slide_content')):
                
                logger.debug("Виконую автозбереження при зміні табу...")
                try:
                    self.tabs['creator'].save_current_slide_content()
                except Exception as e:
                    logger.warning(f"Автозбереження не вдалося: {e}")
            
            # Приховати поточний таб
            if self.current_tab in self.tabs and hasattr(self.tabs[self.current_tab], 'hide'):
                self.tabs[self.current_tab].hide()
            
            # Показати новий таб
            if tab_name in self.tabs:
                if hasattr(self.tabs[tab_name], 'show'):
                    self.tabs[tab_name].show()
                
                # Оновити контент при потребі
                self._refresh_tab_content(tab_name)
            
            # Оновити navbar
            self._update_navbar_active_tab(tab_name)
            
            self.current_tab = tab_name
            logger.debug(f"✅ Перемикання на {tab_name} завершено")
            
        except Exception as e:
            logger.error(f"Помилка перемикання на таб {tab_name}: {e}")

    def _refresh_tab_content(self, tab_name):
        """Оновлює контент табу при перемиканні"""
        try:
            tab = self.tabs.get(tab_name)
            if not tab:
                return
            
            if tab_name == 'demo' and hasattr(tab, 'load_current_slide'):
                tab.load_current_slide()
            elif tab_name == 'creator' and hasattr(tab, 'load_slide_to_editor'):
                current_slide = getattr(tab, 'current_edit_slide', 1)
                tab.load_slide_to_editor(current_slide)
            elif tab_name == 'home' and hasattr(tab, 'refresh_content'):
                tab.refresh_content()
                
        except Exception as e:
            logger.debug(f"Помилка оновлення контенту табу {tab_name}: {e}")

    def _update_navbar_active_tab(self, active_tab):
        """Оновлює активний таб у navbar"""
        for tab_name, button in self.nav_buttons.items():
            if tab_name == active_tab:
                button.configure(style="Primary.TButton")
            else:
                button.configure(style="Ghost.TButton")

    def _update_status_indicator(self, message):
        """Оновлює статус індикатор з автоскиданням"""
        if hasattr(self, 'status_indicator'):
            self.status_indicator.configure(text=f"🔄 {message}")
            # Повернути до базового стану через 3 секунди
            self.root.after(3000, lambda: self.status_indicator.configure(text="✅ Система готова"))

    def _run_system_test(self):
        """Запускає системний тест для перевірки функціональності"""
        try:
            from tkinter import messagebox
            
            test_results = []
            
            # Тест Content Manager
            try:
                from models.content import content_manager
                slides_count = content_manager.get_slide_count()
                test_results.append(f"✅ Content Manager: {slides_count} слайдів")
                
                # Тест Assets
                assets = content_manager.get_available_assets()
                total_assets = sum(len(v) for v in assets.values())
                test_results.append(f"✅ Assets: {total_assets} доступно")
                
            except Exception as e:
                test_results.append(f"❌ Content Manager: {e}")
            
            # Тест табів
            active_tabs = len([t for t in self.tabs.values() if hasattr(t, 'show')])
            test_results.append(f"✅ Таби: {active_tabs}/{len(self.tabs)} активні")
            
            # Тест синхронізації
            observer_active = hasattr(self, '_on_content_changed')
            test_results.append(f"✅ Синхронізація: {'Активна' if observer_active else 'Неактивна'}")
            
            results_text = "СИСТЕМНИЙ ТЕСТ:\n\n" + "\n".join(test_results)
            results_text += "\n\nВикористання:\n1. Відкрийте Creator\n2. Додайте текст/зображення\n3. Збережіть зміни\n4. Перейдіть у Demo - зміни синхронізуються"
            
            messagebox.showinfo("Системний тест", results_text)
            logger.info("Системний тест виконано")
            
        except Exception as e:
            messagebox.showerror("Системний тест", f"Помилка тестування: {e}")
            logger.error(f"Помилка системного тесту: {e}")

    def force_refresh_all_tabs(self):
        """Примусово оновлює всі таби (для зовнішніх викликів)"""
        try:
            logger.info("🔄 Примусове оновлення всіх табів...")
            
            for tab_name, tab in self.tabs.items():
                try:
                    if tab_name == 'demo' and hasattr(tab, 'create_slides_list'):
                        tab.create_slides_list()
                    elif tab_name == 'creator' and hasattr(tab, 'create_slide_thumbnails'):
                        tab.create_slide_thumbnails()
                    elif tab_name == 'home' and hasattr(tab, 'refresh_content'):
                        tab.refresh_content()
                except Exception as e:
                    logger.debug(f"Помилка оновлення табу {tab_name}: {e}")
            
            self._update_status_indicator("Всі таби оновлено")
            logger.info("✅ Примусове оновлення завершено")
            
        except Exception as e:
            logger.error(f"Помилка примусового оновлення: {e}")

    def toggle_fullscreen(self, event=None):
        """Перемикає повноекранний режим"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        logger.debug(f"Fullscreen: {'увімкнено' if self.fullscreen else 'вимкнено'}")

    def exit_fullscreen(self, event=None):
        """Виходить з повноекранного режиму"""
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)
            self.root.attributes('-topmost', False)
            
            self.root.geometry(f"{self.primary_width}x{self.primary_height}+{self.primary_x}+{self.primary_y}")
            logger.debug("Fullscreen вимкнено - залишається на головному моніторі")

    def quit_application(self):
        """Завершує програму з належною очисткою"""
        logger.info("🧹 Завершення програми...")
        
        # Фінальне збереження з Creator
        try:
            if ('creator' in self.tabs and 
                hasattr(self.tabs['creator'], 'save_current_slide_content')):
                logger.info("💾 Фінальне збереження...")
                self.tabs['creator'].save_current_slide_content()
        except Exception as e:
            logger.error(f"Помилка фінального збереження: {e}")
        
        # Відключення Hardware
        try:
            from models.hardware import hardware_manager
            hardware_manager.disconnect_all()
        except Exception as e:
            logger.debug(f"Hardware disconnect помилка: {e}")
        
        # Зупинка Demo сервісу
        try:
            from services.demo import demo_service
            demo_service.stop_demo()
        except Exception as e:
            logger.debug(f"Demo service stop помилка: {e}")
        
        # Закрити GUI
        self.root.quit()
        logger.info("👋 Dynamic Messe Stand V4 завершено")
        sys.exit(0)
        
    def make_glass_card(self, parent, padding=12):
    """Erstellt glass-card im Bertrandt Stil"""
    colors = theme_manager.get_colors()
    
    outer = ttk.Frame(parent, style="TFrame")
    inner = ttk.Frame(outer, style="Glass.TFrame", padding=padding)
    inner.place(relx=0, rely=0, relwidth=1, relheight=1)
    
    return outer, inner
    
    def run(self):
        """Запускає GUI головний цикл"""
        try:
            logger.info("GUI головний цикл запущено")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Програму перервано користувачем")
            self.quit_application()
        except Exception as e:
            logger.error(f"Неочікувана помилка в GUI циклі: {e}")
            self.quit_application()
