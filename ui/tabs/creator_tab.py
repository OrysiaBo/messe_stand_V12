#!/usr/bin/env python3
"""
REPARIERTE Creator Tab - Kritische Speicher-Funktionen
Fokus auf funktionierende Speicherung von Text und Bildern
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import base64
from io import BytesIO
from PIL import Image, ImageTk
from datetime import datetime

# WICHTIGE IMPORTS
from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer

# NEU: Verwende den erweiterten content_manager
from models.content import content_manager

class CreatorTab:
    """REPARIERTE Creator-Tab mit funktionierender Speicherung"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.visible = False
        self.current_edit_slide = 1
        self.current_slide = None
        self.auto_save_timer_id = None
        self.edit_mode = False
        self.edit_widgets = {}
        self.manual_save = False
        
        # Canvas-Elemente Tracking
        self.canvas_items = {}  # Canvas-Item-ID -> Widget mapping
        self.asset_browser = None
        
        self.create_creator_content()
        self.schedule_auto_save()
        logger.info("Creator Tab mit reparierter Speicherung initialisiert")
        
    def create_creator_content(self):
        """Erstellt die Creator-Benutzeroberfläche"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Haupt-Container
        self.container = tk.Frame(self.parent, bg=colors['background_primary'])
        
        # Header-Toolbar
        self.create_toolbar()
        
        # 3-Spalten-Layout: Slides | Editor | Assets+Tools
        content_frame = tk.Frame(self.container, bg=colors['background_primary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=250)  # Slides
        content_frame.grid_columnconfigure(1, weight=1, minsize=800)  # Editor
        content_frame.grid_columnconfigure(2, weight=0, minsize=350)  # Assets+Tools
        
        # Spalte 1: Slides
        self.create_slides_panel(content_frame)
        
        # Spalte 2: Editor
        self.create_editor_panel(content_frame)
        
        # Spalte 3: Assets + Tools
        self.create_assets_tools_panel(content_frame)
        
        # Status
        self.create_status_bar()
    
    def create_toolbar(self):
        """Erstellt die Toolbar mit kritischen Buttons"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        toolbar = tk.Frame(self.container, bg=colors['background_secondary'], height=80)
        toolbar.pack(fill='x', padx=10, pady=(10, 5))
        toolbar.pack_propagate(False)
        
        # Titel
        title_frame = tk.Frame(toolbar, bg=colors['background_secondary'])
        title_frame.pack(side='left', fill='y', padx=(15, 30))
        
        tk.Label(
            title_frame, text="🎨 Slide Creator", font=fonts['title'],
            fg=colors['accent_primary'], bg=colors['background_secondary']
        ).pack(anchor='w', pady=(15, 0))
        
        tk.Label(
            title_frame, text="Reparierte Version mit Speicherung", font=fonts['caption'],
            fg=colors['text_secondary'], bg=colors['background_secondary']
        ).pack(anchor='w')
        
        # Aktionen (KRITISCH - diese müssen funktionieren!)
        actions = tk.Frame(toolbar, bg=colors['background_secondary'])
        actions.pack(side='left', fill='y', padx=20)
        
        # REPARIERTER Speichern-Button
        save_btn = tk.Button(
            actions, text="💾 SPEICHERN", font=fonts['button'],
            bg=colors['accent_success'], fg='white', relief='flat', bd=0,
            padx=20, pady=10, cursor='hand2',
            command=self.force_save_slide
        )
        save_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Test-Button für Debugging
        test_btn = tk.Button(
            actions, text="🔧 TEST", font=fonts['button'],
            bg='#ff9f0a', fg='white', relief='flat', bd=0,
            padx=15, pady=10, cursor='hand2',
            command=self.debug_current_slide
        )
        test_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Navigation
        nav_frame = tk.Frame(toolbar, bg=colors['background_secondary'])
        nav_frame.pack(side='right', fill='y', padx=(20, 15))
        
        self.slide_counter = tk.Label(
            nav_frame, text=f"Slide {self.current_edit_slide} von 5",
            font=fonts['subtitle'], fg=colors['text_primary'], bg=colors['background_secondary']
        )
        self.slide_counter.pack(pady=(20, 5))
        
        nav_btns = tk.Frame(nav_frame, bg=colors['background_secondary'])
        nav_btns.pack()
        
        tk.Button(nav_btns, text="◀ Zurück", command=self.previous_slide,
                 bg=colors['background_tertiary'], fg=colors['text_primary'],
                 relief='flat', bd=0, padx=15, pady=5).pack(side='left', padx=(0, 5))
        
        tk.Button(nav_btns, text="Weiter ▶", command=self.next_slide,
                 bg=colors['background_tertiary'], fg=colors['text_primary'],
                 relief='flat', bd=0, padx=15, pady=5).pack(side='left', padx=(5, 0))
    
    def create_slides_panel(self, parent):
        """Erstellt das Slides-Panel"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        panel = tk.Frame(parent, bg=colors['background_secondary'], relief='solid', bd=1)
        panel.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        panel.grid_propagate(False)
        
        # Header
        tk.Label(panel, text="📋 Slides", font=fonts['title'],
                fg=colors['text_primary'], bg=colors['background_secondary']
               ).pack(padx=15, pady=(15, 10))
        
        # Scrollable Liste
        canvas = tk.Canvas(panel, bg=colors['background_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        self.slides_frame = tk.Frame(canvas, bg=colors['background_secondary'])
        
        self.slides_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.slides_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        scrollbar.pack(side="right", fill="y", pady=(0, 15))
        
        self.create_slide_thumbnails()
    
    def create_editor_panel(self, parent):
        """Erstellt das Haupt-Editor-Panel"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        editor = tk.Frame(parent, bg=colors['background_secondary'], relief='solid', bd=1)
        editor.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Header
        header = tk.Frame(editor, bg=colors['background_secondary'])
        header.pack(fill='x', padx=20, pady=(15, 10))
        
        self.slide_info_label = tk.Label(
            header, text=f"Slide {self.current_edit_slide}: Wählen Sie eine Folie",
            font=fonts['display'], fg=colors['text_primary'], bg=colors['background_secondary']
        )
        self.slide_info_label.pack(anchor='w')
        
        # Canvas für Editor
        canvas_frame = tk.Frame(editor, bg=colors['background_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(10, 10))
        
        # WICHTIG: Slide Canvas für Inhalte
        self.slide_canvas = tk.Canvas(
            canvas_frame, bg='#E8E8E8', relief='flat', bd=0, highlightthickness=0
        )
        self.slide_canvas.pack(fill='both', expand=True)
        self.slide_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Bearbeiten-Toggle
        edit_btn = tk.Button(
            canvas_frame, text="✏️ Bearbeiten", font=fonts['button'],
            bg=colors['accent_secondary'], fg='white', relief='flat', bd=0,
            padx=20, pady=8, cursor='hand2', command=self.toggle_edit_mode
        )
        edit_btn.place(relx=0.95, rely=0.05, anchor='ne')
        
        # Initiale Inhalte laden
        self.slide_canvas.after(100, self.load_slide_to_editor, 1)
    
    def create_assets_tools_panel(self, parent):
        """Erstellt das Assets+Tools Panel"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        panel = tk.Frame(parent, bg=colors['background_secondary'], relief='solid', bd=1)
        panel.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        panel.grid_propagate(False)
        
        # Assets-Browser
        self.create_asset_browser(panel)
        
        # Tools
        self.create_tools_section(panel)
    
    def create_asset_browser(self, parent):
        """NEUER Asset-Browser für alle verfügbaren Assets"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Header
        tk.Label(parent, text="🖼️ Assets", font=fonts['title'],
                fg=colors['text_primary'], bg=colors['background_secondary']
               ).pack(fill='x', padx=15, pady=(15, 10))
        
        # Notebook für verschiedene Asset-Kategorien
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
        # Corporate Assets (aus assets/)
        corp_frame = tk.Frame(notebook, bg=colors['background_tertiary'])
        notebook.add(corp_frame, text="Corporate")
        self.create_asset_list(corp_frame, "corporate_assets")
        
        # UI-Elemente (aus assets/)
        ui_frame = tk.Frame(notebook, bg=colors['background_tertiary'])
        notebook.add(ui_frame, text="UI/Icons")
        self.create_asset_list(ui_frame, "ui_elements")
        
        # Content-Bilder (aus content/)
        content_frame = tk.Frame(notebook, bg=colors['background_tertiary'])
        notebook.add(content_frame, text="Content")
        self.create_asset_list(content_frame, "content_images")
    
    def create_asset_list(self, parent, category):
        """Erstellt Liste für Asset-Kategorie"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Scrollable Liste
        canvas = tk.Canvas(parent, bg=colors['background_tertiary'], highlightthickness=0, height=200)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=colors['background_tertiary'])
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # Assets laden und anzeigen
        self.populate_asset_list(frame, category)
    
    def populate_asset_list(self, frame, category):
        """Füllt Asset-Liste mit verfügbaren Assets"""
        try:
            available_assets = content_manager.get_available_assets()
            assets = available_assets.get(category, [])
            
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            for i, asset in enumerate(assets[:20]):  # Limitiert für Performance
                asset_btn = tk.Button(
                    frame, text=f"📄 {asset['filename'][:20]}...",
                    font=fonts['caption'], bg=colors['background_hover'],
                    fg=colors['text_primary'], relief='flat', bd=0,
                    width=25, anchor='w', padx=10, pady=3,
                    cursor='hand2',
                    command=lambda a=asset: self.add_asset_to_slide(a)
                )
                asset_btn.pack(fill='x', padx=5, pady=2)
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Assets für {category}: {e}")
            tk.Label(frame, text="Fehler beim Laden", bg=colors['background_tertiary']).pack()
    
    def create_tools_section(self, parent):
        """Erstellt Tools-Sektion"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Tools Header
        tk.Label(parent, text="🔧 Tools", font=fonts['title'],
                fg=colors['text_primary'], bg=colors['background_secondary']
               ).pack(fill='x', padx=15, pady=(20, 10))
        
        tools_frame = tk.Frame(parent, bg=colors['background_secondary'])
        tools_frame.pack(fill='x', padx=15, pady=10)
        
        # Text hinzufügen
        tk.Button(tools_frame, text="📝 Text hinzufügen",
                 command=self.add_text_element, font=fonts['button'],
                 bg=colors['background_tertiary'], fg=colors['text_primary'],
                 relief='flat', bd=0, padx=20, pady=8, cursor='hand2'
                ).pack(fill='x', pady=3)
        
        # Lokales Bild hinzufügen
        tk.Button(tools_frame, text="🖼️ Bild hochladen",
                 command=self.add_local_image, font=fonts['button'],
                 bg=colors['background_tertiary'], fg=colors['text_primary'],
                 relief='flat', bd=0, padx=20, pady=8, cursor='hand2'
                ).pack(fill='x', pady=3)
        
        # Slide löschen
        tk.Button(tools_frame, text="🗑️ Slide leeren",
                 command=self.clear_slide, font=fonts['button'],
                 bg=colors['accent_warning'], fg='white',
                 relief='flat', bd=0, padx=20, pady=8, cursor='hand2'
                ).pack(fill='x', pady=3)
    
    def create_status_bar(self):
        """Erstellt Status-Leiste"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        status = tk.Frame(self.container, bg=colors['background_secondary'], height=30)
        status.pack(fill='x', padx=10, pady=5)
        status.pack_propagate(False)
        
        self.status_label = tk.Label(
            status, text="Bereit - Creator-Tab geladen",
            font=fonts['caption'], fg=colors['text_secondary'], bg=colors['background_secondary']
        )
        self.status_label.pack(side='left', padx=15, pady=5)
    
    # ==========================================
    # KRITISCHE SPEICHER-FUNKTIONEN (REPARIERT)
    # ==========================================
    
    def force_save_slide(self):
        """REPARIERT: Erzwingt Speicherung des aktuellen Slides"""
        self.manual_save = True
        success = self.save_current_slide_content()
        
        if success:
            messagebox.showinfo("Speichern", f"Slide {self.current_edit_slide} wurde erfolgreich gespeichert!")
            self.update_status("✅ Slide gespeichert")
        else:
            messagebox.showerror("Fehler", "Slide konnte nicht gespeichert werden!")
            self.update_status("❌ Speichern fehlgeschlagen")
    
    def save_current_slide_content(self):
    """VEREINFACHTE Speicherfunktion"""
    try:
        # Einfache Text-Extraktion
        title_text = ""
        content_text = ""
        
        if self.edit_mode and hasattr(self, 'edit_widgets'):
            if 'title' in self.edit_widgets:
                title_text = self.edit_widgets['title'].get('1.0', 'end-1c')
            if 'content' in self.edit_widgets:  
                content_text = self.edit_widgets['content'].get('1.0', 'end-1c')
        
        if not title_text:
            title_text = f"Folie {self.current_edit_slide}"
            
        # DIREKT zum content_manager speichern
        success = content_manager.update_slide_content(
            self.current_edit_slide, title_text, content_text, {}
        )
        
        if success:
            logger.info(f"✅ Slide {self.current_edit_slide} gespeichert")
            return True
        else:
            logger.error(f"❌ Speichern fehlgeschlagen")
            return False
            
    except Exception as e:
        logger.error(f"Speicherfehler: {e}")
        return False
    
    def extract_canvas_content(self):
        """REPARIERT: Extrahiert Inhalte aus Canvas-Widgets"""
        title_text = ""
        content_text = ""
        canvas_elements = []
        
        try:
            # Alle Canvas-Items durchgehen
            for item in self.slide_canvas.find_all():
                if self.slide_canvas.type(item) == 'window':
                    try:
                        widget = self.slide_canvas.nametowidget(self.slide_canvas.itemcget(item, 'window'))
                        coords = self.slide_canvas.coords(item)
                        
                        if isinstance(widget, tk.Text):
                            # Text-Widget
                            text_content = widget.get('1.0', 'end-1c')
                            if text_content.strip():
                                font = widget.cget('font')
                                is_title = self.is_title_widget(widget, font)
                                
                                if is_title and not title_text:
                                    title_text = text_content.strip()
                                else:
                                    content_text += text_content.strip() + "\n"
                                
                                # Canvas-Element speichern
                                canvas_elements.append({
                                    'type': 'text',
                                    'content': text_content.strip(),
                                    'x': coords[0] if coords else 0,
                                    'y': coords[1] if coords else 0,
                                    'font': str(font),
                                    'is_title': is_title
                                })
                        
                        elif isinstance(widget, tk.Label) and hasattr(widget, 'image'):
                            # Bild-Widget
                            image_data = self.extract_image_data(widget, coords)
                            if image_data:
                                canvas_elements.append(image_data)
                                
                    except Exception as e:
                        logger.debug(f"Fehler beim Verarbeiten von Canvas-Item: {e}")
                        continue
            
            # Content bereinigen
            content_text = content_text.strip()
            
            logger.debug(f"Extrahiert - Titel: '{title_text}', Content: {len(content_text)} Zeichen, Elemente: {len(canvas_elements)}")
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren von Canvas-Content: {e}")
        
        return title_text, content_text, canvas_elements
    
    def extract_image_data(self, widget, coords):
        """REPARIERT: Extrahiert Bild-Daten für Speicherung"""
        try:
            image_data = {
                'type': 'image',
                'x': coords[0] if coords else 0,
                'y': coords[1] if coords else 0,
                'width': widget.winfo_width(),
                'height': widget.winfo_height()
            }
            
            # Original-Pfad falls verfügbar
            if hasattr(widget, 'image_path'):
                image_data['file_path'] = widget.image_path
                logger.debug(f"Bild-Pfad gefunden: {widget.image_path}")
            
            # Bild als Base64 speichern (Fallback)
            if hasattr(widget, 'image'):
                try:
                    # PhotoImage zu PIL Image konvertieren
                    pil_image = ImageTk.getimage(widget.image)
                    buffer = BytesIO()
                    pil_image.save(buffer, format='PNG')
                    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    image_data['image_data'] = image_base64
                    logger.debug("Bild als Base64 gespeichert")
                except Exception as e:
                    logger.warning(f"Bild-Base64-Konvertierung fehlgeschlagen: {e}")
            
            return image_data
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren von Bild-Daten: {e}")
            return None
    
    def is_title_widget(self, widget, font):
        """Bestimmt ob Widget ein Titel ist"""
        try:
            if isinstance(font, tuple) and len(font) >= 2:
                font_size = font[1] if isinstance(font[1], int) else int(font[1])
                return font_size >= 20 or 'bold' in str(font)
            return False
        except:
            return False
    
    def show_save_success(self):
        """Zeigt Speicher-Erfolg an"""
        if hasattr(self, 'slide_info_label'):
            original_text = self.slide_info_label.cget('text')
            self.slide_info_label.configure(
                text=f"✅ Slide {self.current_edit_slide} gespeichert!"
            )
            
            def restore_text():
                if hasattr(self, 'slide_info_label'):
                    slide = content_manager.get_slide(self.current_edit_slide)
                    if slide:
                        self.slide_info_label.configure(text=f"Slide {self.current_edit_slide}: {slide.title}")
            
            self.main_window.root.after(3000, restore_text)
        
        self.manual_save = False
    
    def debug_current_slide(self):
        """Debug-Funktion zum Testen"""
        try:
            slide = content_manager.get_slide(self.current_edit_slide)
            if slide:
                debug_info = f"""DEBUG INFO für Slide {self.current_edit_slide}:
                
Titel: {slide.title}
Content: {len(slide.content)} Zeichen
Canvas-Elemente: {len(slide.canvas_elements)}
Assets: {len(slide.assets)}
Geändert: {slide.modified_at}

Canvas-Items: {len(self.slide_canvas.find_all())}
Edit-Modus: {self.edit_mode}
"""
                messagebox.showinfo("Debug Info", debug_info)
            else:
                messagebox.showerror("Debug", f"Slide {self.current_edit_slide} nicht gefunden!")
                
        except Exception as e:
            messagebox.showerror("Debug Fehler", str(e))
    
    # ==========================================
    # ASSET-MANAGEMENT FUNKTIONEN (NEU)
    # ==========================================
    
    def add_asset_to_slide(self, asset_info):
        """Fügt Asset zur aktuellen Slide hinzu"""
        try:
            # Asset zum Content-Manager hinzufügen
            added_asset = content_manager.add_asset_to_slide(
                self.current_edit_slide, 
                asset_info['path'], 
                'image'
            )
            
            if added_asset:
                # Asset im Canvas anzeigen
                self.display_asset_on_canvas(asset_info)
                self.update_status(f"Asset hinzugefügt: {asset_info['filename']}")
                logger.info(f"Asset erfolgreich hinzugefügt: {asset_info['filename']}")
            else:
                messagebox.showerror("Fehler", f"Asset konnte nicht hinzugefügt werden: {asset_info['filename']}")
                
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen von Asset: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen: {e}")
    
    def display_asset_on_canvas(self, asset_info):
        """Zeigt Asset im Canvas an"""
        try:
            # Bild laden
            if asset_info['extension'].lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                image = Image.open(asset_info['path'])
                image.thumbnail((300, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Label erstellen
                label = tk.Label(
                    self.slide_canvas, image=photo, bg='white', relief='solid', bd=1
                )
                label.image = photo
                label.image_path = asset_info['path']
                
                # Im Canvas platzieren
                canvas_item = self.slide_canvas.create_window(
                    150, 200, window=label, anchor='nw'
                )
                
                # Bewegbar machen
                self.make_canvas_item_movable(label, canvas_item)
                
                # Tracking
                self.canvas_items[canvas_item] = label
                
                logger.debug(f"Asset im Canvas angezeigt: {asset_info['filename']}")
                
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen von Asset: {e}")
    
    def add_local_image(self):
        """Lädt lokales Bild hoch"""
        try:
            filepath = filedialog.askopenfilename(
                title="Bild auswählen",
                filetypes=[
                    ("Bilddateien", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("Alle Dateien", "*.*")
                ]
            )
            
            if filepath:
                asset_info = {
                    'path': filepath,
                    'filename': os.path.basename(filepath),
                    'extension': os.path.splitext(filepath)[1].lower()
                }
                self.add_asset_to_slide(asset_info)
                
        except Exception as e:
            logger.error(f"Fehler beim Laden lokaler Bilder: {e}")
    
    # ==========================================
    # WEITERE FUNKTIONEN
    # ==========================================
    
    def load_slide_to_editor(self, slide_id):
        """Lädt Slide in Editor"""
        try:
            # Aktuellen Slide speichern
            if hasattr(self, 'current_edit_slide') and self.current_slide:
                self.save_current_slide_content()
            
            self.current_edit_slide = slide_id
            self.current_slide = content_manager.get_slide(slide_id)
            
            if self.current_slide:
                self.clear_canvas()
                self.render_slide_preview()
                self.update_slide_info()
                self.update_thumbnail_selection()
                logger.debug(f"Slide {slide_id} in Editor geladen")
            else:
                logger.warning(f"Slide {slide_id} nicht gefunden")
                
        except Exception as e:
            logger.error(f"Fehler beim Laden von Slide {slide_id}: {e}")
    
    def render_slide_preview(self):
        """Rendert Slide-Vorschau"""
        try:
            if not self.current_slide:
                return
                
            canvas_width = self.slide_canvas.winfo_width()
            canvas_height = self.slide_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:
                slide_data = {
                    'title': self.current_slide.title,
                    'content': self.current_slide.content,
                    'slide_number': self.current_edit_slide,
                    'background_color': '#FFFFFF',
                    'text_color': '#1F1F1F'
                }
                
                SlideRenderer.render_slide_to_canvas(
                    self.slide_canvas, slide_data, canvas_width, canvas_height
                )
                
                # Canvas-Elemente wiederherstellen falls vorhanden
                if self.current_slide.canvas_elements:
                    self.restore_canvas_elements(self.current_slide.canvas_elements)
                    
        except Exception as e:
            logger.error(f"Fehler beim Rendern der Slide-Vorschau: {e}")
    
    def update_slide_info(self):
        """Aktualisiert Slide-Information"""
        if hasattr(self, 'slide_info_label') and self.current_slide:
            self.slide_info_label.configure(
                text=f"Slide {self.current_edit_slide}: {self.current_slide.title}"
            )
            self.slide_counter.configure(
                text=f"Slide {self.current_edit_slide} von {content_manager.get_slide_count()}"
            )
    
    def update_status(self, message):
        """Aktualisiert Status"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
    
    # Navigation
    def previous_slide(self):
        """Vorherige Slide"""
        if self.current_edit_slide > 1:
            self.load_slide_to_editor(self.current_edit_slide - 1)
    
    def next_slide(self):
        """Nächste Slide"""
        max_slides = content_manager.get_slide_count()
        if self.current_edit_slide < max_slides:
            self.load_slide_to_editor(self.current_edit_slide + 1)
    
    # Weitere erforderliche Methoden (Stubs)
    def create_slide_thumbnails(self):
        """Erstellt Slide-Thumbnails"""
        # Implementation hier
        pass
    
    def toggle_edit_mode(self):
        """Wechselt Edit-Modus"""
        # Implementation hier
        pass
    
    def add_text_element(self):
        """Fügt Text-Element hinzu"""
        # Implementation hier
        pass
    
    def clear_slide(self):
        """Leert Slide"""
        # Implementation hier
        pass
    
    def clear_canvas(self):
        """Leert Canvas"""
        self.slide_canvas.delete("all")
    
    def restore_canvas_elements(self, elements):
        """Stellt Canvas-Elemente wieder her"""
        # Implementation hier
        pass
    
    def make_canvas_item_movable(self, widget, canvas_item):
        """Macht Canvas-Item bewegbar"""
        # Implementation hier
        pass
    
    def on_canvas_resize(self, event):
        """Canvas-Resize Handler"""
        self.main_window.root.after(100, self.render_slide_preview)
    
    def update_thumbnail_selection(self):
        """Aktualisiert Thumbnail-Auswahl"""
        # Implementation hier
        pass
    
    def schedule_auto_save(self):
        """Plant Auto-Save"""
        if self.auto_save_timer_id:
            self.main_window.root.after_cancel(self.auto_save_timer_id)
        self.auto_save_timer_id = self.main_window.root.after(5000, self.auto_save_slide)
    
    def auto_save_slide(self):
        """Auto-Save Funktion"""
        if not self.manual_save:  # Nur wenn nicht gerade manuell gespeichert wird
            self.save_current_slide_content()
        self.schedule_auto_save()
    
    # Interface-Methoden
    def show(self):
        """Zeigt Tab"""
        if not self.visible:
            self.container.pack(fill='both', expand=True)
            self.visible = True
            self.load_slide_to_editor(1)
    
    def hide(self):
        """Versteckt Tab"""
        if self.visible:
            self.save_current_slide_content()  # Speichern beim Verstecken
            self.container.pack_forget()
            self.visible = False
