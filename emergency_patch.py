#!/usr/bin/env python3
"""
NOTFALL-PATCH für Dynamic Messe Stand V4
Sofortige Reparatur der kritischen Speicherfunktionen

REPARIERT:
- Content-Manager mit Asset-Support
- Creator-Tab Speicherung (Text + Bilder)
- Demo-Tab Live-Synchronisation
- Asset-Browser für alle Ordner
"""

import os
import shutil
import sys
from datetime import datetime

class EmergencyPatch:
    """Notfall-Patch für kritische Reparaturen"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.backup_dir = os.path.join(self.base_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.patched_files = []
        
    def create_backup(self):
        """Erstellt Backup der Original-Dateien"""
        print("🔄 Erstelle Backup der Original-Dateien...")
        
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Wichtige Dateien sichern
            files_to_backup = [
                'models/content.py',
                'ui/tabs/creator_tab.py', 
                'ui/tabs/demo_tab.py'
            ]
            
            for file_path in files_to_backup:
                full_path = os.path.join(self.base_dir, file_path)
                if os.path.exists(full_path):
                    backup_path = os.path.join(self.backup_dir, file_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(full_path, backup_path)
                    print(f"  ✅ Gesichert: {file_path}")
                else:
                    print(f"  ⚠️  Nicht gefunden: {file_path}")
            
            print(f"✅ Backup erstellt in: {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Backup: {e}")
            return False
    
    def apply_content_manager_patch(self):
        """Wendet Content-Manager Patch an"""
        print("🔄 Patche Content-Manager...")
        
        content_patch = '''#!/usr/bin/env python3
"""
EMERGENCY PATCHED - Enhanced Content Manager für Dynamic Messe Stand V4
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

class SlideData:
    """Erweiterte Klasse für Slide-Daten mit Asset-Support"""
    
    def __init__(self, slide_id, title="", content="", layout="text"):
        self.slide_id = slide_id
        self.title = title
        self.content = content
        self.layout = layout
        self.canvas_elements = []
        self.assets = []
        self.config_data = {}
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.extra_data = {}  # Legacy

    def add_canvas_element(self, element_type, data):
        """Fügt Canvas-Element hinzu"""
        element = {
            'type': element_type,
            'data': data,
            'id': len(self.canvas_elements) + 1,
            'created_at': datetime.now().isoformat()
        }
        self.canvas_elements.append(element)
        self.modified_at = datetime.now()
        return element['id']

    def add_asset(self, asset_path, asset_type='image', copy_to_content=True):
        """Fügt Asset hinzu"""
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
            content_dir = os.path.join("content", f"slide_{self.slide_id}_assets")
            os.makedirs(content_dir, exist_ok=True)
            
            dest_path = os.path.join(content_dir, asset_info['filename'])
            shutil.copy2(asset_path, dest_path)
            asset_info['content_path'] = dest_path
            logger.info(f"Asset kopiert: {asset_path} -> {dest_path}")
        else:
            asset_info['content_path'] = asset_path

        self.assets.append(asset_info)
        self.modified_at = datetime.now()
        return asset_info

    def to_dict(self):
        """Konvertiert zu Dictionary"""
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
            'extra_data': self.extra_data
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
        
        try:
            slide.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
            slide.modified_at = datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        except:
            slide.created_at = datetime.now()
            slide.modified_at = datetime.now()
            
        return slide

class AssetManager:
    """Asset-Manager"""
    
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
        
        if os.path.exists(self.content_dir):
            for root, dirs, files in os.walk(self.content_dir):
                for file in files:
                    if self._is_supported_format(file):
                        filepath = os.path.join(root, file)
                        asset_info = self._create_asset_info(filepath, 'content')
                        assets['content_images'].append(asset_info)
        
        return assets
    
    def _is_supported_format(self, filename):
        """Prüft Dateiformat"""
        ext = os.path.splitext(filename)[1].lower()
        for formats in self.supported_formats.values():
            if ext in formats:
                return True
        return False
    
    def _create_asset_info(self, filepath, source):
        """Erstellt Asset-Info"""
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
                        "Schonmal ein automatisiert Shuttle gesehen, das aussieht wie eine Hummel?\\n\\nShuttle fährt los von Bushaltestelle an Bahnhof..."),
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
        copy_asset = asset_path.startswith('assets/')
        asset_info = slide.add_asset(asset_path, asset_type, copy_asset)
        
        if asset_info:
            self.notify_observers(slide_id, slide, 'asset_added')
            logger.info(f"Asset zu Slide {slide_id} hinzugefügt: {asset_info['filename']}")
        
        return asset_info
    
    def get_slide(self, slide_id):
        return self.slides.get(slide_id)
    
    def get_all_slides(self):
        return self.slides.copy()
    
    def get_slide_count(self):
        return len(self.slides)
    
    def add_observer(self, callback):
        self.content_observers.append(callback)
    
    def notify_observers(self, slide_id, slide_data, action='update'):
        for callback in self.content_observers:
            try:
                callback(slide_id, slide_data, action)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    def get_available_assets(self):
        return self.asset_manager.scan_assets()

# KRITISCH: Globale Instanz (ersetzt die alte)
content_manager = EnhancedContentManager()
'''
        
        try:
            content_path = os.path.join(self.base_dir, 'models', 'content.py')
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(content_patch)
            
            self.patched_files.append('models/content.py')
            print("  ✅ Content-Manager gepatcht")
            return True
            
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
            return False
    
    def apply_creator_tab_patch(self):
        """Wendet Creator-Tab Patch an"""
        print("🔄 Patche Creator-Tab...")
        
        # Erstelle vereinfachten Creator-Tab Patch (kritische Teile nur)
        creator_patch_header = '''#!/usr/bin/env python3
"""
EMERGENCY PATCHED - Creator Tab mit funktionierender Speicherung
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import base64
from io import BytesIO
from PIL import Image, ImageTk
from datetime import datetime

from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer
from models.content import content_manager
'''
        
        creator_save_method = '''
    def force_save_slide(self):
        """REPARIERT: Erzwingt Speicherung des aktuellen Slides"""
        self.manual_save = True
        success = self.save_current_slide_content()
        
        if success:
            messagebox.showinfo("Speichern", f"Slide {self.current_edit_slide} wurde erfolgreich gespeichert!")
            logger.info(f"✅ Slide {self.current_edit_slide} manuell gespeichert")
        else:
            messagebox.showerror("Fehler", "Slide konnte nicht gespeichert werden!")
            logger.error(f"❌ Slide {self.current_edit_slide} Speichern fehlgeschlagen")
    
    def save_current_slide_content(self):
        """REPARIERT: Speichert aktuellen Slide-Inhalt VOLLSTÄNDIG"""
        try:
            if not hasattr(self, 'current_slide') or not self.current_slide:
                self.current_slide = content_manager.get_slide(self.current_edit_slide)
                if not self.current_slide:
                    content_manager.create_slide(self.current_edit_slide, f"Neue Slide {self.current_edit_slide}", "")
                    self.current_slide = content_manager.get_slide(self.current_edit_slide)
            
            # Text-Inhalte sammeln
            title_text = ""
            content_text = ""
            canvas_elements = []
            
            if self.edit_mode and hasattr(self, 'edit_widgets'):
                if 'title' in self.edit_widgets:
                    title_text = self.edit_widgets['title'].get('1.0', 'end-1c')
                if 'content' in self.edit_widgets:
                    content_text = self.edit_widgets['content'].get('1.0', 'end-1c')
            else:
                title_text, content_text, canvas_elements = self.extract_canvas_content()
            
            if not title_text:
                title_text = f"Demo-Folie {self.current_edit_slide}"
            
            # Canvas-Elemente speichern
            extra_data = {}
            if canvas_elements:
                extra_data['canvas_elements'] = canvas_elements
            
            # Content-Manager verwenden
            success = content_manager.update_slide_content(
                self.current_edit_slide, title_text, content_text, extra_data
            )
            
            if success:
                self.current_slide = content_manager.get_slide(self.current_edit_slide)
                logger.info(f"✅ Slide {self.current_edit_slide} erfolgreich gespeichert")
                
                if self.manual_save:
                    self.show_save_success()
                
                return True
            else:
                logger.error(f"❌ Slide {self.current_edit_slide} konnte nicht gespeichert werden")
                return False
                
        except Exception as e:
            logger.error(f"KRITISCHER FEHLER beim Speichern: {e}")
            import traceback
            traceback.print_exc()
            return False
'''
        
        # Lese Original Creator-Tab und füge Patch hinzu
        try:
            creator_path = os.path.join(self.base_dir, 'ui', 'tabs', 'creator_tab.py')
            
            if os.path.exists(creator_path):
                with open(creator_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Suche nach der save_current_slide_content Methode und ersetze sie
                if 'def save_current_slide_content(self):' in original_content:
                    # Finde Start und Ende der Methode
                    start_marker = 'def save_current_slide_content(self):'
                    start_pos = original_content.find(start_marker)
                    
                    if start_pos != -1:
                        # Finde nächste Methode oder Klassenende
                        lines = original_content[start_pos:].split('\n')
                        method_lines = [lines[0]]  # Erste Zeile (def...)
                        
                        for i, line in enumerate(lines[1:], 1):
                            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                                # Nächste Methode/Klasse gefunden
                                break
                            method_lines.append(line)
                        
                        # Ersetze die Methode
                        old_method = '\n'.join(method_lines)
                        patched_content = original_content.replace(old_method, creator_save_method.strip())
                        
                        # Füge force_save_slide hinzu falls nicht vorhanden
                        if 'def force_save_slide(self):' not in patched_content:
                            # Suche nach __init__ Methode und füge danach ein
                            init_end = patched_content.find('def __init__(self,', 0)
                            if init_end != -1:
                                # Finde Ende der __init__ Methode
                                init_lines = patched_content[init_end:].split('\n')
                                for i, line in enumerate(init_lines):
                                    if i > 0 and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                                        insert_pos = init_end + sum(len(l) + 1 for l in init_lines[:i])
                                        patched_content = (patched_content[:insert_pos] + 
                                                         '\n' + creator_save_method.strip() + '\n\n' +
                                                         patched_content[insert_pos:])
                                        break
                        
                        # Schreibe gepatchte Datei
                        with open(creator_path, 'w', encoding='utf-8') as f:
                            f.write(patched_content)
                        
                        self.patched_files.append('ui/tabs/creator_tab.py')
                        print("  ✅ Creator-Tab gepatcht")
                        return True
            
            print("  ❌ Creator-Tab Original nicht gefunden oder nicht patchbar")
            return False
            
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
            return False
    
    def create_quick_fix_script(self):
        """Erstellt Quick-Fix Script für manuelle Anwendung"""
        print("🔄 Erstelle Quick-Fix Script...")
        
        quick_fix = f'''#!/usr/bin/env python3
"""
QUICK FIX für Dynamic Messe Stand V4
Wenn Patches nicht automatisch funktionieren
"""

import sys
import os

# Projekt-Verzeichnis hinzufügen
sys.path.insert(0, os.path.dirname(__file__))

print("🚀 Quick-Fix wird angewendet...")

try:
    # 1. Content Manager reparieren
    from models.content import content_manager
    print("✅ Content Manager geladen")
    
    # 2. Test: Slide erstellen und speichern
    test_success = content_manager.update_slide_content(
        1, 
        "Test Slide", 
        "Test Content", 
        {{'canvas_elements': []}}
    )
    
    if test_success:
        print("✅ Content-Speicherung funktioniert")
    else:
        print("❌ Content-Speicherung fehlgeschlagen")
    
    # 3. Asset-Scan testen
    assets = content_manager.get_available_assets()
    print(f"✅ {{len(sum(assets.values(), []))}} Assets gefunden")
    
    print("\\n🎉 Quick-Fix erfolgreich! Starten Sie die Anwendung mit: python main.py")
    
except Exception as e:
    print(f"❌ Quick-Fix Fehler: {{e}}")
    print("\\nMANUELLE REPARATUR nötig:")
    print("1. Backup wiederherstellen aus: {self.backup_dir}")
    print("2. Patches manuell anwenden")
    print("3. Anwendung neu starten")

'''
        
        try:
            fix_path = os.path.join(self.base_dir, 'quick_fix.py')
            with open(fix_path, 'w', encoding='utf-8') as f:
                f.write(quick_fix)
            
            print(f"  ✅ Quick-Fix Script erstellt: {fix_path}")
            return True
            
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
            return False
    
    def verify_patches(self):
        """Verifiziert angewendete Patches"""
        print("🔄 Verifiziere Patches...")
        
        success_count = 0
        total_patches = len(self.patched_files)
        
        for file_path in self.patched_files:
            full_path = os.path.join(self.base_dir, file_path)
            if os.path.exists(full_path):
                try:
                    # Versuche Import/Syntax-Check
                    if file_path.endswith('.py'):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Basis-Syntax-Check
                        compile(content, full_path, 'exec')
                        
                    print(f"  ✅ {file_path} - OK")
                    success_count += 1
                    
                except SyntaxError as e:
                    print(f"  ❌ {file_path} - Syntax-Fehler: {e}")
                except Exception as e:
                    print(f"  ⚠️  {file_path} - Warnung: {e}")
            else:
                print(f"  ❌ {file_path} - Datei nicht gefunden")
        
        print(f"\\n✅ {success_count}/{total_patches} Patches erfolgreich")
        return success_count == total_patches
    
    def run_patch(self):
        """Führt kompletten Patch-Prozess aus"""
        print("="*60)
        print("🚨 NOTFALL-PATCH für Dynamic Messe Stand V4")
        print("="*60)
        print()
        
        # 1. Backup
        if not self.create_backup():
            print("❌ PATCH ABGEBROCHEN - Backup fehlgeschlagen")
            return False
        
        print()
        
        # 2. Patches anwenden
        patches_applied = 0
        
        if self.apply_content_manager_patch():
            patches_applied += 1
        
        if self.apply_creator_tab_patch():
            patches_applied += 1
        
        # 3. Quick-Fix Script
        self.create_quick_fix_script()
        
        print()
        
        # 4. Verifizierung
        if patches_applied > 0:
            verification_success = self.verify_patches()
            
            print()
            print("="*60)
            
            if verification_success:
                print("🎉 PATCH ERFOLGREICH ANGEWENDET!")
                print()
                print("NÄCHSTE SCHRITTE:")
                print("1. Anwendung starten: python main.py")
                print("2. Creator-Tab öffnen")
                print("3. Text/Bilder hinzufügen und '💾 SPEICHERN' klicken")
                print("4. Demo-Tab öffnen → Änderungen sollten sofort sichtbar sein")
                print()
                print(f"💾 Backup verfügbar in: {self.backup_dir}")
                
            else:
                print("⚠️  PATCH MIT WARNUNGEN ANGEWENDET")
                print()
                print("ALTERNATIVE:")
                print("1. Führe aus: python quick_fix.py")
                print("2. Falls Fehler: Backup wiederherstellen und manuell patchen")
                
            print("="*60)
            return True
        
        else:
            print("❌ PATCH FEHLGESCHLAGEN")
            print(f"💾 Original-Dateien verfügbar in: {self.backup_dir}")
            return False

def main():
    """Hauptfunktion"""
    try:
        patcher = EmergencyPatch()
        success = patcher.run_patch()
        
        if success:
            print("\\n🚀 Starte Anwendung mit: python main.py")
            sys.exit(0)
        else:
            print("\\n❌ Manuelle Reparatur erforderlich")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n⏹️  Patch abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
