#!/usr/bin/env python3
"""
Demo Tab für die Bertrandt GUI
Präsentations-Modus mit Slide-Navigation und automatischer Steuerung
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer
from models.content import content_manager
from services.demo import demo_service

class DemoTab:
    """Demo-Tab für Live-Präsentationen"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.visible = False
        self.current_slide = 1
        self.total_slides = 10
        self.auto_play = False
        self.auto_play_interval = 5  # Sekunden
        self.auto_play_thread = None
        self.slide_buttons = {}
        self.last_update_time = 0
        
        # Demo-Service Konfiguration
        self.demo_running = False
        
        self.create_demo_content()
        
        # Content-Manager Observer hinzufügen
        content_manager.add_observer(self.on_content_changed)
        
    def on_content_changed(self, slide_id, slide_data, action='update'):
        """Obroblyuvach zminy kontentu (synkhronizatsiya z Creator) - optimizovanyj"""
        try:
            current_time = time.time()
            # Ogranicheniye chastoty obnovlenij - ne boleye raza v sekundu
            if current_time - self.last_update_time < 1.0:
                return
            
            if action == 'update' or action == 'load':
                # Obnovlyuvaty spisok slajdiv tilky yaksho zminilsya zagolovok
                if hasattr(slide_data, 'title'):
                    current_button = self.slide_buttons.get(slide_id)
                    if current_button:
                        # Obnoviti tilky konkretnui knopku
                        title = slide_data.title
                        display_title = title[:20] + "..." if len(title) > 20 else title
                        current_button.configure(text=f"{slide_id}\n{display_title}")
                    else:
                        # Povnistyu perestvoriti spisok tilky yaksho knopky ne isnuye
                        self.create_slides_list()
                
                # Peremalyuvaty potochnyj slajd yaksho vin buv zminenyj
                if slide_id == self.current_slide:
                    self.render_current_slide()
                
                self.last_update_time = current_time
                logger.debug(f"Demo synchronized with content changes for slide {slide_id}")
                
            elif action == 'delete':
                # Obrobyty vydalennya slajdu
                if slide_id == self.current_slide and self.current_slide > 1:
                    self.current_slide -= 1
                
                self.create_slides_list()
                self.load_current_slide()
        
        except Exception as e:
            logger.error(f"Error handling content change in demo: {e}")
        
    def create_demo_content(self):
        """Erstellt den Demo-Tab Inhalt"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Haupt-Container
        self.container = tk.Frame(self.parent, bg=colors['background_primary'])
        
        # Header-Toolbar
        self.create_demo_header()
        
        # 2-Spalten Layout
        content_frame = tk.Frame(self.container, bg=colors['background_primary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Grid-Layout
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=300)  # Slide-Navigation (links)
        content_frame.grid_columnconfigure(1, weight=1, minsize=900)  # Slide-Display (rechts)
        
        # Spalte 1: Slide-Navigation
        self.create_slide_navigation(content_frame)
        
        # Spalte 2: Haupt-Display
        self.create_slide_display(content_frame)
        
        # Footer mit Controls
        self.create_demo_footer()
    
    def create_demo_header(self):
        """Erstellt die Demo-Header"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        header_frame = tk.Frame(
            self.container,
            bg=colors['background_secondary'],
            relief='flat',
            bd=0,
            height=80
        )
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        # Titel
        title_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        title_frame.pack(side='left', fill='y', padx=(15, 30))
        
        title_label = tk.Label(
            title_frame,
            text="🎯 Live Demo",
            font=fonts['title'],
            fg=colors['accent_primary'],
            bg=colors['background_secondary']
        )
        title_label.pack(anchor='w', pady=(15, 0))
        
        subtitle_label = tk.Label(
            title_frame,
            text="Interaktive Präsentation",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Demo-Steuerung
        controls_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        controls_frame.pack(side='left', fill='y', padx=20)
        
        # Start/Stop Demo
        self.demo_button = tk.Button(
            controls_frame,
            text="▶ Demo starten",
            font=fonts['button'],
            bg=colors['accent_secondary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.toggle_demo
        )
        self.demo_button.pack(side='left', padx=(0, 10), pady=15)
        
        # Auto-Play Toggle
        self.autoplay_button = tk.Button(
            controls_frame,
            text="🔄 Auto-Play",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.toggle_autoplay
        )
        self.autoplay_button.pack(side='left', padx=(0, 10), pady=15)
        
        # Slide-Info
        info_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        info_frame.pack(side='right', fill='y', padx=(20, 15))
        
        self.slide_info_label = tk.Label(
            info_frame,
            text="Slide 1 von 10",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.slide_info_label.pack(pady=(20, 5))
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            info_frame,
            variable=self.progress_var,
            maximum=100,
            length=150,
            mode='determinate'
        )
        self.progress_bar.pack()
    
    def create_slide_navigation(self, parent):
        """Erstellt die Slide-Navigation (links)"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Navigation Frame
        nav_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1,
            width=300
        )
        nav_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        nav_frame.grid_propagate(False)
        
        # Header
        nav_header = tk.Frame(nav_frame, bg=colors['background_secondary'])
        nav_header.pack(fill='x', padx=15, pady=(15, 10))
        
        header_label = tk.Label(
            nav_header,
            text="📑 Folien-Übersicht",
            font=fonts['title'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        header_label.pack(anchor='w')
        
        # Navigation Buttons
        nav_buttons_frame = tk.Frame(nav_header, bg=colors['background_secondary'])
        nav_buttons_frame.pack(fill='x', pady=(10, 0))
        
        prev_btn = tk.Button(
            nav_buttons_frame,
            text="◀",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            pady=5,
            cursor='hand2',
            command=self.previous_slide
        )
        prev_btn.pack(side='left', padx=(0, 5))
        
        next_btn = tk.Button(
            nav_buttons_frame,
            text="▶",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            pady=5,
            cursor='hand2',
            command=self.next_slide
        )
        next_btn.pack(side='left', padx=(5, 0))
        
        # Slides List Container
        list_frame = tk.Frame(nav_frame, bg=colors['background_secondary'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(10, 15))
        
        # Scrollable Slides List
        canvas = tk.Canvas(list_frame, bg=colors['background_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.slides_frame = tk.Frame(canvas, bg=colors['background_secondary'])
        
        self.slides_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.slides_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Slides erstellen
        self.create_slides_list()
    
    def create_slides_list(self):
        """Erstellt die Slides-Liste optimiziert"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Content-Manager verwenden
        slides = content_manager.get_all_slides()
        
        if not slides:
            logger.warning("Keine Slides gefunden für Demo")
            return
        
        # Lösche nur wenn komplett neue Struktur nötig
        if len(self.slide_buttons) != len(slides):
            for widget in self.slides_frame.winfo_children():
                widget.destroy()
            self.slide_buttons.clear()
        
        for slide_id, slide in slides.items():
            try:
                # Prüfe ob Button bereits existiert
                if slide_id in self.slide_buttons:
                    # Aktualisiere nur den Text
                    button = self.slide_buttons[slide_id]
                    title = slide.title
                    display_title = title[:20] + "..." if len(title) > 20 else title
                    button.configure(text=f"{slide_id}\n{display_title}")
                    continue
                
                # Erstelle neuen Button nur wenn nötig
                slide_container = tk.Frame(
                    self.slides_frame,
                    bg=colors['background_secondary']
                )
                slide_container.pack(fill='x', pady=2)
                
                # Button Style abhängig von Aktivität
                is_active = slide_id == self.current_slide
                bg_color = colors['accent_primary'] if is_active else colors['background_tertiary']
                
                title = slide.title
                display_title = title[:20] + "..." if len(title) > 20 else title
                
                slide_btn = tk.Button(
                    slide_container,
                    text=f"{slide_id}\n{display_title}",
                    font=fonts['body'],
                    bg=bg_color,
                    fg='white' if is_active else colors['text_primary'],
                    relief='flat',
                    bd=0,
                    width=25,
                    height=3,
                    cursor='hand2',
                    command=lambda sid=slide_id: self.goto_slide(sid),
                    justify='left',
                    anchor='w'
                )
                slide_btn.pack(fill='x', ipady=3)
                
                self.slide_buttons[slide_id] = slide_btn
                
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von Slide-Button {slide_id}: {e}")
        
        # Total slides aktualisieren
        self.total_slides = len(slides)
        self.update_slide_info()
    
    def create_slide_display(self, parent):
        """Erstellt das Haupt-Slide-Display (rechts)"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Display Frame
        display_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1
        )
        display_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Header
        display_header = tk.Frame(display_frame, bg=colors['background_secondary'])
        display_header.pack(fill='x', padx=20, pady=(15, 10))
        
        self.current_slide_label = tk.Label(
            display_header,
            text="Demo-Folie wird geladen...",
            font=fonts['display'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.current_slide_label.pack(anchor='w')
        
        # Slide Canvas - Hauptanzeige
        canvas_frame = tk.Frame(display_frame, bg=colors['background_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(10, 10))
        
        # Slide Canvas erstellen
        self.slide_canvas = tk.Canvas(
            canvas_frame,
            bg='#FFFFFF',  # Weiß für Slides
            relief='flat',
            bd=2,
            highlightthickness=0
        )
        self.slide_canvas.pack(fill='both', expand=True)
        
        # Canvas-Größe überwachen
        self.slide_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Initiale Slide laden
        self.slide_canvas.after(100, self.load_current_slide)
    
    def create_demo_footer(self):
        """Erstellt den Demo-Footer"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        footer_frame = tk.Frame(
            self.container,
            bg=colors['background_secondary'],
            height=50
        )
        footer_frame.pack(fill='x', padx=10, pady=5)
        footer_frame.pack_propagate(False)
        
        # Links: Timer-Info
        timer_frame = tk.Frame(footer_frame, bg=colors['background_secondary'])
        timer_frame.pack(side='left', fill='y', padx=15)
        
        self.timer_label = tk.Label(
            timer_frame,
            text="Demo bereit",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        self.timer_label.pack(pady=15)
        
        # Rechts: Vollbild Controls
        controls_frame = tk.Frame(footer_frame, bg=colors['background_secondary'])
        controls_frame.pack(side='right', fill='y', padx=15)
        
        fullscreen_btn = tk.Button(
            controls_frame,
            text="⛶ Vollbild",
            font=fonts['caption'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=self.main_window.toggle_fullscreen
        )
        fullscreen_btn.pack(pady=8)
    
    def load_current_slide(self):
        """Lädt und zeigt den aktuellen Slide"""
        try:
            slide = content_manager.get_slide(self.current_slide)
            
            if slide:
                # Slide-Titel aktualisieren
                self.current_slide_label.configure(text=f"Demo-Folie {self.current_slide}: {slide.title}")
                
                # Slide rendern
                self.render_current_slide()
                
                # Navigation aktualisieren
                self.update_slide_navigation()
                self.update_slide_info()
                
                logger.debug(f"Loaded slide {self.current_slide}: {slide.title}")
            else:
                logger.warning(f"Slide {self.current_slide} not found")
                self.current_slide_label.configure(text=f"Slide {self.current_slide} nicht gefunden")
                
        except Exception as e:
            logger.error(f"Error loading slide {self.current_slide}: {e}")
    
    def render_current_slide(self):
        """Rendert den aktuellen Slide auf die Canvas"""
        try:
            slide = content_manager.get_slide(self.current_slide)
            
            if not slide:
                return
            
            # Canvas-Größe ermitteln
            canvas_width = self.slide_canvas.winfo_width()
            canvas_height = self.slide_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:
                # Slide-Daten vorbereiten
                slide_data = {
                    'title': slide.title,
                    'content': slide.content,
                    'slide_number': self.current_slide,
                    'background_color': '#FFFFFF',
                    'text_color': '#1F1F1F'
                }
                
                # Slide mit dem gleichen Renderer wie Creator rendern
                SlideRenderer.render_slide_to_canvas(
                    self.slide_canvas,
                    slide_data,
                    canvas_width,
                    canvas_height
                )
                
                logger.debug(f"Rendered slide {self.current_slide} in demo")
            
        except Exception as e:
            logger.error(f"Error rendering slide: {e}")
    
    def on_canvas_resize(self, event):
        """Canvas-Größenänderung behandeln"""
        # Slide neu rendern bei Größenänderung
        self.main_window.root.after(100, self.render_current_slide)
    
    def update_slide_navigation(self):
        """Aktualisiert die Slide-Navigation Buttons"""
        colors = theme_manager.get_colors()
        
        for slide_id, button in self.slide_buttons.items():
            if slide_id == self.current_slide:
                button.configure(
                    bg=colors['accent_primary'],
                    fg='white'
                )
            else:
                button.configure(
                    bg=colors['background_tertiary'],
                    fg=colors['text_primary']
                )
    
    def update_slide_info(self):
        """Aktualisiert die Slide-Information"""
        try:
            self.slide_info_label.configure(text=f"Slide {self.current_slide} von {self.total_slides}")
            
            # Progress Bar aktualisieren
            if self.total_slides > 0:
                progress = (self.current_slide / self.total_slides) * 100
                self.progress_var.set(progress)
        except Exception as e:
            logger.error(f"Error updating slide info: {e}")
    
    def goto_slide(self, slide_id):
        """Geht zu einem bestimmten Slide"""
        try:
            self.current_slide = slide_id
            self.load_current_slide()
            logger.info(f"Demo: Navigated to slide {slide_id}")
        except Exception as e:
            logger.error(f"Error going to slide {slide_id}: {e}")
    
    def previous_slide(self):
        """Geht zum vorherigen Slide"""
        if self.current_slide > 1:
            self.current_slide -= 1
            self.load_current_slide()
    
    def next_slide(self):
        """Geht zum nächsten Slide"""
        if self.current_slide < self.total_slides:
            self.current_slide += 1
            self.load_current_slide()
        elif self.auto_play:  # Restart bei Auto-Play
            self.current_slide = 1
            self.load_current_slide()
    
    def toggle_demo(self):
        """Startet oder stoppt die Demo"""
        colors = theme_manager.get_colors()
        
        if not self.demo_running:
            # Demo starten
            self.demo_running = True
            demo_service.start_demo(self.current_slide)
            
            self.demo_button.configure(
                text="⏹ Demo stoppen",
                bg=colors['accent_warning']
            )
            
            self.timer_label.configure(text="Demo läuft...")
            logger.info("Demo gestartet")
            
        else:
            # Demo stoppen
            self.demo_running = False
            demo_service.stop_demo()
            
            self.demo_button.configure(
                text="▶ Demo starten",
                bg=colors['accent_secondary']
            )
            
            self.timer_label.configure(text="Demo bereit")
            self.stop_autoplay()
            logger.info("Demo gestoppt")
    
    def toggle_autoplay(self):
        """Schaltet Auto-Play ein/aus"""
        colors = theme_manager.get_colors()
        
        if not self.auto_play:
            self.start_autoplay()
            self.autoplay_button.configure(
                text="⏸ Auto-Play",
                bg=colors['accent_primary']
            )
        else:
            self.stop_autoplay()
            self.autoplay_button.configure(
                text="🔄 Auto-Play",
                bg=colors['background_tertiary']
            )
    
    def start_autoplay(self):
        """Startet Auto-Play"""
        self.auto_play = True
        self.auto_play_thread = threading.Thread(target=self.autoplay_worker, daemon=True)
        self.auto_play_thread.start()
        logger.info("Auto-Play gestartet")
    
    def stop_autoplay(self):
        """Stoppt Auto-Play"""
        self.auto_play = False
        if self.auto_play_thread and self.auto_play_thread.is_alive():
            self.auto_play_thread.join(timeout=0.5)
        logger.info("Auto-Play gestoppt")
    
    def autoplay_worker(self):
        """Auto-Play Worker-Thread"""
        while self.auto_play:
            time.sleep(self.auto_play_interval)
            if self.auto_play:  # Nochmal prüfen nach sleep
                self.main_window.root.after(0, self.next_slide)
    
    def refresh_theme(self):
        """Aktualisiert das Theme für den Demo-Tab"""
        try:
            colors = theme_manager.get_colors()
            
            if hasattr(self, 'container'):
                self.container.configure(bg=colors['background_primary'])
            
            # Slides-Liste neu erstellen für Theme-Update
            self.create_slides_list()
            
            logger.debug("Demo-Tab Theme aktualisiert")
        except Exception as e:
            logger.error(f"Error refreshing demo theme: {e}")
    
    def show(self):
        """Zeigt den Demo-Tab"""
        if not self.visible:
            self.container.pack(fill='both', expand=True)
            self.visible = True
            
            # Aktuellen Slide laden
            self.load_current_slide()
            
            logger.debug("Demo-Tab angezeigt")
    
    def hide(self):
        """Versteckt den Demo-Tab"""
        if self.visible:
            # Demo stoppen falls läuft
            if self.demo_running:
                self.toggle_demo()
            
            self.container.pack_forget()
            self.visible = False
            logger.debug("Demo-Tab versteckt")
