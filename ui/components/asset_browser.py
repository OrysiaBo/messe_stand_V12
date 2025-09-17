#!/usr/bin/env python3
"""
Asset Browser Component für Dynamic Messe Stand V4
Vollständiger Asset-Browser für alle Ordner mit Vorschau
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk
from core.theme import theme_manager
from core.logger import logger
from models.content import content_manager

class AssetBrowserWidget:
    """Widget für Asset-Browsing mit Vorschau und Integration"""
    
    def __init__(self, parent, on_asset_selected_callback):
        self.parent = parent
        self.on_asset_selected = on_asset_selected_callback
        self.current_category = "corporate_assets"
        self.assets_cache = {}
        self.preview_cache = {}
        
        self.setup_ui()
        self.load_assets()
        
    def setup_ui(self):
        """Erstellt die Asset-Browser UI"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        # Hauptcontainer
        self.container = tk.Frame(self.parent, bg=colors['background_secondary'])
        
        # Header
        header = tk.Frame(self.container, bg=colors['background_secondary'])
        header.pack(fill='x', padx=10, pady=(10, 5))
        
        tk.Label(
            header, text="🗂️ Asset Browser", 
            font=fonts['title'], fg=colors['text_primary'], 
            bg=colors['background_secondary']
        ).pack(anchor='w')
        
        tk.Label(
            header, text="Alle verfügbaren Assets", 
            font=fonts['caption'], fg=colors['text_secondary'], 
            bg=colors['background_secondary']
        ).pack(anchor='w')
        
        # Kategorie-Tabs
        self.create_category_tabs()
        
        # Asset-Liste mit Vorschau
        self.create_asset_list()
        
        # Aktions-Buttons
        self.create_action_buttons()
    
    def create_category_tabs(self):
        """Erstellt Kategorie-Tabs"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        tabs_frame = tk.Frame(self.container, bg=colors['background_secondary'])
        tabs_frame.pack(fill='x', padx=10, pady=5)
        
        # Tab-Buttons
        self.tab_buttons = {}
        categories = [
            ("Corporate", "corporate_assets", "🏢"),
            ("UI/Icons", "ui_elements", "🎨"),
            ("Content", "content_images", "📷"),
            ("Uploads", "user_uploads", "📤")
        ]
        
        for i, (label, category, icon) in enumerate(categories):
            is_active = category == self.current_category
            bg = colors['accent_primary'] if is_active else colors['background_tertiary']
            fg = 'white' if is_active else colors['text_primary']
            
            btn = tk.Button(
                tabs_frame, text=f"{icon} {label}",
                font=fonts['button'], bg=bg, fg=fg,
                relief='flat', bd=0, padx=15, pady=8,
                cursor='hand2',
                command=lambda cat=category: self.switch_category(cat)
            )
            btn.pack(side='left', padx=2)
            self.tab_buttons[category] = btn
    
    def create_asset_list(self):
        """Erstellt scrollbare Asset-Liste mit Vorschau"""
        colors = theme_manager.get_colors()
        
        # List-Container
        list_container = tk.Frame(self.container, bg=colors['background_secondary'])
        list_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Canvas für Scrolling
        self.list_canvas = tk.Canvas(
            list_container, bg=colors['background_tertiary'], 
            highlightthickness=0, height=300
        )
        
        scrollbar = tk.Scrollbar(
            list_container, orient="vertical", 
            command=self.list_canvas.yview
        )
        
        self.asset_frame = tk.Frame(
            self.list_canvas, bg=colors['background_tertiary']
        )
        
        # Scrolling konfigurieren
        self.asset_frame.bind(
            "<Configure>", 
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )
        
        self.list_canvas.create_window((0, 0), window=self.asset_frame, anchor="nw")
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        self.list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel binding
        self.list_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.asset_frame.bind("<MouseWheel>", self.on_mouse_wheel)
    
    def create_action_buttons(self):
        """Erstellt Aktions-Buttons"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        actions = tk.Frame(self.container, bg=colors['background_secondary'])
        actions.pack(fill='x', padx=10, pady=(5, 10))
        
        # Aktualisieren-Button
        refresh_btn = tk.Button(
            actions, text="🔄 Aktualisieren",
            font=fonts['button'], bg=colors['accent_secondary'], fg='white',
            relief='flat', bd=0, padx=15, pady=8, cursor='hand2',
            command=self.refresh_assets
        )
        refresh_btn.pack(side='left', padx=(0, 10))
        
        # Upload-Button
        upload_btn = tk.Button(
            actions, text="📤 Hochladen",
            font=fonts['button'], bg=colors['accent_primary'], fg='white',
            relief='flat', bd=0, padx=15, pady=8, cursor='hand2',
            command=self.upload_asset
        )
        upload_btn.pack(side='left')
    
    def load_assets(self):
        """Lädt alle Assets"""
        try:
            self.assets_cache = content_manager.get_available_assets()
            self.populate_current_category()
            logger.debug(f"Assets geladen: {sum(len(v) for v in self.assets_cache.values())} gesamt")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Assets: {e}")
            self.show_error_message("Fehler beim Laden der Assets")
    
    def populate_current_category(self):
        """Füllt aktuelle Kategorie mit Assets"""
        # Alte Widgets entfernen
        for widget in self.asset_frame.winfo_children():
            widget.destroy()
        
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        assets = self.assets_cache.get(self.current_category, [])
        
        if not assets:
            tk.Label(
                self.asset_frame, text="Keine Assets in dieser Kategorie",
                font=fonts['body'], bg=colors['background_tertiary'],
                fg=colors['text_secondary']
            ).pack(pady=20)
            return
        
        # Assets anzeigen (max. 50 für Performance)
        for i, asset in enumerate(assets[:50]):
            self.create_asset_item(asset, i)
    
    def create_asset_item(self, asset, index):
        """Erstellt einzelnes Asset-Item mit Vorschau"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        # Container für Asset
        item_frame = tk.Frame(
            self.asset_frame, bg=colors['background_secondary'],
            relief='solid', bd=1
        )
        item_frame.pack(fill='x', padx=5, pady=2)
        
        # Grid Layout: Vorschau | Info | Aktionen
        item_frame.grid_columnconfigure(1, weight=1)
        
        # Vorschau (links)
        preview_frame = tk.Frame(item_frame, bg=colors['background_secondary'])
        preview_frame.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        self.create_asset_preview(preview_frame, asset)
        
        # Asset-Info (mitte)
        info_frame = tk.Frame(item_frame, bg=colors['background_secondary'])
        info_frame.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        # Dateiname
        name_label = tk.Label(
            info_frame, text=asset['filename'],
            font=fonts['body'], fg=colors['text_primary'],
            bg=colors['background_secondary'], anchor='w'
        )
        name_label.pack(fill='x')
        
        # Details
        size_text = f"{asset['size']} Bytes" if asset['size'] < 1024 else f"{asset['size']//1024} KB"
        details = f"{asset['extension'].upper()} • {size_text} • {asset['source']}"
        
        details_label = tk.Label(
            info_frame, text=details,
            font=fonts['caption'], fg=colors['text_secondary'],
            bg=colors['background_secondary'], anchor='w'
        )
        details_label.pack(fill='x')
        
        # Aktionen (rechts)
        actions_frame = tk.Frame(item_frame, bg=colors['background_secondary'])
        actions_frame.grid(row=0, column=2, padx=10, pady=5, sticky='e')
        
        # Hinzufügen-Button
        add_btn = tk.Button(
            actions_frame, text="➕ Hinzufügen",
            font=fonts['caption'], bg=colors['accent_primary'], fg='white',
            relief='flat', bd=0, padx=10, pady=5, cursor='hand2',
            command=lambda a=asset: self.select_asset(a)
        )
        add_btn.pack()
        
        # Hover-Effekte
        self.add_hover_effects(item_frame, colors)
    
    def create_asset_preview(self, parent, asset):
        """Erstellt Asset-Vorschau"""
        colors = theme_manager.get_colors()
        
        try:
            if asset['extension'].lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                # Bild-Vorschau
                preview = self.get_image_preview(asset['path'])
                if preview:
                    preview_label = tk.Label(parent, image=preview, bg=colors['background_secondary'])
                    preview_label.image = preview  # Referenz behalten
                    preview_label.pack()
                    return
            
            # Fallback: Icon basierend auf Dateityp
            icon_text = self.get_file_icon(asset['extension'])
            tk.Label(
                parent, text=icon_text, font=('Arial', 24),
                bg=colors['background_secondary'], fg=colors['accent_primary']
            ).pack()
            
        except Exception as e:
            logger.debug(f"Fehler bei Vorschau für {asset['filename']}: {e}")
            tk.Label(
                parent, text="📄", font=('Arial', 24),
                bg=colors['background_secondary'], fg=colors['text_secondary']
            ).pack()
    
    def get_image_preview(self, image_path):
        """Erstellt Bild-Vorschau"""
        try:
            if image_path in self.preview_cache:
                return self.preview_cache[image_path]
            
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image.thumbnail((64, 64), Image.Resampling.LANCZOS)
                
                # Quadratisches Thumbnail erstellen
                thumb = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
                offset = ((64 - image.size[0]) // 2, (64 - image.size[1]) // 2)
                thumb.paste(image, offset)
                
                photo = ImageTk.PhotoImage(thumb)
                self.preview_cache[image_path] = photo
                return photo
            
        except Exception as e:
            logger.debug(f"Fehler beim Erstellen der Vorschau für {image_path}: {e}")
        
        return None
    
    def get_file_icon(self, extension):
        """Gibt Icon für Dateityp zurück"""
        icons = {
            '.png': '🖼️', '.jpg': '📷', '.jpeg': '📷', '.gif': '🎞️',
            '.svg': '🎨', '.ico': '🎯', '.pdf': '📄', '.txt': '📝',
            '.md': '📋', '.json': '⚙️', '.yaml': '⚙️', '.yml': '⚙️'
        }
        return icons.get(extension.lower(), '📄')
    
    def add_hover_effects(self, widget, colors):
        """Fügt Hover-Effekte hinzu"""
        original_bg = widget.cget('bg')
        
        def on_enter(e):
            widget.configure(bg=colors['background_hover'])
        
        def on_leave(e):
            widget.configure(bg=original_bg)
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def switch_category(self, category):
        """Wechselt Asset-Kategorie"""
        self.current_category = category
        
        # Tab-Buttons aktualisieren
        colors = theme_manager.get_colors()
        for cat, btn in self.tab_buttons.items():
            if cat == category:
                btn.configure(bg=colors['accent_primary'], fg='white')
            else:
                btn.configure(bg=colors['background_tertiary'], fg=colors['text_primary'])
        
        # Asset-Liste aktualisieren
        self.populate_current_category()
        logger.debug(f"Kategorie gewechselt zu: {category}")
    
    def select_asset(self, asset):
        """Wählt Asset aus und ruft Callback auf"""
        try:
            if self.on_asset_selected:
                self.on_asset_selected(asset)
                logger.info(f"Asset ausgewählt: {asset['filename']}")
        except Exception as e:
            logger.error(f"Fehler bei Asset-Auswahl: {e}")
            messagebox.showerror("Fehler", f"Asset konnte nicht hinzugefügt werden: {e}")
    
    def refresh_assets(self):
        """Aktualisiert Asset-Liste"""
        try:
            self.preview_cache.clear()  # Cache leeren
            self.load_assets()
            logger.info("Assets aktualisiert")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren: {e}")
    
    def upload_asset(self):
        """Lädt neues Asset hoch"""
        from tkinter import filedialog
        
        try:
            file_path = filedialog.askopenfilename(
                title="Asset hochladen",
                filetypes=[
                    ("Bilddateien", "*.png *.jpg *.jpeg *.gif *.bmp *.svg"),
                    ("Alle Dateien", "*.*")
                ]
            )
            
            if file_path:
                # Asset zu user_uploads kopieren
                import shutil
                uploads_dir = os.path.join("content", "user_uploads")
                os.makedirs(uploads_dir, exist_ok=True)
                
                filename = os.path.basename(file_path)
                dest_path = os.path.join(uploads_dir, filename)
                
                shutil.copy2(file_path, dest_path)
                
                # Asset-Liste aktualisieren
                self.refresh_assets()
                
                # Zu user_uploads wechseln
                self.switch_category("user_uploads")
                
                messagebox.showinfo("Upload", f"Asset hochgeladen: {filename}")
                logger.info(f"Asset hochgeladen: {filename}")
                
        except Exception as e:
            logger.error(f"Fehler beim Upload: {e}")
            messagebox.showerror("Upload-Fehler", str(e))
    
    def on_mouse_wheel(self, event):
        """Mouse-Wheel Scrolling"""
        self.list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def show_error_message(self, message):
        """Zeigt Fehlermeldung in der Liste"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        for widget in self.asset_frame.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.asset_frame, text=f"❌ {message}",
            font=fonts['body'], bg=colors['background_tertiary'],
            fg=colors['accent_warning']
        ).pack(pady=20)
    
    def pack(self, **kwargs):
        """Pack-Methode für Integration"""
        self.container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid-Methode für Integration"""
        self.container.grid(**kwargs)


class AssetPreviewDialog:
    """Dialog für Asset-Vorschau"""
    
    def __init__(self, parent, asset):
        self.asset = asset
        self.dialog = tk.Toplevel(parent)
        self.setup_dialog()
    
    def setup_dialog(self):
        """Erstellt Vorschau-Dialog"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        self.dialog.title(f"Vorschau: {self.asset['filename']}")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg=colors['background_primary'])
        
        # Header
        header = tk.Frame(self.dialog, bg=colors['background_secondary'], height=80)
        header.pack(fill='x', padx=10, pady=10)
        header.pack_propagate(False)
        
        tk.Label(
            header, text=self.asset['filename'],
            font=fonts['title'], bg=colors['background_secondary'],
            fg=colors['text_primary']
        ).pack(pady=20)
        
        # Vorschau
        if self.asset['extension'].lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            self.create_image_preview()
        else:
            self.create_file_info()
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg=colors['background_primary'])
        button_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        tk.Button(
            button_frame, text="Schließen",
            font=fonts['button'], bg=colors['background_tertiary'],
            fg=colors['text_primary'], command=self.dialog.destroy
        ).pack(side='right', padx=10)
    
    def create_image_preview(self):
        """Erstellt Bild-Vorschau"""
        try:
            colors = theme_manager.get_colors()
            
            preview_frame = tk.Frame(self.dialog, bg=colors['background_primary'])
            preview_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            image = Image.open(self.asset['path'])
            image.thumbnail((500, 400), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            preview_label = tk.Label(
                preview_frame, image=photo, bg=colors['background_primary']
            )
            preview_label.image = photo
            preview_label.pack(expand=True)
            
        except Exception as e:
            self.create_file_info()
            logger.error(f"Fehler bei Bild-Vorschau: {e}")
    
    def create_file_info(self):
        """Erstellt Datei-Info"""
        colors = theme_manager.get_colors()
        fonts = theme_manager.get_fonts(1920, 1080)
        
        info_frame = tk.Frame(self.dialog, bg=colors['background_primary'])
        info_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # File-Icon
        icon_text = "📄"
        if self.asset['extension'].lower() in ['.png', '.jpg', '.jpeg']:
            icon_text = "🖼️"
        
        tk.Label(
            info_frame, text=icon_text, font=('Arial', 48),
            bg=colors['background_primary'], fg=colors['accent_primary']
        ).pack(pady=20)
        
        # Info-Text
        info_text = f"""
Datei: {self.asset['filename']}
Typ: {self.asset['extension'].upper()}
Größe: {self.asset['size']} Bytes
Quelle: {self.asset['source']}
Pfad: {self.asset['path']}
        """
        
        tk.Label(
            info_frame, text=info_text, font=fonts['body'],
            bg=colors['background_primary'], fg=colors['text_primary'],
            justify='left'
        ).pack(pady=10)
