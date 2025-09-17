#!/usr/bin/env python3
"""
Creator Tab für die Bertrandt GUI
3-Spalten Drag & Drop Editor für Demo-Folien
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import base64
from io import BytesIO
from PIL import Image, ImageTk
from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer
from models.content import content_manager
from datetime import datetime

class CreatorTab:
    """3-Spalten Creator-Tab für Demo-Folien Bearbeitung"""
    
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
        
        # Drag & Drop Variablen
        self.drag_data = {'element_type': None, 'widget': None}
        self.slide_width = 1920
        self.slide_height = 1080
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.create_creator_content()
        self.schedule_auto_save()
        
    def schedule_auto_save(self):
        """Планує автоматичне збереження через 3 секунди"""
        if self.auto_save_timer_id:
            self.main_window.root.after_cancel(self.auto_save_timer_id)
        self.auto_save_timer_id = self.main_window.root.after(3000, self.auto_save_presentation)

    def manual_save_slide(self):
        """Ручне збереження слайду"""
        self.manual_save = True
        self.save_current_slide_content()

    def save_current_slide_content(self):
        """Зберігає контент поточного слайду в Creator з синхронізацією"""
        try:
            if not hasattr(self, 'current_slide') or not self.current_slide:
                logger.warning("No current slide to save")
                return False
            
            title_text = ""
            content_text = ""
            canvas_elements = []
            
            if self.edit_mode and hasattr(self, 'edit_widgets'):
                # Режим редагування - отримати з віджетів
                if 'title' in self.edit_widgets:
                    title_text = self.edit_widgets['title'].get('1.0', 'end-1c')
                if 'content' in self.edit_widgets:
                    content_text = self.edit_widgets['content'].get('1.0', 'end-1c')
            else:
                # Режим попереднього перегляду - отримати з canvas widgets
                for item in self.slide_canvas.find_all():
                    if self.slide_canvas.type(item) == 'window':
                        try:
                            widget = self.slide_canvas.nametowidget(self.slide_canvas.itemcget(item, 'window'))
                            coords = self.slide_canvas.coords(item)
                            
                            if isinstance(widget, tk.Label) and hasattr(widget, 'image'):
                                # Це картинка - зберегти дані про неї
                                try:
                                    image_data = {
                                        'type': 'image',
                                        'x': coords[0] if coords else 0,
                                        'y': coords[1] if coords else 0,
                                        'width': widget.winfo_width(),
                                        'height': widget.winfo_height()
                                    }
                                    
                                    # Зберегти шлях до файлу якщо є
                                    if hasattr(widget, 'image_path'):
                                        image_data['file_path'] = widget.image_path
                                    
                                    # Або зберегти дані картинки як base64
                                    if hasattr(widget, 'image'):
                                        try:
                                            # Конвертувати PhotoImage в PIL Image
                                            pil_image = ImageTk.getimage(widget.image)
                                            
                                            # Зберегти як base64
                                            buffer = BytesIO()
                                            pil_image.save(buffer, format='PNG')
                                            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                                            image_data['image_data'] = image_base64
                                            
                                        except Exception as e:
                                            logger.warning(f"Could not save image data: {e}")
                                    
                                    canvas_elements.append(image_data)
                                    
                                except Exception as e:
                                    logger.error(f"Error saving image element: {e}")
                                    
                            elif isinstance(widget, tk.Text):
                                text_content = widget.get('1.0', 'end-1c')
                                
                                # Визначити тип на основі font або позиції
                                font = widget.cget('font')
                                if isinstance(font, tuple) and len(font) >= 2:
                                    font_size = font[1] if isinstance(font[1], int) else int(font[1])
                                    
                                    # Великий шрифт = заголовок
                                    if font_size >= 20 or 'bold' in str(font):
                                        if not title_text:  # Перший великий текст = заголовок
                                            title_text = text_content
                                        else:
                                            content_text += text_content + "\n"
                                    else:
                                        content_text += text_content + "\n"
                                else:
                                    content_text += text_content + "\n"
                                
                                # Зберегти позицію тексту
                                canvas_elements.append({
                                    'type': 'text',
                                    'content': text_content,
                                    'x': coords[0] if coords else 0,
                                    'y': coords[1] if coords else 0
                                })
                                    
                        except Exception as e:
                            logger.debug(f"Could not process canvas widget: {e}")
                            continue
            
            # Очистити зайві переноси рядків
            content_text = content_text.strip()
            
            # Якщо не знайшли заголовок, використати перший рядок контенту
            if not title_text and content_text:
                lines = content_text.split('\n')
                title_text = lines[0] if lines else f"Demo-Folie {self.current_edit_slide}"
                content_text = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            # Якщо все ще немає заголовка, використати за замовчуванням
            if not title_text:
                title_text = f"Demo-Folie {self.current_edit_slide}"
            
            # Зберегти через content_manager для синхронізації
            success = content_manager.update_slide_content(
                self.current_edit_slide,
                title_text,
                content_text,
                {'canvas_elements': canvas_elements} if canvas_elements else None
            )
            
            if success:
                # Показати успішне збереження тільки при ручному збереженні
                if hasattr(self, 'slide_info_label') and getattr(self, 'manual_save', False):
                    original_text = self.slide_info_label.cget('text')
                    self.slide_info_label.configure(
                        text=f"✅ Demo-Folie {self.current_edit_slide} gespeichert: {title_text[:30]}..."
                    )
                    
                    # Повернути оригінальний текст через 2 секунди
                    def restore_text():
                        if hasattr(self, 'slide_info_label'):
                            self.slide_info_label.configure(text=original_text)
                    
                    self.main_window.root.after(2000, restore_text)
                    self.manual_save = False  # Скинути флаг
                
                logger.info(f"Successfully saved slide {self.current_edit_slide}: {title_text[:30]}...")
            else:
                logger.error(f"Failed to save slide {self.current_edit_slide}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error saving current slide content: {e}")
            return False

    def load_slide_to_editor(self, slide_id):
        """Завантажує Demo-Folie в редактор з правильною синхронізацією"""
        try:
            # Зберегти поточний слайд перед переключенням
            if hasattr(self, 'current_edit_slide') and hasattr(self, 'current_slide') and self.current_slide:
                self.save_current_slide_content()
            
            # Завантажити новий слайд з content_manager
            slide = content_manager.get_slide(slide_id)
            
            if slide:
                self.current_edit_slide = slide_id
                self.current_slide = slide
                
                # Очистити canvas
                self.clear_slide_canvas()
                
                # Відновити збережені елементи якщо є
                if hasattr(slide, 'extra_data') and slide.extra_data and 'canvas_elements' in slide.extra_data:
                    self.restore_canvas_elements(slide.extra_data['canvas_elements'])
                else:
                    # Показати попередній перегляд якщо немає додаткових елементів
                    self.render_slide_preview()
                
                # Оновити UI
                self.update_thumbnail_selection()
                self.update_slide_counter()
                
                if hasattr(self, 'slide_info_label'):
                    self.slide_info_label.configure(
                        text=f"Demo-Folie {slide_id}: {slide.title}"
                    )
                
                logger.debug(f"Loaded slide {slide_id} into editor: {slide.title}")
                
            else:
                logger.warning(f"Slide {slide_id} not found")
                
        except Exception as e:
            logger.error(f"Error loading slide to editor: {e}")

    def restore_canvas_elements(self, canvas_elements):
        """Відновлює збережені елементи canvas (картинки, текст)"""
        try:
            if not canvas_elements:
                return
                
            for element in canvas_elements:
                if element['type'] == 'image':
                    self.restore_image_element(element)
                elif element['type'] == 'text':
                    self.restore_text_element(element)
                    
        except Exception as e:
            logger.error(f"Error restoring canvas elements: {e}")

    def restore_image_element(self, image_data):
        """Відновлює картинку з збережених даних"""
        try:
            image = None
            
            # Спробувати завантажити з файлу
            if 'file_path' in image_data and os.path.exists(image_data['file_path']):
                try:
                    image = Image.open(image_data['file_path'])
                    image.thumbnail((400, 300), Image.Resampling.LANCZOS)
                except Exception as e:
                    logger.warning(f"Could not load image from file: {e}")
            
            # Якщо файл недоступний, спробувати base64 дані
            if image is None and 'image_data' in image_data:
                try:
                    image_bytes = base64.b64decode(image_data['image_data'])
                    image = Image.open(BytesIO(image_bytes))
                except Exception as e:
                    logger.warning(f"Could not load image from base64: {e}")
            
            if image:
                # Створити PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Створити Label з картинкою
                image_label = tk.Label(
                    self.slide_canvas,
                    image=photo,
                    bg='white',
                    relief='solid',
                    bd=1
                )
                image_label.image = photo  # Зберегти посилання
                
                if 'file_path' in image_data:
                    image_label.image_path = image_data['file_path']
                
                # Розмістити на canvas в збереженій позиції
                canvas_item = self.slide_canvas.create_window(
                    image_data['x'], image_data['y'],
                    window=image_label,
                    anchor='nw'
                )
                
                # Зробити переміщуваним
                self.make_canvas_item_movable(image_label, canvas_item)
                
                logger.debug(f"Restored image at position ({image_data['x']}, {image_data['y']})")
            
        except Exception as e:
            logger.error(f"Error restoring image element: {e}")

    def restore_text_element(self, text_data):
        """Відновлює текстовий елемент з збережених даних"""
        try:
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            # Створити текстовий віджет
            text_widget = tk.Text(
                self.slide_canvas,
                width=30,
                height=3,
                font=(fonts['body'][0], 14),
                bg='white',
                fg='#2C3E50',
                relief='solid',
                bd=1,
                wrap='word',
                insertbackground='#2C3E50'
            )
            
            # Вставити збережений текст
            text_widget.insert('1.0', text_data.get('content', ''))
            
            # Розмістити на canvas в збереженій позиції
            canvas_item = self.slide_canvas.create_window(
                text_data['x'], text_data['y'],
                window=text_widget,
                anchor='nw'
            )
            
            # Зробити переміщуваним
            self.make_canvas_item_movable(text_widget, canvas_item)
            
            # Автозбереження при редагуванні
            text_widget.bind('<KeyRelease>', lambda e: self.schedule_auto_save())
            
            logger.debug(f"Restored text element at position ({text_data['x']}, {text_data['y']})")
            
        except Exception as e:
            logger.error(f"Error restoring text element: {e}")

    def render_slide_preview(self):
        """Рендерить попередній перегляд слайду використовуючи той же рендерер що і Demo"""
        try:
            if not hasattr(self, 'slide_canvas') or not self.current_slide:
                return
                
            canvas_width = self.slide_canvas.winfo_width()
            canvas_height = self.slide_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:
                # Підготувати дані слайду
                slide_data = {
                    'title': self.current_slide.title,
                    'content': self.current_slide.content,
                    'slide_number': self.current_edit_slide,
                    'background_color': '#FFFFFF',
                    'text_color': '#1F1F1F'
                }
                
                # Використати той же рендерер що і Demo
                SlideRenderer.render_slide_to_canvas(
                    self.slide_canvas,
                    slide_data,
                    canvas_width,
                    canvas_height
                )
                
                logger.debug(f"Rendered slide preview {self.current_edit_slide} in creator")
                
        except Exception as e:
            logger.error(f"Error rendering slide preview: {e}")

    def clear_slide_canvas(self):
        """Очищає canvas від всього контенту"""
        try:
            # Видалити всі елементи крім dropzone
            all_items = self.slide_canvas.find_all()
            for item in all_items:
                tags = self.slide_canvas.gettags(item)
                if 'dropzone' not in tags:
                    self.slide_canvas.delete(item)
            
            logger.debug("Canvas cleared")
            
        except Exception as e:
            logger.error(f"Error clearing canvas: {e}")

    def update_thumbnail_selection(self):
        """Оновлює виділення thumbnail в списку слайдів"""
        try:
            colors = theme_manager.get_colors()
            
            if hasattr(self, 'thumbnail_buttons'):
                for slide_id, button in self.thumbnail_buttons.items():
                    if slide_id == self.current_edit_slide:
                        button.configure(
                            bg=colors['accent_primary'],
                            fg='white'
                        )
                    else:
                        button.configure(
                            bg=colors['background_tertiary'],
                            fg=colors['text_primary']
                        )
            
            logger.debug(f"Updated thumbnail selection for slide {self.current_edit_slide}")
            
        except Exception as e:
            logger.error(f"Error updating thumbnail selection: {e}")

    def update_slide_counter(self):
        """Оновлює лічильник слайдів"""
        try:
            if hasattr(self, 'slide_counter') and hasattr(self, 'thumbnail_buttons'):
                self.slide_counter.configure(
                    text=f"Demo-Folie {self.current_edit_slide} von {len(self.thumbnail_buttons)}"
                )
        except Exception as e:
            logger.error(f"Error updating slide counter: {e}")

    def auto_save_presentation(self):
        """Автоматично зберігає презентацію"""
        try:
            self.save_current_slide_content()
            # Планує наступне збереження
            self.schedule_auto_save()
        except Exception as e:
            logger.error(f"Fehler beim Auto-Speichern: {e}")
            self.schedule_auto_save()  # Продовжуємо спроби
        
    def create_creator_content(self):
        """Erstellt den 3-Spalten Creator-Tab"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Haupt-Container
        self.container = tk.Frame(self.parent, bg=colors['background_primary'])
        
        # Header-Toolbar (oben)
        self.create_header_toolbar()
        
        # 3-Spalten-Layout
        content_frame = tk.Frame(self.container, bg=colors['background_primary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Grid-Layout für 3 Spalten
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=250)  # Folien-Übersicht (links)
        content_frame.grid_columnconfigure(1, weight=1, minsize=800)  # Editor (mitte)
        content_frame.grid_columnconfigure(2, weight=0, minsize=300)  # Tool-Box (rechts)
        
        # Spalte 1: Folien-Übersicht (links)
        self.create_slides_overview_panel(content_frame)
        
        # Spalte 2: Haupt-Editor (mitte)
        self.create_main_editor_panel(content_frame)
        
        # Spalte 3: Tool-Box (rechts)
        self.create_toolbox_panel(content_frame)
        
        # Status-Leiste (unten)
        self.create_status_bar()
    
    def create_header_toolbar(self):
        """Erstellt die Header-Toolbar"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Header-Frame (15% höher)
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
            text="🎨 Slide Creator",
            font=fonts['title'],
            fg=colors['accent_primary'],
            bg=colors['background_secondary']
        )
        title_label.pack(anchor='w', pady=(15, 0))
        
        subtitle_label = tk.Label(
            title_frame,
            text="Drag & Drop Editor",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Aktionen
        actions_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        actions_frame.pack(side='left', fill='y', padx=20)
        
        # Speichern
        save_btn = tk.Button(
            actions_frame,
            text="💾 Speichern",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.manual_save_slide
        )
        save_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Vorschau
        preview_btn = tk.Button(
            actions_frame,
            text="👁 Vorschau",
            font=fonts['button'],
            bg=colors['accent_secondary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.preview_slide
        )
        preview_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Slide-Navigation
        nav_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        nav_frame.pack(side='right', fill='y', padx=(20, 15))
        
        # Slide-Zähler
        self.slide_counter = tk.Label(
            nav_frame,
            text="Demo-Folie 1 von 10",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.slide_counter.pack(pady=(20, 5))
        
        # Navigation-Buttons
        nav_buttons = tk.Frame(nav_frame, bg=colors['background_secondary'])
        nav_buttons.pack()
        
        prev_btn = tk.Button(
            nav_buttons,
            text="◀ Zurück",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.previous_slide
        )
        prev_btn.pack(side='left', padx=(0, 5))
        
        next_btn = tk.Button(
            nav_buttons,
            text="Weiter ▶",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.next_slide
        )
        next_btn.pack(side='left', padx=(5, 0))
    
    def create_slides_overview_panel(self, parent):
        """Erstellt die Folien-Übersicht (links) - Demo-Folien"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Panel Frame
        panel_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1,
            width=250
        )
        panel_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        panel_frame.grid_propagate(False)
        
        # Header
        header_frame = tk.Frame(panel_frame, bg=colors['background_secondary'])
        header_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        header_label = tk.Label(
            header_frame,
            text="📋 Demo-Folien",
            font=fonts['title'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        header_label.pack(anchor='w')
        
        # Info-Label
        info_label = tk.Label(
            header_frame,
            text="Klicken zum Bearbeiten",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        info_label.pack(anchor='w', pady=(5, 0))
        
        # Scrollable Thumbnail List
        canvas = tk.Canvas(panel_frame, bg=colors['background_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(panel_frame, orient="vertical", command=canvas.yview)
        self.thumbnail_frame = tk.Frame(canvas, bg=colors['background_secondary'])
        
        self.thumbnail_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.thumbnail_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        scrollbar.pack(side="right", fill="y", pady=(0, 15))
        
        # Thumbnails erstellen
        self.create_slide_thumbnails()
    
    def create_slide_thumbnails(self):
        """Erstellt Slide-Thumbnails aus den Demo-Folien"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Якщо thumbnails вже створені, тільки оновити їх
        if hasattr(self, 'thumbnail_buttons') and self.thumbnail_buttons:
            slides = content_manager.get_all_slides()
            for slide_id, slide in slides.items():
                if slide_id in self.thumbnail_buttons:
                    button = self.thumbnail_buttons[slide_id]
                    title = slide.title
                    display_title = title[:18] + "..." if len(title) > 18 else title
                    button.configure(text=f"Folie {slide_id}\n{display_title}")
            return
        
        self.thumbnail_buttons = {}
        
        # Content-Manager verwenden (Demo-Folien)
        slides = content_manager.get_all_slides()
        
        if not slides:
            logger.warning("Keine Demo-Folien gefunden")
            return
        
        for slide_id, slide in slides.items():
            try:
                # Thumbnail-Container
                thumb_container = tk.Frame(
                    self.thumbnail_frame,
                    bg=colors['background_secondary']
                )
                thumb_container.pack(fill='x', padx=5, pady=3)
                
                # Thumbnail-Button
                is_active = slide_id == self.current_edit_slide
                bg_color = colors['accent_primary'] if is_active else colors['background_tertiary']
                
                title = slide.title
                display_title = title[:18] + "..." if len(title) > 18 else title
                
                thumb_btn = tk.Button(
                    thumb_container,
                    text=f"Folie {slide_id}\n{display_title}",
                    font=fonts['body'],
                    bg=bg_color,
                    fg='white' if is_active else colors['text_primary'],
                    relief='flat',
                    bd=0,
                    width=20,
                    height=3,
                    cursor='hand2',
                    command=lambda sid=slide_id: self.load_slide_to_editor(sid),
                    justify='left'
                )
                thumb_btn.pack(fill='x', ipady=5)
                
                self.thumbnail_buttons[slide_id] = thumb_btn
                
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von Thumbnail für Slide {slide_id}: {e}")
    
    def create_main_editor_panel(self, parent):
        """Erstellt den Haupt-Editor (mitte) - immer weiße Canvas"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Editor Frame
        editor_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1
        )
        editor_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Header
        header_frame = tk.Frame(editor_frame, bg=colors['background_secondary'])
        header_frame.pack(fill='x', padx=20, pady=(15, 10))
        
        # Slide-Info
        self.slide_info_label = tk.Label(
            header_frame,
            text="Demo-Folie 1: Wählen Sie eine Folie zum Bearbeiten",
            font=fonts['display'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.slide_info_label.pack(anchor='w')
        
        # Canvas für Drag & Drop Editor - volle Breite und Höhe
        canvas_frame = tk.Frame(editor_frame, bg=colors['background_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(10, 10))
        
        # Canvas Container - nutzt kompletten verfügbaren Platz
        canvas_container = tk.Frame(canvas_frame, bg=colors['background_secondary'])
        canvas_container.pack(fill='both', expand=True)
        
        # Slide Canvas erstellen - mit dunklerem Hintergrund für besseren Kontrast
        self.slide_canvas = tk.Canvas(
            canvas_container,
            bg='#E8E8E8',  # Etwas dunkler für besseren Kontrast zur weißen Folie
            relief='flat',
            bd=0,
            highlightthickness=0
        )
        self.slide_canvas.pack(fill='both', expand=True)
        
        # Canvas-Größe überwachen und Folie entsprechend skalieren
        self.slide_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Bearbeiten-Button
        edit_button = tk.Button(
            canvas_container,
            text="Bearbeiten",
            font=fonts['button'],
            bg=colors['accent_secondary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.toggle_edit_mode
        )
        edit_button.place(relx=0.95, rely=0.05, anchor='ne')
        
        # Initiale Drop-Zone erstellen (unsichtbar)
        self.create_slide_content()
    
    def create_slide_content(self):
        """Erstellt Drop-Zone und initialen Slide-Rahmen"""
        # Unsichtbare Drop-Zone für Drop-Erkennung
        self.dropzone_rect = self.slide_canvas.create_rectangle(
            0, 0, self.slide_width, self.slide_height,
            outline='',  # Unsichtbar
            width=0,
            fill='',
            tags='dropzone'
        )
        
        # Initialen Slide-Rahmen hinzufügen
        self.slide_canvas.after(100, self.render_slide_preview)
    
    def on_canvas_resize(self, event):
        """Обробник зміни розміру canvas"""
        # Перемалювати попередній перегляд при зміні розміру
        self.main_window.root.after(100, self.render_slide_preview)

    def toggle_edit_mode(self):
        """Переключає між режимом попереднього перегляду та редагування"""
        try:
            if not hasattr(self, 'edit_mode'):
                self.edit_mode = False
                
            self.edit_mode = not self.edit_mode
            
            if self.edit_mode:
                # Режим редагування - додати текстові поля
                self.create_edit_widgets()
            else:
                # Режим попереднього перегляду - зберегти зміни та показати попередній перегляд
                self.save_current_slide_content()
                self.clear_slide_canvas()
                self.render_slide_preview()
                
        except Exception as e:
            logger.error(f"Error toggling edit mode: {e}")

    def create_edit_widgets(self):
        """Створює віджети для редагування"""
        try:
            # Очистити canvas
            self.clear_slide_canvas()
            
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            # Отримати дані поточного слайду
            slide = content_manager.get_slide(self.current_edit_slide)
            
            # Створити віджети редагування
            title_widget = tk.Text(
                self.slide_canvas,
                width=60,
                height=3,
                font=(fonts['title'][0], 24, 'bold'),
                bg='white',
                fg='#1E88E5',
                relief='flat',
                bd=1,
                wrap='word',
                insertbackground='#1E88E5'
            )
            
            content_widget = tk.Text(
                self.slide_canvas,
                width=70,
                height=15,
                font=(fonts['body'][0], 14),
                bg='white',
                fg='#2C3E50',
                relief='flat',
                bd=1,
                wrap='word',
                insertbackground='#2C3E50'
            )
            
            if slide:
                title_widget.insert('1.0', slide.title)
                content_widget.insert('1.0', slide.content)
            
            # Розмістити віджети на canvas
            self.slide_canvas.create_window(100, 50, window=title_widget, anchor='nw')
            self.slide_canvas.create_window(100, 150, window=content_widget, anchor='nw')
            
            # Зберегти посилання для подальшого використання
            self.edit_widgets = {
                'title': title_widget,
                'content': content_widget
            }
            
            # Автозбереження при редагуванні
            def on_edit(event=None):
                self.schedule_auto_save()
            
            title_widget.bind('<KeyRelease>', on_edit)
            content_widget.bind('<KeyRelease>', on_edit)
            
        except Exception as e:
            logger.error(f"Error creating edit widgets: {e}")
    
    def create_toolbox_panel(self, parent):
        """Erstellt die Tool-Box (rechts)"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Panel Frame
        panel_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1,
            width=300
        )
        panel_frame.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        panel_frame.grid_propagate(False)
        
        # Header
        header_frame = tk.Frame(panel_frame, bg=colors['background_secondary'])
        header_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        header_label = tk.Label(
            header_frame,
            text="🔧 Tool-Box",
            font=fonts['title'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        header_label.pack(anchor='w')
        
        # Tools
        tools_frame = tk.Frame(panel_frame, bg=colors['background_secondary'])
        tools_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Text-Tool
        text_btn = tk.Button(
            tools_frame,
            text="📝 Text hinzufügen",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=lambda: self.add_element('text')
        )
        text_btn.pack(fill='x', pady=5)
        
        # Image-Tool
        image_btn = tk.Button(
            tools_frame,
            text="🖼️ Bild hinzufügen",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=lambda: self.add_element('image')
        )
        image_btn.pack(fill='x', pady=5)
        
        # Clear-Tool
        clear_btn = tk.Button(
            tools_frame,
            text="🗑️ Folie leeren",
            font=fonts['button'],
            bg=colors['accent_warning'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.clear_slide
        )
        clear_btn.pack(fill='x', pady=5)
    
    def create_status_bar(self):
        """Erstellt die Status-Leiste"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        status_frame = tk.Frame(
            self.container,
            bg=colors['background_secondary'],
            height=30
        )
        status_frame.pack(fill='x', padx=10, pady=5)
        status_frame.pack_propagate(False)
        
        # Status-Text
        self.status_label = tk.Label(
            status_frame,
            text="Bereit - Wählen Sie eine Folie zum Bearbeiten",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        self.status_label.pack(side='left', padx=15, pady=5)
        
        # Speicher-Status
        self.save_status_label = tk.Label(
            status_frame,
            text="Gespeichert",
            font=fonts['caption'],
            fg=colors['text_tertiary'],
            bg=colors['background_secondary']
        )
        self.save_status_label.pack(side='right', padx=15, pady=5)
    
    def add_element(self, element_type):
        """Fügt ein Element zur Folie hinzu"""
        try:
            if element_type == 'image':
                self.add_image_element()
            elif element_type == 'text':
                self.add_text_element()
            else:
                logger.info(f"Adding {element_type} element to slide")
                messagebox.showinfo("Tool", f"{element_type.capitalize()} Tool wird implementiert")
        except Exception as e:
            logger.error(f"Error adding element: {e}")

    def add_image_element(self):
        """Додає картинку на слайд"""
        try:
            # Відкрити діалог вибору файлу
            file_path = filedialog.askopenfilename(
                title="Bild auswählen",
                filetypes=[
                    ("Bilddateien", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("GIF", "*.gif"),
                    ("Alle Dateien", "*.*")
                ]
            )
            
            if file_path:
                # Переключитися в режим редагування якщо не в ньому
                if not self.edit_mode:
                    self.toggle_edit_mode()
                
                # Завантажити та підготувати картинку
                image = Image.open(file_path)
                
                # Масштабувати картинку до розумного розміру
                max_width, max_height = 400, 300
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Створити PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Створити Label з картинкою
                image_label = tk.Label(
                    self.slide_canvas,
                    image=photo,
                    bg='white',
                    relief='solid',
                    bd=1
                )
                image_label.image = photo  # Зберегти посилання
                image_label.image_path = file_path  # Зберегти шлях до файлу
                
                # Розмістити на canvas
                canvas_item = self.slide_canvas.create_window(
                    200, 300,  # Початкова позиція
                    window=image_label,
                    anchor='nw'
                )
                
                # Зробити картинку переміщуваною
                self.make_canvas_item_movable(image_label, canvas_item)
                
                logger.info(f"Image added to slide: {os.path.basename(file_path)}")
                
                # Автоматично зберегти
                self.schedule_auto_save()
                
                # Показати повідомлення про успіх
                messagebox.showinfo("Bild hinzugefügt", f"Bild erfolgreich hinzugefügt:\n{os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen des Bildes:\n{e}")

    def add_text_element(self):
        """Додає текстовий елемент на слайд"""
        try:
            # Переключитися в режим редагування якщо не в ньому
            if not self.edit_mode:
                self.toggle_edit_mode()
            
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            # Створити новий текстовий віджет
            text_widget = tk.Text(
                self.slide_canvas,
                width=30,
                height=3,
                font=(fonts['body'][0], 14),
                bg='white',
                fg='#2C3E50',
                relief='solid',
                bd=1,
                wrap='word',
                insertbackground='#2C3E50'
            )
            
            # Додати placeholder текст
            text_widget.insert('1.0', 'Neuer Text - hier bearbeiten')
            
            # Розмістити на canvas
            canvas_item = self.slide_canvas.create_window(
                150, 400,  # Початкова позиція
                window=text_widget,
                anchor='nw'
            )
            
            # Зробити переміщуваним
            self.make_canvas_item_movable(text_widget, canvas_item)
            
            # Автозбереження при редагуванні
            text_widget.bind('<KeyRelease>', lambda e: self.schedule_auto_save())
            
            logger.info("Text element added to slide")
            
        except Exception as e:
            logger.error(f"Error adding text element: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen des Textes:\n{e}")

    def make_canvas_item_movable(self, widget, canvas_item):
        """Робить елемент на canvas переміщуваним"""
        def start_move(event):
            widget.start_x = event.x
            widget.start_y = event.y
        
        def on_move(event):
            # Обчислити нову позицію
            delta_x = event.x - widget.start_x
            delta_y = event.y - widget.start_y
            
            # Перемістити елемент
            self.slide_canvas.move(canvas_item, delta_x, delta_y)
        
        def end_move(event):
            # Зберегти зміни після переміщення
            self.schedule_auto_save()
        
        # Додати обробники подій
        widget.bind('<Button-1>', start_move)
        widget.bind('<B1-Motion>', on_move)
        widget.bind('<ButtonRelease-1>', end_move)
        
        # Змінити курсор при наведенні
        widget.bind('<Enter>', lambda e: widget.configure(cursor='hand2'))
        widget.bind('<Leave>', lambda e: widget.configure(cursor=''))
    
    def clear_slide(self):
        """Leert die aktuelle Folie"""
        try:
            result = messagebox.askyesno("Folie leeren", "Möchten Sie wirklich die aktuelle Folie leeren?")
            if result:
                self.clear_slide_canvas()
                # Видалити збережені елементи
                slide = content_manager.get_slide(self.current_edit_slide)
                if slide and hasattr(slide, 'extra_data'):
                    slide.extra_data = None
                    content_manager.update_slide_content(
                        self.current_edit_slide,
                        slide.title,
                        slide.content,
                        None
                    )
                logger.info(f"Cleared slide {self.current_edit_slide}")
        except Exception as e:
            logger.error(f"Error clearing slide: {e}")
    
    def previous_slide(self):
        """Geht zur vorherigen Folie"""
        try:
            slides = content_manager.get_all_slides()
            slide_ids = sorted(slides.keys())
            
            if slide_ids:
                current_index = slide_ids.index(self.current_edit_slide) if self.current_edit_slide in slide_ids else 0
                prev_index = (current_index - 1) % len(slide_ids)
                self.load_slide_to_editor(slide_ids[prev_index])
        except Exception as e:
            logger.error(f"Error going to previous slide: {e}")
    
    def next_slide(self):
        """Geht zur nächsten Folie"""
        try:
            slides = content_manager.get_all_slides()
            slide_ids = sorted(slides.keys())
            
            if slide_ids:
                current_index = slide_ids.index(self.current_edit_slide) if self.current_edit_slide in slide_ids else 0
                next_index = (current_index + 1) % len(slide_ids)
                self.load_slide_to_editor(slide_ids[next_index])
        except Exception as e:
            logger.error(f"Error going to next slide: {e}")
    
    def preview_slide(self):
        """Zeigt Vorschau der aktuellen Folie"""
        try:
            # Zuerst speichern
            self.save_current_slide_content()
            
            # Dann Vorschau anzeigen
            if self.edit_mode:
                self.edit_mode = False
                self.clear_slide_canvas()
                self.render_slide_preview()
            
            logger.info(f"Previewing slide {self.current_edit_slide}")
        except Exception as e:
            logger.error(f"Error previewing slide: {e}")
    
    def refresh_thumbnails(self):
        """Aktualisiert die Thumbnail-Anzeige nach Änderungen"""
        try:
            self.create_slide_thumbnails()
            logger.debug("Thumbnails refreshed")
        except Exception as e:
            logger.error(f"Error refreshing thumbnails: {e}")
    
    def refresh_theme(self):
        """Aktualisiert das Theme für den Creator-Tab"""
        try:
            # Theme-Updates für alle Komponenten
            colors = theme_manager.get_colors()
            
            # Container-Hintergrund aktualisieren
            if hasattr(self, 'container'):
                self.container.configure(bg=colors['background_primary'])
            
            # Weitere Theme-Updates können hier hinzugefügt werden
            logger.debug("Creator-Tab Theme aktualisiert")
        except Exception as e:
            logger.error(f"Error refreshing theme: {e}")
    
    def show(self):
        """Zeigt den Creator-Tab"""
        if not self.visible:
            self.container.pack(fill='both', expand=True)
            self.visible = True
            
            # Lade ersten Slide wenn noch keiner geladen
            if not hasattr(self, 'current_slide') or not self.current_slide:
                self.load_slide_to_editor(1)
            
            logger.debug("Creator-Tab angezeigt")
    
    def hide(self):
        """Versteckt den Creator-Tab"""
        if self.visible:
            # Speichere aktuelle Änderungen vor dem Verstecken
            if hasattr(self, 'current_slide') and self.current_slide:
                self.save_current_slide_content()
            
            self.container.pack_forget()
            self.visible = False
            logger.debug("Creator-Tab versteckt")
