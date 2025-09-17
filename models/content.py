#!/usr/bin/env python3
"""
Enhanced Content Manager für Dynamic Messe Stand V4
Erweitert um Asset-Management und Canvas-Element Speicherung
"""

import os
import json
import yaml
import shutil
import base64
from datetime import datetime
from pathlib import Path
from core.logger import logger
from core.storage import storage_manager

class SlideData:
    """Erweiterte Klasse für Slide-Daten mit Asset-Support"""
    
    def __init__(self, slide_id, title="", content="", layout="text"):
        self.slide_id = slide_id
        self.title = title
        self.content = content
        self.layout = layout  # "text", "image", "mixed"
        self.canvas_elements = []  # Canvas-Elemente (Text, Bilder, etc.)
        self.assets = []       # Asset-Referenzen
        self.config_data = {}  # Zusätzliche Konfiguration
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.extra_data = {}   # Legacy-Support

    def add_canvas_element(self, element_type, data):
        """Fügt ein Canvas-Element hinzu"""
        element = {
            'type': element_type,  # 'text', 'image', 'shape'
            'data': data,
            'id': len(self.canvas_elements) + 1,
            'created_at': datetime.now().isoformat()
        }
        self.canvas_elements.append(element)
        self.modified_at = datetime.now()
        return element['id']

    def add_asset(self, asset_path, asset_type='image', copy_to_content=True):
        """Fügt ein Asset hinzu und kopiert es falls erforderlich"""
        if not os.path.exists(asset_path):
            logger.error(f"Asset nicht gefunden: {asset_path}")
            return None

        asset_info = {
            'original_path': asset_path,
            'type': asset_type,
            'filename': os.path.basename(asset_path),
            'added_at': datetime.now().isoformat()
        }

        if copy_to_content:
            # Asset in content-Verzeichnis kopieren
            content_dir = os.path.join("content", f"slide_{self.slide_id}_assets")
            os.makedirs(content_dir, exist_ok=True)
            
            dest_path = os.path.join(content_dir, asset_info['filename'])
            shutil.copy2(asset_path, dest_path)
            asset_info['content_path'] = dest_path
            logger.info(f"Asset kopiert: {asset_path} -> {dest_path}")
        else:
            # Nur Referenz speichern
            asset_info['content_path'] = asset_path

        self.assets.append(asset_info)
        self.modified_at = datetime.now()
        return asset_info

    def to_dict(self):
        """Konvertiert zu Dictionary für JSON-Serialisierung"""
        return {
            'slide_id': self.slide_id,
            'title': self.title,
            'content': self.content,
            'layout': self.layout,
            'canvas_elements': self.canvas_elements,
            'assets': self.assets,
            'config_data': self.config_data,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'extra_data': self.extra_data  # Legacy
        }
    
    @classmethod
    def from_dict(cls, data):
        """Erstellt Instanz aus Dictionary"""
        slide = cls(
            data.get('slide_id', 1),
            data.get('title', ''),
            data.get('content', ''),
            data.get('layout', 'text')
        )
        
        slide.canvas_elements = data.get('canvas_elements', [])
        slide.assets = data.get('assets', [])
        slide.config_data = data.get('config_data', {})
        slide.extra_data = data.get('extra_data', {})
        
        # Zeitstempel wiederherstellen
        try:
            slide.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
            slide.modified_at = datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        except:
            slide.created_at = datetime.now()
            slide.modified_at = datetime.now()
            
        return slide


class AssetManager:
    """Verwaltet Assets aus verschiedenen Quellen"""
    
    def __init__(self):
        self.assets_dir = "assets"
        self.content_dir = "content"
        self.supported_formats = {
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg'],
            'icons': ['.png', '.svg', '.ico'],
            'documents': ['.pdf', '.txt', '.md']
        }
    
    def scan_assets(self):
        """Scannt alle verfügbaren Assets"""
        assets = {
            'ui_elements': [],
            'content_images': [],
            'corporate_assets': [],
            'user_uploads': []
        }
        
        # Assets-Verzeichnis scannen
        if os.path.exists(self.assets_dir):
            for root, dirs, files in os.walk(self.assets_dir):
                for file in files:
                    if self._is_supported_format(file):
                        filepath = os.path.join(root, file)
                        asset_info = self._create_asset_info(filepath, 'corporate')
                        
                        if 'icon' in file.lower() or 'ui' in root.lower():
                            assets['ui_elements'].append(asset_info)
                        else:
                            assets['corporate_assets'].append(asset_info)
        
        # Content-Verzeichnis scannen
        if os.path.exists(self.content_dir):
            for root, dirs, files in os.walk(self.content_dir):
                for file in files:
                    if self._is_supported_format(file):
                        filepath = os.path.join(root, file)
                        asset_info = self._create_asset_info(filepath, 'content')
                        assets['content_images'].append(asset_info)
        
        return assets
    
    def _is_supported_format(self, filename):
        """Prüft ob Dateiformat unterstützt wird"""
        ext = os.path.splitext(filename)[1].lower()
        for formats in self.supported_formats.values():
            if ext in formats:
                return True
        return False
    
    def _create_asset_info(self, filepath, source):
        """Erstellt Asset-Information"""
        stat = os.stat(filepath)
        return {
            'path': filepath,
            'filename': os.path.basename(filepath),
            'source': source,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': os.path.splitext(filepath)[1].lower()
        }


class EnhancedContentManager:
    """Erweiterte ContentManager-Klasse"""
    
    def __init__(self):
        self.slides = {}
        self.content_observers = []
        self.asset_manager = AssetManager()
        self.load_default_content()
    
    def load_default_content(self):
        """Lädt Standard-Inhalte"""
        default_slides = {
            1: SlideData(1, "BumbleB - Das automatisierte Shuttle", 
                        "Schonmal ein automatisiert Shuttle gesehen, das aussieht wie eine Hummel?\n\nShuttle fährt los von Bushaltestelle an Bahnhof..."),
            2: SlideData(2, "BumbleB - Wie die Hummel fährt",
                        "Wie die Hummel ihre Flügel nutzt, so nutzt unser BumbleB innovative Technologie für autonomes Fahren."),
            3: SlideData(3, "Einsatzgebiete und Vorteile",
                        "Vielseitige Einsatzmöglichkeiten in urbanen Gebieten für nachhaltigen Transport."),
            4: SlideData(4, "Sicherheitssysteme",
                        "Moderne Sicherheitssysteme gewährleisten maximale Sicherheit für alle Passagiere."),
            5: SlideData(5, "Nachhaltigkeit & Umwelt",
                        "Nachhaltiger Transport für eine grüne Zukunft - umweltfreundlich und effizient.")
        }
        
        for slide_id, slide_data in default_slides.items():
            if slide_id not in self.slides:
                self.slides[slide_id] = slide_data
    
    def create_slide(self, slide_id, title="", content="", layout="text"):
        """Erstellt neuen Slide"""
        self.slides[slide_id] = SlideData(slide_id, title, content, layout)
        self.notify_observers(slide_id, self.slides[slide_id])
        logger.info(f"Slide {slide_id} erstellt")
        return True
    
    def update_slide_content(self, slide_id, title, content, extra_data=None):
        """Aktualisiert Slide-Inhalt"""
        if slide_id not in self.slides:
            self.slides[slide_id] = SlideData(slide_id)
        
        slide = self.slides[slide_id]
        slide.title = title
        slide.content = content
        slide.modified_at = datetime.now()
        
        if extra_data:
            slide.extra_data.update(extra_data)
            # Canvas-Elemente aus extra_data extrahieren
            if 'canvas_elements' in extra_data:
                slide.canvas_elements = extra_data['canvas_elements']
        
        self.notify_observers(slide_id, slide)
        logger.debug(f"Slide {slide_id} aktualisiert: {title[:30]}...")
        return True
    
    def add_asset_to_slide(self, slide_id, asset_path, asset_type='image'):
        """Fügt Asset zu Slide hinzu"""
        if slide_id not in self.slides:
            logger.error(f"Slide {slide_id} nicht gefunden")
            return None
        
        slide = self.slides[slide_id]
        
        # Bestimme ob Asset kopiert werden soll
        copy_asset = asset_path.startswith('assets/')  # Assets kopieren
        
        asset_info = slide.add_asset(asset_path, asset_type, copy_asset)
        
        if asset_info:
            self.notify_observers(slide_id, slide, 'asset_added')
            logger.info(f"Asset zu Slide {slide_id} hinzugefügt: {asset_info['filename']}")
        
        return asset_info
    
    def get_slide(self, slide_id):
        """Gibt Slide zurück"""
        return self.slides.get(slide_id)
    
    def get_all_slides(self):
        """Gibt alle Slides zurück"""
        return self.slides.copy()
    
    def get_slide_count(self):
        """Gibt Anzahl der Slides zurück"""
        return len(self.slides)
    
    def add_observer(self, callback):
        """Fügt Observer hinzu"""
        self.content_observers.append(callback)
    
    def notify_observers(self, slide_id, slide_data, action='update'):
        """Benachrichtigt Observer"""
        for callback in self.content_observers:
            try:
                callback(slide_id, slide_data, action)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    def save_to_file(self, filepath=None):
        """Speichert alle Slides in JSON-Datei"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"presentations/presentation_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = {
            'presentation': {
                'title': 'BumbleB Präsentation',
                'created_at': datetime.now().isoformat(),
                'version': '2.0'
            },
            'slides': {str(k): v.to_dict() for k, v in self.slides.items()}
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Präsentation gespeichert: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            return None
    
    def load_from_file(self, filepath):
        """Lädt Slides aus JSON-Datei"""
        if not os.path.exists(filepath):
            logger.error(f"Datei nicht gefunden: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'slides' in data:
                self.slides.clear()
                for slide_id_str, slide_data in data['slides'].items():
                    slide_id = int(slide_id_str)
                    self.slides[slide_id] = SlideData.from_dict(slide_data)
                
                # Alle Observer benachrichtigen
                for slide_id, slide_data in self.slides.items():
                    self.notify_observers(slide_id, slide_data, action='load')
                
                logger.info(f"Präsentation geladen: {filepath} ({len(self.slides)} Slides)")
                return True
        except Exception as e:
            logger.error(f"Fehler beim Laden: {e}")
            return False
    
    def get_available_assets(self):
        """Gibt alle verfügbaren Assets zurück"""
        return self.asset_manager.scan_assets()

# Globale Instanz (ersetzt die alte)
content_manager = EnhancedContentManager()
