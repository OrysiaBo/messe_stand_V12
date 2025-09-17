#!/usr/bin/env python3
"""
REPARIERTE Demo Tab - SOFORTIGE Synchronisation mit Creator
Kritische Änderungen für Live-Updates ohne Neustart
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer
from models.content import content_manager
from services.demo import demo_service

class DemoTab:
    """REPARIERTE Demo-Tab mit SOFORTIGER Synchronisation"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.visible = False
        self.current_slide = 1
        self.total_slides = 5
        self.auto_play = False
        self.auto_play_interval = 5
        self.auto_play_thread = None
        self.slide_buttons = {}
        self.last_update_time = 0
        self.last_content_hash = {}  # Für Change-Detection
        
        # KRITISCH: Demo-Service Integration
        self.demo_running = False
        self.sync_timer_id = None
        
        self.create_demo_content()
        
        # WICHTIG: Content-Observer SOFORT registrieren
        content_manager.add_observer(self.on_content_changed)
        
        # KRITISCH: Sync-Timer für Live-Updates starten
        self.start_sync_timer()
        
        logger.info("Demo Tab with IMMEDIATE synchronization initialized")
        
    def start_sync_timer(self):
        """Startet Timer für kontinuierliche Synchronisation"""
        self.sync_content()
        self.sync_timer_id = self.main_window.root.after(2000, self.start_sync_timer)
    
    def on_content_changed(self, slide_id, slide_data, action='update'):
        """REPARIERT: Sofortige Content-Änderungs-Behandlung"""
        try:
            logger.info(f"🔄 Demo: Content-Änderung erkannt für Slide {slide_id} (Aktion: {action})")
            
            current_time = time.time()
            if current_time - self.last_update_time < 0.5:  # Throttling reduziert
                return
            
            if action in ['update', 'load', 'asset_added']:
                # SOFORT: Slides-Liste aktualisieren
                self.update_slide_button(slide_id, slide_data)
                
                # SOFORT: Aktuellen Slide neu rendern falls betroffen
                if slide_id == self.current_slide:
                    logger.info(f"🔄 Demo: Rendering aktuellen Slide {slide_id} neu")
                    self.main_window.root.after(100, self.render_current_slide)
                
                self.last_update_time = current_time
                
            elif action == 'delete':
                self.handle_slide_deletion(slide_id)
                
            # UI-Status aktualisieren
            self.update_slide_info()
            
        except Exception as e:
            logger.error(f"Fehler bei Content-Änderung in Demo: {e}")
    
    def sync_content(self):
        """Synchronisiert Content ohne Observer (Fallback)"""
        try:
            # Alle Slides prüfen auf Änderungen
            all_slides = content_manager.get_all_slides()
            
            for slide_id, slide in all_slides.items():
                # Hash für Change-Detection
                content_hash = hash(f"{slide.title}_{slide.content}_{len(slide.canvas_elements)}")
                
                if slide_id not in self.last_content_hash or self.last_content_hash[slide_id] != content_hash:
                    # Slide hat sich geändert
                    self.last_content_hash[slide_id] = content_hash
                    
                    # Button aktualisieren
                    self.update_slide_button(slide_id, slide)
                    
                    # Aktuellen Slide neu rendern falls betroffen
                    if slide_id == self.current_slide:
                        self.main_window.root.after(50, self.render_current_slide)
            
            # Slide-Anzahl aktualisieren
            self.total_slides = len(all_slides)
            self.update_slide_info()
            
        except Exception as e:
            logger.debug(f"Sync-Content Fehler (nicht kritisch): {e}")
    
    def update_slide_button(self, slide_id, slide_data):
        """REPARIERT: Aktualisiert spezifischen Slide-Button"""
        try:
            if slide_id in self.slide_buttons:
                button = self.slide_buttons[slide_id]
                title = slide_data.title if hasattr(slide_data, 'title') else f"Slide {slide_id}"
                display_title = title[:18] + "..." if len(title) > 18 else title
                
                # Button-Text aktualisieren
                button.configure(text=f"{slide_id}\n{display_title}")
                
                logger.debug(f"✅ Slide-Button {slide_id} aktualisiert: '{title}'")
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren von Slide-Button {slide_id}: {e}")
    
    def handle_slide_deletion(self, slide_id):
        """Behandelt Slide-Löschung"""
        if slide_id == self.current_slide and self.current_slide > 1:
            self.current_slide -= 1
            self.load_current_slide()
        
        self.create_slides_list()  # Vollständige Neuerststellung
    
    def create_demo_content(self):
        """Erstellt Demo-Interface"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Haupt-Container
        self.container = tk.Frame(self.parent, bg=colors['background_primary'])
        
        # Header
        self.create_demo_header()
        
        # 2-Spalten Layout
        content_frame = tk.Frame(self.container, bg=colors['background_primary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=300)  # Navigation
        content_frame.grid_columnconfigure(1, weight=1, minsize=900)  # Display
        
        # Spalte 1: Navigation
        self.create_slide_navigation(content_frame)
        
        # Spalte 2: Display
        self.create_slide_display(content_frame)
        
        # Footer
        self.create_demo_footer()
    
    def create_demo_header(self):
        """Erstellt Demo-Header"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        header = tk.Frame(self.container, bg=colors['background_secondary'], height=80)
        header.pack(fill='x', padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        # Titel
        title_frame = tk.Frame(header, bg=colors['background_secondary'])
        title_frame.pack(side='left', fill='y', padx=(15, 30))
        
        tk.Label(title_frame, text="🎯 Live Demo", font=fonts['title'],
                fg=colors['accent_primary'], bg=colors['background_secondary']).pack(anchor='w', pady=(15, 0))
        
        tk.Label(title_frame, text="Live-Synchronisation mit Creator", font=fonts['caption'],
                fg=colors['text_secondary'], bg=colors['background_secondary']).pack(anchor='w')
        
        # Demo-Steuerung
        controls = tk.Frame(header, bg=colors['background_secondary'])
        controls.pack(side='left', fill='y', padx=20)
        
        # Start/Stop Demo
        self.demo_button = tk.Button(
            controls, text="▶ Demo starten", font=fonts['button'],
            bg=colors['accent_secondary'], fg='white', relief='flat', bd=0,
            padx=20, pady=10, cursor='hand2', command=self.toggle_demo
        )
        self.demo_button.pack(side='left', padx=(0, 10), pady=15)
        
        # Refresh-Button (manuell)
        refresh_btn = tk.Button(
            controls, text="🔄 Aktualisieren", font=fonts['button'],
            bg=colors['accent_primary'], fg='white', relief='flat', bd=0,
            padx=15, pady=10, cursor='hand2', command=self.force_refresh
        )
        refresh_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Slide-Info
        info_frame = tk.Frame(header, bg=colors['background_secondary'])
        info_frame.pack(side='right', fill='y', padx=(20, 15))
        
        self.slide_info_label = tk.Label(
            info_frame, text=f"Slide {self.current_slide} von {self.total_slides}",
            font=fonts['subtitle'], fg=colors['text_primary'], bg=colors['background_secondary']
        )
        self.slide_info_label.pack(pady=(20, 5))
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            info_frame, variable=self.progress_var, maximum=100, length=150, mode='determinate'
        )
        self.progress_bar.pack()
    
    def create_slide_navigation(self, parent):
        """Erstellt Slide-Navigation"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        nav_frame = tk.Frame(parent, bg=colors['background_secondary'], relief='solid', bd=1)
        nav_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        nav_frame.grid_propagate(False)
        
        # Header
        nav_header = tk.Frame(nav_frame, bg=colors['background_secondary'])
        nav_header.pack(fill='x', padx=15, pady=(15, 10))
        
        tk.Label(nav_header, text="📑 Folien-Übersicht", font=fonts['title'],
                fg=colors['text_primary'], bg=colors['background_secondary']).pack(anchor='w')
        
        # Navigation Buttons
        nav_buttons = tk.Frame(nav_header, bg=colors['background_secondary'])
        nav_buttons.pack(fill='x', pady=(10, 0))
        
        tk.Button(nav_buttons, text="◀", font=fonts['button'], bg=colors['accent_primary'],
                 fg='white', relief='flat', bd=0, width=3, pady=5, cursor='hand2',
                 command=self.previous_slide).pack(side='left', padx=(0, 5))
        
        tk.Button(nav_buttons, text="▶", font=fonts['button'], bg=colors['accent_primary'],
                 fg='white', relief='flat', bd=0, width=3, pady=5, cursor='hand2',
                 command=self.next_slide).pack(side='left', padx=(5, 0))
        
        # Scrollable Slides List
        list_frame = tk.Frame(nav_frame, bg=colors['background_secondary'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(10, 15))
        
        canvas = tk.Canvas(list_frame, bg=colors['background_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.slides_frame = tk.Frame(canvas, bg=colors['background_secondary'])
        
        self.slides_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.slides_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Slides erstellen
        self.create_slides_list()
    
    def create_slides_list(self):
        """REPARIERT: Erstellt Slides-Liste mit Live-Daten"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Alte Buttons löschen
        for widget in self.slides_frame.winfo_children():
            widget.destroy()
        self.slide_buttons.clear()
        
        try:
            # DIREKTE Daten von content_manager holen
            slides = content_manager.get_all_slides()
            
            if not slides:
                tk.Label(self.slides_frame, text="Keine Slides gefunden",
                        bg=colors['background_secondary'], fg=colors['text_secondary']).pack()
                return
            
            # Neue Buttons erstellen
            for slide_id, slide in sorted(slides.items()):
                slide_container = tk.Frame(self.slides_frame, bg=colors['background_secondary'])
                slide_container.pack(fill='x', pady=2)
                
                # Button Style
                is_active = slide_id == self.current_slide
                bg_color = colors['accent_primary'] if is_active else colors['background_tertiary']
                
                title = slide.title if hasattr(slide, 'title') else f"Slide {slide_id}"
                display_title = title[:18] + "..." if len(title) > 18 else title
                
                slide_btn = tk.Button(
                    slide_container, text=f"{slide_id}\n{display_title}",
                    font=fonts['body'], bg=bg_color,
                    fg='white' if is_active else colors['text_primary'],
                    relief='flat', bd=0, width=25, height=3, cursor='hand2',
                    command=lambda sid=slide_id: self.goto_slide(sid),
                    justify='left', anchor='w'
                )
                slide_btn.pack(fill='x', ipady=3)
                
                self.slide_buttons[slide_id] = slide_btn
            
            self.total_slides = len(slides)
            logger.debug(f"✅ {len(slides)} Slides in Demo-Liste erstellt")
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Slides-Liste: {e}")
            tk.Label(self.slides_frame, text="Fehler beim Laden",
                    bg=colors['background_secondary'], fg=colors['text_secondary']).pack()
    
    def create_slide_display(self, parent):
        """Erstellt Slide-Display"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        display = tk.Frame(parent, bg=colors['background_secondary'], relief='solid', bd=1)
        display.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Header
        display_header = tk.Frame(display, bg=colors['background_secondary'])
        display_header.pack(fill='x', padx=20, pady=(15, 10))
        
        self.current_slide_label = tk.Label(
            display_header, text="Demo-Folie wird geladen...", font=fonts['display'],
            fg=colors['text_primary'], bg=colors['background_secondary']
        )
        self.current_slide_label.pack(anchor='w')
        
        # Canvas für Slides
        canvas_frame = tk.Frame(display, bg=colors['background_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(10, 10))
        
        self.slide_canvas = tk.Canvas(canvas_frame, bg='#FFFFFF', relief='flat', bd=2, highlightthickness=0)
        self.slide_canvas.pack(fill='both', expand=True)
        self.slide_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Initiale Slide laden
        self.slide_canvas.after(100, self.load_current_slide)
    
    def create_demo_footer(self):
        """Erstellt Demo-Footer"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        footer = tk.Frame(self.container, bg=colors['background_secondary'], height=50)
        footer.pack(fill='x', padx=10, pady=5)
        footer.pack_propagate(False)
        
        # Status
        self.timer_label = tk.Label(footer, text="Demo bereit - Live-Sync aktiv",
                                   font=fonts['caption'], fg=colors['text_secondary'],
                                   bg=colors['background_secondary'])
        self.timer_label.pack(side='left', padx=15, pady=15)
        
        # Sync-Status
        self.sync_status = tk.Label(footer, text="🔄 Synchronisiert", font=fonts['caption'],
                                   fg=colors['accent_success'], bg=colors['background_secondary'])
        self.sync_status.pack(side='right', padx=15, pady=15)
    
    def load_current_slide(self):
        """REPARIERT: Lädt aktuellen Slide mit Live-Daten"""
        try:
            # DIREKT von content_manager laden
            slide = content_manager.get_slide(self.current_slide)
            
            if slide:
                # Titel aktualisieren
                self.current_slide_label.configure(
                    text=f"Demo-Folie {self.current_slide}: {slide.title}"
                )
                
                # Slide rendern
                self.render_current_slide()
                
                # Navigation aktualisieren
                self.update_slide_navigation()
                self.update_slide_info()
                
                logger.debug(f"✅ Slide {self.current_slide} geladen: {slide.title}")
            else:
                logger.warning(f"Slide {self.current_slide} nicht gefunden")
                self.current_slide_label.configure(
                    text=f"Slide {self.current_slide} nicht gefunden"
                )
                
        except Exception as e:
            logger.error(f"Fehler beim Laden von Slide {self.current_slide}: {e}")
    
    def render_current_slide(self):
        """REPARIERT: Rendert aktuellen Slide SOFORT"""
        try:
            # DIREKT von content_manager holen
            slide = content_manager.get_slide(self.current_slide)
            
            if not slide:
                logger.warning(f"Slide {self.current_slide} für Rendering nicht gefunden")
                return
            
            # Canvas-Größe
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
                
                # SOFORT rendern
                SlideRenderer.render_slide_to_canvas(
                    self.slide_canvas, slide_data, canvas_width, canvas_height
                )
                
                logger.debug(f"✅ Slide {self.current_slide} gerendert")
                
                # Sync-Status aktualisieren
                if hasattr(self, 'sync_status'):
                    self.sync_status.configure(text="✅ Aktualisiert", fg=theme_manager.get_colors()['accent_success'])
                    
        except Exception as e:
            logger.error(f"Fehler beim Rendern von Slide {self.current_slide}: {e}")
            if hasattr(self, 'sync_status'):
                self.sync_status.configure(text="❌ Renderfehler", fg=theme_manager.get_colors()['accent_warning'])
    
    def force_refresh(self):
        """KRITISCH: Erzwingt komplette Aktualisierung"""
        try:
            logger.info("🔄 Demo: Forced Refresh gestartet")
            
            # 1. Slides-Liste neu erstellen
            self.create_slides_list()
            
            # 2. Aktuellen Slide neu laden
            self.load_current_slide()
            
            # 3. UI aktualisieren
            self.update_slide_info()
            
            # 4. Status
            if hasattr(self, 'timer_label'):
                self.timer_label.configure(text="🔄 Manuell aktualisiert")
                self.main_window.root.after(3000, 
                    lambda: self.timer_label.configure(text="Demo bereit - Live-Sync aktiv"))
            
            logger.info("✅ Demo: Forced Refresh abgeschlossen")
            
        except Exception as e:
            logger.error(f"Fehler bei Forced Refresh: {e}")
    
    def update_slide_info(self):
        """Aktualisiert Slide-Information"""
        try:
            if hasattr(self, 'slide_info_label'):
                self.slide_info_label.configure(
                    text=f"Slide {self.current_slide} von {self.total_slides}"
                )
            
            if hasattr(self, 'progress_var') and self.total_slides > 0:
                progress = (self.current_slide / self.total_slides) * 100
                self.progress_var.set(progress)
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Slide-Info: {e}")
    
    def update_slide_navigation(self):
        """Aktualisiert Slide-Navigation"""
        colors = theme_manager.get_colors()
        
        for slide_id, button in self.slide_buttons.items():
            if slide_id == self.current_slide:
                button.configure(bg=colors['accent_primary'], fg='white')
            else:
                button.configure(bg=colors['background_tertiary'], fg=colors['text_primary'])
    
    def goto_slide(self, slide_id):
        """Springt zu Slide"""
        try:
            self.current_slide = slide_id
            self.load_current_slide()
            logger.info(f"Demo: Navigation zu Slide {slide_id}")
        except Exception as e:
            logger.error(f"Fehler bei Navigation zu Slide {slide_id}: {e}")
    
    def previous_slide(self):
        """Vorherige Slide"""
        if self.current_slide > 1:
            self.goto_slide(self.current_slide - 1)
    
    def next_slide(self):
        """Nächste Slide"""
        if self.current_slide < self.total_slides:
            self.goto_slide(self.current_slide + 1)
        elif self.auto_play:
            self.goto_slide(1)  # Loop
    
    def toggle_demo(self):
        """Startet/Stoppt Demo"""
        colors = theme_manager.get_colors()
        
        if not self.demo_running:
            # Demo starten
            self.demo_running = True
            demo_service.start_demo(self.current_slide)
            
            self.demo_button.configure(text="⏹ Demo stoppen", bg=colors['accent_warning'])
            self.timer_label.configure(text="Demo läuft...")
            logger.info("Demo gestartet")
            
        else:
            # Demo stoppen
            self.demo_running = False
            demo_service.stop_demo()
            
            self.demo_button.configure(text="▶ Demo starten", bg=colors['accent_secondary'])
            self.timer_label.configure(text="Demo bereit - Live-Sync aktiv")
            logger.info("Demo gestoppt")
    
    def on_canvas_resize(self, event):
        """Canvas Resize Handler"""
        self.main_window.root.after(100, self.render_current_slide)
    
    def show(self):
        """Zeigt Tab"""
        if not self.visible:
            self.container.pack(fill='both', expand=True)
            self.visible = True
            self.load_current_slide()
            logger.info("Demo Tab angezeigt")
    
    def hide(self):
        """Versteckt Tab"""
        if self.visible:
            if self.demo_running:
                self.toggle_demo()  # Demo stoppen
            
            if self.sync_timer_id:
                self.main_window.root.after_cancel(self.sync_timer_id)
            
            self.container.pack_forget()
            self.visible = False
            logger.info("Demo Tab versteckt")
    
    def __del__(self):
        """Cleanup bei Zerstörung"""
        try:
            if hasattr(self, 'sync_timer_id') and self.sync_timer_id:
                self.main_window.root.after_cancel(self.sync_timer_id)
        except:
            pass
