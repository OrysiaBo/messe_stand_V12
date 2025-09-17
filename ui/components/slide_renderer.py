#!/usr/bin/env python3
"""
ОБЪЕДИНЕННЫЙ Enhanced Slide Renderer для Dynamic Messe Stand V4
Сочетает расширенную функциональность с улучшенным PowerPoint-стилем дизайна
Поддерживает Canvas-элементы, Assets, изображения и современный дизайн
"""

import tkinter as tk
import base64
from io import BytesIO
from PIL import Image, ImageTk
import os
from core.theme import theme_manager
from core.logger import logger

class EnhancedSlideRenderer:
    """Объединенная Enhanced Slide-Renderer-класса с улучшенным дизайном"""
    
    @staticmethod
    def render_slide_to_canvas(canvas, slide_data, canvas_width, canvas_height):
        """
        ГЛАВНАЯ функция рендеринга с объединенной функциональностью
        Поддерживает Canvas-элементы, изображения, Assets и улучшенный дизайн
        """
        # Canvas очистить
        canvas.delete("all")
        
        # Улучшенное базовое рендеринг (PowerPoint-style + расширения)
        layout_info = EnhancedSlideRenderer.render_enhanced_base_slide(
            canvas, slide_data, canvas_width, canvas_height
        )
        
        # Canvas-элементы рендерить (расширенная функциональность)
        if 'canvas_elements' in slide_data and slide_data['canvas_elements']:
            EnhancedSlideRenderer.render_canvas_elements(
                canvas, slide_data['canvas_elements'], canvas_width, canvas_height
            )
        
        # Assets рендерить (расширенная функциональность)  
        if 'assets' in slide_data and slide_data['assets']:
            EnhancedSlideRenderer.render_slide_assets(
                canvas, slide_data['assets'], canvas_width, canvas_height
            )
        
        # Конфигурационные данные из JSON
        if 'config_data' in slide_data and slide_data['config_data']:
            EnhancedSlideRenderer.render_config_elements(
                canvas, slide_data['config_data'], canvas_width, canvas_height
            )
    
    @staticmethod
    def render_enhanced_base_slide(canvas, slide_data, canvas_width, canvas_height):
        """УЛУЧШЕННОЕ базовое рендеринг слайда (PowerPoint-style + расширения)"""
        try:
            # Унифицированные цвета для лучшей читабельности
            bg_color = slide_data.get('background_color', '#FFFFFF')
            text_color = slide_data.get('text_color', '#1F1F1F')
            title_color = '#1E88E5'   # Bertrandt синий - улучшенная читаемость
            accent_color = '#FF6600'  # Bertrandt оранжевый
            
            # Расчет оптимального масштабирования
            margin = 40
            slide_width = 1920
            slide_height = 1080
            
            scale_x = (canvas_width - margin) / slide_width
            scale_y = (canvas_height - margin) / slide_height
            scale_factor = min(scale_x, scale_y, 1.0)
            
            # Центрированная позиция
            scaled_width = slide_width * scale_factor
            scaled_height = slide_height * scale_factor
            offset_x = (canvas_width - scaled_width) / 2
            offset_y = (canvas_height - scaled_height) / 2
            
            # Улучшенная тень (более профессиональная)
            shadow_offset = max(6, int(8 * scale_factor))
            canvas.create_rectangle(
                offset_x + shadow_offset, offset_y + shadow_offset,
                offset_x + scaled_width + shadow_offset, offset_y + scaled_height + shadow_offset,
                fill='#D0D0D0', outline='', tags='slide_shadow'
            )
            
            # Главный фон с тонкой рамкой
            canvas.create_rectangle(
                offset_x, offset_y, offset_x + scaled_width, offset_y + scaled_height,
                fill=bg_color, outline='#CCCCCC', width=2, tags='slide_background'
            )
            
            # Улучшенный заголовок с лучшим позиционированием
            title = slide_data.get('title', '')
            title_rendered = False
            
            if title:
                title_y = offset_y + (60 * scale_factor)
                canvas.create_text(
                    offset_x + scaled_width / 2, title_y,
                    text=title,
                    font=('Segoe UI', max(20, int(28 * scale_factor)), 'bold'),
                    fill=title_color,
                    anchor='center',
                    width=scaled_width - (80 * scale_factor),
                    tags='slide_title'
                )
                
                # Улучшенная акцентная линия под заголовком
                line_y = title_y + (40 * scale_factor)
                canvas.create_line(
                    offset_x + (60 * scale_factor), line_y,
                    offset_x + scaled_width - (60 * scale_factor), line_y,
                    fill=accent_color,
                    width=max(3, int(4 * scale_factor)),
                    tags='slide_accent'
                )
                title_rendered = True
            
            # Улучшенный контент с лучшим spacing
            content = slide_data.get('content', '')
            if content:
                content_y_start = offset_y + (140 * scale_factor if title_rendered else 80 * scale_factor)
                content_lines = content.replace('\n\n', '\n').split('\n')
                line_height = max(24, int(30 * scale_factor))
                
                for i, line in enumerate(content_lines[:15]):  # Увеличено до 15 строк
                    if line.strip():
                        y_pos = content_y_start + (i * line_height)
                        if y_pos < offset_y + scaled_height - (80 * scale_factor):
                            # Улучшенное форматирование списков
                            display_text = f"• {line.strip()}" if not line.strip().startswith('•') else line.strip()
                            
                            canvas.create_text(
                                offset_x + (80 * scale_factor),
                                y_pos,
                                text=display_text,
                                font=('Segoe UI', max(10, int(14 * scale_factor))),
                                fill=text_color,
                                anchor='nw',
                                width=scaled_width - (160 * scale_factor),
                                tags='slide_content'
                            )
            
            # Улучшенное брендирование - логотип Bertrandt (справа внизу)
            canvas.create_text(
                offset_x + scaled_width - (40 * scale_factor),
                offset_y + scaled_height - (30 * scale_factor),
                text="BERTRANDT",
                font=('Segoe UI', max(8, int(12 * scale_factor)), 'bold'),
                fill='#003366',
                anchor='se',
                tags='slide_branding'
            )
            
            # Номер слайда (слева внизу)
            slide_number = slide_data.get('slide_number', slide_data.get('slide_id', 1))
            canvas.create_text(
                offset_x + (40 * scale_factor),
                offset_y + scaled_height - (30 * scale_factor),
                text=f"Folie {slide_number}",
                font=('Segoe UI', max(6, int(10 * scale_factor))),
                fill='#666666',
                anchor='sw',
                tags='slide_number'
            )
            
            # Return layout info для Canvas-элементов
            return {
                'offset_x': offset_x,
                'offset_y': offset_y,
                'scaled_width': scaled_width,
                'scaled_height': scaled_height,
                'scale_factor': scale_factor
            }
            
        except Exception as e:
            logger.error(f"Ошибка при улучшенном базовом рендеринге слайда: {e}")
            return {
                'offset_x': 0, 'offset_y': 0,
                'scaled_width': canvas_width, 'scaled_height': canvas_height,
                'scale_factor': 1.0
            }
    
    @staticmethod
    def render_canvas_elements(canvas, canvas_elements, canvas_width, canvas_height):
        """Рендерит Canvas-элементы (текст, изображения, формы)"""
        try:
            layout_info = EnhancedSlideRenderer.get_layout_info(canvas_width, canvas_height)
            
            for element in canvas_elements:
                element_type = element.get('type', 'unknown')
                
                if element_type == 'window':
                    widget_type = element.get('widget_type', 'Text')
                    if widget_type == 'Text':
                        EnhancedSlideRenderer.render_text_widget(canvas, element, layout_info)
                    elif widget_type == 'Label':
                        EnhancedSlideRenderer.render_label_widget(canvas, element, layout_info)
                elif element_type == 'text':
                    EnhancedSlideRenderer.render_text_element(canvas, element, layout_info)
                elif element_type == 'image':
                    EnhancedSlideRenderer.render_image_element(canvas, element, layout_info)
                elif element_type == 'rectangle':
                    EnhancedSlideRenderer.render_rectangle_element(canvas, element, layout_info)
                else:
                    logger.debug(f"Неизвестный тип Canvas-элемента: {element_type}")
            
            logger.debug(f"{len(canvas_elements)} Canvas-элементов отрендерено")
            
        except Exception as e:
            logger.error(f"Ошибка при рендеринге Canvas-элементов: {e}")
    
    @staticmethod
    def render_text_widget(canvas, element, layout_info):
        """Рендерит Text widget из JSON конфигурации"""
        try:
            text = element.get('text', '')
            coords = element.get('coords', [100, 100])
            font = element.get('font', '{Segoe UI} 16')
            fg = element.get('fg', '#2C3E50')
            bg = element.get('bg', 'white')
            width = element.get('width', 60)
            height = element.get('height', 8)
            
            # Позицию масштабировать
            x, y = coords[0], coords[1] 
            scaled_x = layout_info['offset_x'] + (x * layout_info['scale_factor'])
            scaled_y = layout_info['offset_y'] + (y * layout_info['scale_factor'])
            
            # Font парсить
            font_parts = font.strip('{}').split()
            font_family = 'Segoe UI'
            font_size = 16
            font_weight = 'normal'
            
            if len(font_parts) >= 2:
                font_family = font_parts[0]
                font_size = int(font_parts[1])
                if len(font_parts) > 2 and 'bold' in font_parts[2]:
                    font_weight = 'bold'
            
            # Масштабирование размера шрифта
            scaled_font_size = max(8, int(font_size * layout_info['scale_factor']))
            
            # Многострочный текст
            lines = text.replace('\\n', '\n').split('\n')
            line_height = scaled_font_size + 4
            
            for i, line in enumerate(lines):
                if line.strip():
                    canvas.create_text(
                        scaled_x, scaled_y + (i * line_height),
                        text=line,
                        font=(font_family, scaled_font_size, font_weight),
                        fill=fg,
                        anchor='nw',
                        width=width * layout_info['scale_factor'] * 8,  # Приблизительная ширина
                        tags='canvas_text_widget'
                    )
            
        except Exception as e:
            logger.error(f"Ошибка при рендеринге Text widget: {e}")
    
    @staticmethod
    def render_label_widget(canvas, element, layout_info):
        """Рендерит Label widget из JSON конфигурации"""
        try:
            text = element.get('text', '')
            coords = element.get('coords', [100, 100])
            font = element.get('font', '{Segoe UI} 16')
            fg = element.get('fg', '#003366')
            anchor = element.get('anchor', 'center')
            justify = element.get('justify', 'center')
            
            # Позицию масштабировать
            x, y = coords[0], coords[1]
            scaled_x = layout_info['offset_x'] + (x * layout_info['scale_factor'])
            scaled_y = layout_info['offset_y'] + (y * layout_info['scale_factor'])
            
            # Font парсить
            font_parts = font.strip('{}').split()
            font_family = 'Segoe UI'
            font_size = 16
            font_weight = 'normal'
            
            if len(font_parts) >= 2:
                font_family = font_parts[0]
                font_size = int(font_parts[1])
                if len(font_parts) > 2 and 'bold' in font_parts[2]:
                    font_weight = 'bold'
            
            # Масштабирование размера шрифта
            scaled_font_size = max(8, int(font_size * layout_info['scale_factor']))
            
            canvas.create_text(
                scaled_x, scaled_y,
                text=text,
                font=(font_family, scaled_font_size, font_weight),
                fill=fg,
                anchor=anchor,
                tags='canvas_label_widget'
            )
            
        except Exception as e:
            logger.error(f"Ошибка при рендеринге Label widget: {e}")
    
    @staticmethod
    def render_rectangle_element(canvas, element, layout_info):
        """Рендерит rectangle элемент"""
        try:
            coords = element.get('coords', [0, 0, 100, 100])
            fill = element.get('fill', '')
            outline = element.get('outline', '')
            width = element.get('width', '1.0')
            
            # Координаты масштабировать
            x1, y1, x2, y2 = coords
            scaled_x1 = layout_info['offset_x'] + (x1 * layout_info['scale_factor'])
            scaled_y1 = layout_info['offset_y'] + (y1 * layout_info['scale_factor'])
            scaled_x2 = layout_info['offset_x'] + (x2 * layout_info['scale_factor'])
            scaled_y2 = layout_info['offset_y'] + (y2 * layout_info['scale_factor'])
            
            # Width масштабировать
            line_width = max(1, int(float(width) * layout_info['scale_factor']))
            
            canvas.create_rectangle(
                scaled_x1, scaled_y1, scaled_x2, scaled_y2,
                fill=fill if fill else '',
                outline=outline if outline else '',
                width=line_width,
                tags='canvas_rectangle'
            )
            
        except Exception as e:
            logger.error(f"Ошибка при рендеринге rectangle: {e}")
    
    @staticmethod
    def render_text_element(canvas, element, layout_info):
        """Рендерит обычный text элемент"""
        try:
            content = element.get('content', '')
            x = element.get('x', 100)
            y = element.get('y', 100)
            font_info = element.get('font', 'Arial 12')
            is_title = element.get('is_title', False)
            
            # Позицию масштабировать
            scaled_x = layout_info['offset_x'] + (x * layout_info['scale_factor'])
            scaled_y = layout_info['offset_y'] + (y * layout_info['scale_factor'])
            
            # Font парсить
            font_family = 'Arial'
            font_size = 12
            font_weight = 'normal'
            
            try:
                if isinstance(font_info, str):
                    parts = font_info.split()
                    if len(parts) >= 2:
                        font_family = parts[0]
                        font_size = int(''.join(filter(str.isdigit, parts[1])))
                        if 'bold' in font_info.lower():
                            font_weight = 'bold'
                elif isinstance(font_info, tuple):
                    font_family = font_info[0]
                    font_size = font_info[1] if len(font_info) > 1 else 12
                    font_weight = font_info[2] if len(font_info) > 2 else 'normal'
            except:
                pass
            
            # Масштабирование размера шрифта
            scaled_font_size = max(8, int(font_size * layout_info['scale_factor']))
            
            # Цвет по типу
            color = '#1E88E5' if is_title else '#2C3E50'
            
            # Текст рендерить
            canvas.create_text(
                scaled_x, scaled_y,
                text=content,
                font=(font_family, scaled_font_size, font_weight),
                fill=color,
                anchor='nw',
                width=min(400 * layout_info['scale_factor'], layout_info['scaled_width'] - scaled_x),
                tags='canvas_text'
            )
            
        except Exception as e:
            logger.error(f"Ошибка при рендеринге text элемента: {e}")
    
    @staticmethod
    def render_image_element(canvas, element, layout_info):
        """Рендерит image элемент"""
        try:
            x = element.get('x', 100)
            y = element.get('y', 100)
            width = element.get('width', 200)
            height = element.get('height', 150)
            
            # Позицию и размер масштабировать
            scaled_x = layout_info['offset_x'] + (x * layout_info['scale_factor'])
            scaled_y = layout_info['offset_y'] + (y * layout_info['scale_factor'])
            scaled_width = width * layout_info['scale_factor']
            scaled_height = height * layout_info['scale_factor']
            
            # Изображение загрузить
            image = None
            
            # Попытка файл-path
            if 'file_path' in element and os.path.exists(element['file_path']):
                try:
                    image = Image.open(element['file_path'])
                    logger.debug(f"Изображение из файла загружено: {element['file_path']}")
                except Exception as e:
                    logger.debug(f"Ошибка при загрузке файла: {e}")
            
            # Попытка Base64-данные
            if image is None and 'image_data' in element:
                try:
                    image_bytes = base64.b64decode(element['image_data'])
                    image = Image.open(BytesIO(image_bytes))
                    logger.debug("Изображение из Base64-данных загружено")
                except Exception as e:
                    logger.debug(f"Ошибка при загрузке Base64: {e}")
            
            if image:
                # Изображение масштабировать
                image = image.resize(
                    (max(1, int(scaled_width)), max(1, int(scaled_height))), 
                    Image.Resampling.LANCZOS
                )
                
                # PhotoImage создать
                photo = ImageTk.PhotoImage(image)
                
                # В Canvas отобразить
                canvas.create_image(
                    scaled_x, scaled_y,
                    image=photo,
                    anchor='nw',
                    tags='canvas_image'
                )
                
                # Референцию сохранить (важно для Tkinter)
                if not hasattr(canvas, '_image_refs'):
                    canvas._image_refs = []
                canvas._image_refs.append(photo)
            else:
                # Placeholder, если изображение не загружено
                canvas.create_rectangle(
                    scaled_x, scaled_y, 
                    scaled_x + scaled_width, scaled_y + scaled_height,
                    fill='#f0f0f0', outline='#ccc', width=1,
                    tags='canvas_placeholder'
                )
                
                canvas.create_text(
                    scaled_x + scaled_width/2, scaled_y + scaled_height/2,
                    text="🖼️\nИзображение\nне найдено",
                    font=('Arial', max(8, int(10 * layout_info['scale_factor']))),
                    fill='#999',
                    anchor='center',
                    tags='canvas_placeholder_text'
                )
            
        except Exception as e:
            logger.error(f"Ошибка при рендеринге image элемента: {e}")
    
    @staticmethod
    def render_config_elements(canvas, config_data, canvas_width, canvas_height):
        """Рендерит элементы из config_data (JSON конфигурация)"""
        try:
            if 'canvas_elements' in config_data:
                EnhancedSlideRenderer.render_canvas_elements(
                    canvas, config_data['canvas_elements'], canvas_width, canvas_height
                )
                logger.debug("Config canvas_elements отрендерены")
        except Exception as e:
            logger.error(f"Ошибка при рендеринге config элементов: {e}")
    
    @staticmethod
    def render_slide_assets(canvas, assets, canvas_width, canvas_height):
        """Рендерит Slide-Assets (предварительный просмотр)"""
        try:
            layout_info = EnhancedSlideRenderer.get_layout_info(canvas_width, canvas_height)
            
            # Assets в правом нижнем углу показать (маленький предпросмотр)
            asset_start_x = layout_info['offset_x'] + layout_info['scaled_width'] - (200 * layout_info['scale_factor'])
            asset_start_y = layout_info['offset_y'] + layout_info['scaled_height'] - (100 * layout_info['scale_factor'])
            
            for i, asset in enumerate(assets[:3]):  # Максимум 3 assets отобразить
                try:
                    asset_x = asset_start_x + (i * 60 * layout_info['scale_factor'])
                    
                    # Тип asset определить
                    if asset['type'] == 'image' and 'content_path' in asset:
                        # Мини-предпросмотр создать
                        if os.path.exists(asset['content_path']):
                            preview_image = Image.open(asset['content_path'])
                            size = int(50 * layout_info['scale_factor'])
                            preview_image.thumbnail((size, size), Image.Resampling.LANCZOS)
                            
                            photo = ImageTk.PhotoImage(preview_image)
                            
                            canvas.create_image(
                                asset_x, asset_start_y,
                                image=photo,
                                anchor='nw',
                                tags='slide_asset'
                            )
                            
                            # Референцию сохранить
                            if not hasattr(canvas, '_asset_refs'):
                                canvas._asset_refs = []
                            canvas._asset_refs.append(photo)
                
                except Exception as e:
                    logger.debug(f"Ошибка при рендеринге asset {i}: {e}")
            
            if assets:
                logger.debug(f"{len(assets)} Slide-assets обработано")
                
        except Exception as e:
            logger.error(f"Ошибка при рендеринге Slide-assets: {e}")
    
    @staticmethod
    def get_layout_info(canvas_width, canvas_height):
        """Вычисляет layout информацию"""
        margin = 40
        slide_width = 1920
        slide_height = 1080
        
        scale_x = (canvas_width - margin) / slide_width
        scale_y = (canvas_height - margin) / slide_height
        scale_factor = min(scale_x, scale_y, 1.0)
        
        scaled_width = slide_width * scale_factor
        scaled_height = slide_height * scale_factor
        offset_x = (canvas_width - scaled_width) / 2
        offset_y = (canvas_height - scaled_height) / 2
        
        return {
            'offset_x': offset_x,
            'offset_y': offset_y,
            'scaled_width': scaled_width,
            'scaled_height': scaled_height,
            'scale_factor': scale_factor
        }
    
    @staticmethod
    def clear_canvas_references(canvas):
        """Очищает Canvas-референции (Memory-Management)"""
        try:
            if hasattr(canvas, '_image_refs'):
                canvas._image_refs.clear()
            if hasattr(canvas, '_asset_refs'):
                canvas._asset_refs.clear()
        except:
            pass


# Legacy-совместимая Wrapper-класса
class SlideRenderer:
    """Legacy-совместимая Wrapper-класса для обратной совместимости"""
    
    @staticmethod
    def render_slide_to_canvas(canvas, slide_data, canvas_width, canvas_height):
        """Legacy-совместимая render методика"""
        # Расширенные данные из slide_data извлечь
        if hasattr(slide_data, '__dict__'):
            # SlideData-объект
            extended_data = {
                'title': slide_data.title,
                'content': slide_data.content,
                'slide_number': getattr(slide_data, 'slide_id', 1),
                'background_color': '#FFFFFF',
                'text_color': '#1F1F1F',
                'canvas_elements': getattr(slide_data, 'canvas_elements', []),
                'assets': getattr(slide_data, 'assets', []),
                'config_data': getattr(slide_data, 'config_data', {})
            }
        else:
            # Dictionary
            extended_data = slide_data.copy()
            if 'canvas_elements' not in extended_data:
                extended_data['canvas_elements'] = []
            if 'assets' not in extended_data:
                extended_data['assets'] = []
            if 'config_data' not in extended_data:
                extended_data['config_data'] = {}
        
        # Расширенный renderer использовать
        EnhancedSlideRenderer.render_slide_to_canvas(
            canvas, extended_data, canvas_width, canvas_height
        )
    
    @staticmethod  
    def render_slide_with_elements(canvas, slide_data, canvas_width, canvas_height):
        """Новая методика для явного Canvas-element рендеринга"""
        EnhancedSlideRenderer.render_slide_to_canvas(
            canvas, slide_data, canvas_width, canvas_height
        )


# Export расширенных функций
__all__ = ['SlideRenderer', 'EnhancedSlideRenderer']
