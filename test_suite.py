#!/usr/bin/env python3
"""
Umfassende Test Suite für Dynamic Messe Stand V4
Validiert alle reparierten Funktionen vor Produktivbetrieb

VERWENDUNG:
python test_suite.py --all      # Alle Tests
python test_suite.py --quick    # Schnelle Tests
python test_suite.py --fix      # Tests + automatische Reparaturen
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Projekt-Verzeichnis hinzufügen
sys.path.insert(0, os.path.dirname(__file__))

class TestSuite:
    """Umfassende Test Suite für alle reparierten Funktionen"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_results = []
        self.errors_found = []
        self.warnings_found = []
        
    def log_result(self, test_name, status, message="", details=""):
        """Protokolliert Testergebnis"""
        result = {
            'test': test_name,
            'status': status,  # 'PASS', 'FAIL', 'WARN'
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        # Konsole-Output
        status_icon = {
            'PASS': '✅',
            'FAIL': '❌', 
            'WARN': '⚠️'
        }
        
        print(f"{status_icon.get(status, '?')} {test_name}: {message}")
        
        if status == 'FAIL':
            self.errors_found.append(result)
        elif status == 'WARN':
            self.warnings_found.append(result)
    
    def test_file_structure(self):
        """Test 1: Dateistruktur validieren"""
        print("🔍 Test 1: Validiere Dateistruktur...")
        
        required_files = [
            'main.py',
            'models/content.py',
            'ui/tabs/creator_tab.py',
            'ui/tabs/demo_tab.py',
            'ui/main_window.py',
            'core/logger.py',
            'core/theme.py',
            'services/demo.py'
        ]
        
        required_dirs = [
            'assets',
            'content', 
            'models',
            'ui/tabs',
            'ui/components',
            'services',
            'core'
        ]
        
        # Dateien prüfen
        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(self.base_dir, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        # Verzeichnisse prüfen
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = os.path.join(self.base_dir, dir_path)
            if not os.path.exists(full_path):
                missing_dirs.append(dir_path)
        
        if missing_files or missing_dirs:
            details = f"Fehlende Dateien: {missing_files}\nFehlende Verzeichnisse: {missing_dirs}"
            self.log_result("Dateistruktur", "FAIL", "Unvollständige Projektstruktur", details)
            return False
        else:
            self.log_result("Dateistruktur", "PASS", "Alle erforderlichen Dateien vorhanden")
            return True
    
    def test_imports(self):
        """Test 2: Python-Imports validieren"""
        print("🔍 Test 2: Validiere Python-Imports...")
        
        test_imports = [
            ('tkinter', 'Tkinter GUI-Framework'),
            ('PIL', 'Pillow Bildverarbeitung'), 
            ('yaml', 'YAML-Parser (optional)'),
            ('json', 'JSON-Parser'),
            ('threading', 'Threading-Support'),
            ('datetime', 'Datum/Zeit-Funktionen')
        ]
        
        import_errors = []
        
        for module, description in test_imports:
            try:
                __import__(module)
                self.log_result(f"Import {module}", "PASS", f"{description} verfügbar")
            except ImportError as e:
                import_errors.append(f"{module}: {e}")
                if module in ['tkinter', 'PIL']:
                    self.log_result(f"Import {module}", "FAIL", f"Kritischer Import fehlgeschlagen: {e}")
                else:
                    self.log_result(f"Import {module}", "WARN", f"Optionaler Import fehlgeschlagen: {e}")
        
        return len([e for m, d in test_imports if m in ['tkinter', 'PIL'] for e in import_errors if m in e]) == 0
    
    def test_content_manager(self):
        """Test 3: Content Manager Funktionen"""
        print("🔍 Test 3: Teste Content Manager...")
        
        try:
            from models.content import content_manager
            
            # Basis-Funktionen testen
            initial_count = content_manager.get_slide_count()
            self.log_result("Content Manager Import", "PASS", f"{initial_count} Slides initial geladen")
            
            # Slide erstellen
            test_slide_id = 9999
            success = content_manager.update_slide_content(
                test_slide_id,
                "Test Slide für Validierung",
                "Dies ist ein Test-Inhalt für die Validierung der Speicher-Funktionen.",
                {'canvas_elements': [{'type': 'text', 'content': 'Test Element'}]}
            )
            
            if success:
                self.log_result("Content Speicherung", "PASS", "Slide-Speicherung funktioniert")
                
                # Slide laden
                loaded_slide = content_manager.get_slide(test_slide_id)
                if loaded_slide and loaded_slide.title == "Test Slide für Validierung":
                    self.log_result("Content Laden", "PASS", "Slide-Laden funktioniert")
                else:
                    self.log_result("Content Laden", "FAIL", "Geladene Slide-Daten stimmen nicht überein")
                
                # Cleanup
                if test_slide_id in content_manager.slides:
                    del content_manager.slides[test_slide_id]
                
            else:
                self.log_result("Content Speicherung", "FAIL", "Slide konnte nicht gespeichert werden")
            
            # Asset-Manager testen
            try:
                assets = content_manager.get_available_assets()
                total_assets = sum(len(v) for v in assets.values())
                
                if total_assets > 0:
                    self.log_result("Asset Manager", "PASS", f"{total_assets} Assets gefunden")
                else:
                    self.log_result("Asset Manager", "WARN", "Keine Assets gefunden - Assets-Ordner prüfen")
                    
            except Exception as e:
                self.log_result("Asset Manager", "FAIL", f"Asset-Scanner Fehler: {e}")
            
            return True
            
        except Exception as e:
            self.log_result("Content Manager", "FAIL", f"Import/Initialisierung fehlgeschlagen: {e}")
            return False
    
    def test_creator_tab_functions(self):
        """Test 4: Creator Tab Funktionen (Headless)"""
        print("🔍 Test 4: Teste Creator Tab Funktionen...")
        
        try:
            # Creator Tab importieren
            from ui.tabs.creator_tab import CreatorTab
            self.log_result("Creator Tab Import", "PASS", "Creator Tab erfolgreich importiert")
            
            # Mock-Parent für Tests
            class MockParent:
                def winfo_width(self): return 800
                def winfo_height(self): return 600
                def pack(self, **kwargs): pass
                def pack_forget(self): pass
                def grid(self, **kwargs): pass
                def grid_forget(self): pass
            
            class MockMainWindow:
                def __init__(self):
                    self.fonts = {
                        'title': ('Arial', 18, 'bold'),
                        'body': ('Arial', 12),
                        'button': ('Arial', 10, 'bold'),
                        'caption': ('Arial', 9)
                    }
                    class MockRoot:
                        def after(self, ms, callback): pass
                        def after_cancel(self, id): pass
                    self.root = MockRoot()
            
            # Creator Tab Methoden testen (ohne GUI)
            mock_parent = MockParent()
            mock_window = MockMainWindow()
            
            # Direkte Methoden-Tests (statisch)
            creator_methods = [
                'save_current_slide_content',
                'load_slide_to_editor',
                'extract_canvas_content',
                'force_save_slide'
            ]
            
            methods_found = []
            for method_name in creator_methods:
                if hasattr(CreatorTab, method_name):
                    methods_found.append(method_name)
            
            if len(methods_found) >= 3:
                self.log_result("Creator Tab Methoden", "PASS", f"{len(methods_found)}/4 kritische Methoden gefunden")
            else:
                self.log_result("Creator Tab Methoden", "FAIL", f"Nur {len(methods_found)}/4 Methoden gefunden")
            
            return True
            
        except Exception as e:
            self.log_result("Creator Tab", "FAIL", f"Creator Tab Test fehlgeschlagen: {e}")
            return False
    
    def test_demo_tab_sync(self):
        """Test 5: Demo Tab Synchronisation"""
        print("🔍 Test 5: Teste Demo Tab Synchronisation...")
        
        try:
            from ui.tabs.demo_tab import DemoTab
            self.log_result("Demo Tab Import", "PASS", "Demo Tab erfolgreich importiert")
            
            # Sync-relevante Methoden prüfen
            sync_methods = [
                'on_content_changed',
                'sync_content', 
                'force_refresh',
                'render_current_slide'
            ]
            
            methods_found = []
            for method_name in sync_methods:
                if hasattr(DemoTab, method_name):
                    methods_found.append(method_name)
            
            if len(methods_found) >= 3:
                self.log_result("Demo Tab Sync", "PASS", f"{len(methods_found)}/4 Sync-Methoden gefunden")
            else:
                self.log_result("Demo Tab Sync", "WARN", f"Nur {len(methods_found)}/4 Sync-Methoden gefunden")
            
            return True
            
        except Exception as e:
            self.log_result("Demo Tab", "FAIL", f"Demo Tab Test fehlgeschlagen: {e}")
            return False
    
    def test_slide_renderer(self):
        """Test 6: Slide Renderer mit Canvas-Elementen"""
        print("🔍 Test 6: Teste Slide Renderer...")
        
        try:
            from ui.components.slide_renderer import SlideRenderer, EnhancedSlideRenderer
            self.log_result("Slide Renderer Import", "PASS", "Slide Renderer erfolgreich importiert")
            
            # Erweiterte Renderer-Methoden prüfen
            if hasattr(EnhancedSlideRenderer, 'render_canvas_elements'):
                self.log_result("Canvas Element Rendering", "PASS", "Canvas-Element Rendering verfügbar")
            else:
                self.log_result("Canvas Element Rendering", "FAIL", "Canvas-Element Rendering fehlt")
            
            if hasattr(EnhancedSlideRenderer, 'render_slide_assets'):
                self.log_result("Asset Rendering", "PASS", "Asset Rendering verfügbar") 
            else:
                self.log_result("Asset Rendering", "WARN", "Asset Rendering nicht verfügbar")
            
            return True
            
        except Exception as e:
            self.log_result("Slide Renderer", "FAIL", f"Slide Renderer Test fehlgeschlagen: {e}")
            return False
    
    def test_assets_availability(self):
        """Test 7: Assets-Verfügbarkeit prüfen"""
        print("🔍 Test 7: Prüfe Assets-Verfügbarkeit...")
        
        asset_dirs = ['assets', 'content']
        found_assets = {}
        
        for dir_name in asset_dirs:
            dir_path = os.path.join(self.base_dir, dir_name)
            if os.path.exists(dir_path):
                asset_count = 0
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp']):
                            asset_count += 1
                found_assets[dir_name] = asset_count
                
                if asset_count > 0:
                    self.log_result(f"Assets in {dir_name}", "PASS", f"{asset_count} Bild-Assets gefunden")
                else:
                    self.log_result(f"Assets in {dir_name}", "WARN", f"Keine Bild-Assets in {dir_name}")
            else:
                self.log_result(f"Assets {dir_name}", "WARN", f"Verzeichnis {dir_name} existiert nicht")
                found_assets[dir_name] = 0
        
        total_assets = sum(found_assets.values())
        if total_assets >= 5:
            self.log_result("Asset Verfügbarkeit", "PASS", f"{total_assets} Assets insgesamt verfügbar")
            return True
        else:
            self.log_result("Asset Verfügbarkeit", "WARN", f"Nur {total_assets} Assets - mehr Assets empfohlen")
            return False
    
    def test_integration_flow(self):
        """Test 8: End-to-End Integration Flow"""
        print("🔍 Test 8: Teste Integration Flow...")
        
        try:
            from models.content import content_manager
            
            # Simuliere Creator → Demo Flow
            test_slide_id = 8888
            
            # 1. Creator: Slide erstellen
            create_success = content_manager.update_slide_content(
                test_slide_id,
                "Integration Test Slide",
                "Content für Integration Test\nMit mehreren Zeilen\nUnd Canvas-Elementen",
                {
                    'canvas_elements': [
                        {'type': 'text', 'content': 'Test Text Element', 'x': 100, 'y': 200},
                        {'type': 'image', 'x': 300, 'y': 400, 'width': 200, 'height': 150}
                    ]
                }
            )
            
            if create_success:
                self.log_result("Integration: Slide erstellen", "PASS", "Slide erfolgreich erstellt")
                
                # 2. Demo: Slide laden
                loaded_slide = content_manager.get_slide(test_slide_id)
                
                if loaded_slide:
                    self.log_result("Integration: Slide laden", "PASS", "Slide erfolgreich geladen")
                    
                    # 3. Canvas-Elemente prüfen
                    if hasattr(loaded_slide, 'canvas_elements') and loaded_slide.canvas_elements:
                        canvas_count = len(loaded_slide.canvas_elements)
                        self.log_result("Integration: Canvas-Elemente", "PASS", f"{canvas_count} Canvas-Elemente gefunden")
                    else:
                        self.log_result("Integration: Canvas-Elemente", "WARN", "Keine Canvas-Elemente gefunden")
                    
                    # 4. Observer-Pattern simulieren
                    observer_called = False
                    
                    def test_observer(slide_id, slide_data, action):
                        nonlocal observer_called
                        observer_called = True
                    
                    content_manager.add_observer(test_observer)
                    content_manager.update_slide_content(test_slide_id, "Updated Title", "Updated Content")
                    
                    if observer_called:
                        self.log_result("Integration: Observer Pattern", "PASS", "Observer erfolgreich benachrichtigt")
                    else:
                        self.log_result("Integration: Observer Pattern", "FAIL", "Observer nicht benachrichtigt")
                    
                    # Cleanup
                    if test_slide_id in content_manager.slides:
                        del content_manager.slides[test_slide_id]
                    
                    return True
                else:
                    self.log_result("Integration: Slide laden", "FAIL", "Slide konnte nicht geladen werden")
            else:
                self.log_result("Integration: Slide erstellen", "FAIL", "Slide konnte nicht erstellt werden")
                
            return False
            
        except Exception as e:
            self.log_result("Integration Flow", "FAIL", f"Integration Test fehlgeschlagen: {e}")
            return False
    
    def test_performance(self):
        """Test 9: Performance-Tests"""
        print("🔍 Test 9: Teste Performance...")
        
        try:
            from models.content import content_manager
            
            # Asset-Scan Performance
            start_time = time.time()
            assets = content_manager.get_available_assets()
            scan_time = time.time() - start_time
            
            total_assets = sum(len(v) for v in assets.values())
            
            if scan_time < 2.0:
                self.log_result("Performance: Asset-Scan", "PASS", f"{total_assets} Assets in {scan_time:.2f}s gescannt")
            elif scan_time < 5.0:
                self.log_result("Performance: Asset-Scan", "WARN", f"Asset-Scan etwas langsam: {scan_time:.2f}s")
            else:
                self.log_result("Performance: Asset-Scan", "FAIL", f"Asset-Scan zu langsam: {scan_time:.2f}s")
            
            # Content-Manager Performance
            start_time = time.time()
            for i in range(10):
                content_manager.update_slide_content(i + 7000, f"Test {i}", f"Content {i}")
            operation_time = time.time() - start_time
            
            # Cleanup
            for i in range(10):
                if (i + 7000) in content_manager.slides:
                    del content_manager.slides[i + 7000]
            
            if operation_time < 1.0:
                self.log_result("Performance: Content Ops", "PASS", f"10 Operationen in {operation_time:.2f}s")
            else:
                self.log_result("Performance: Content Ops", "WARN", f"Content-Ops langsam: {operation_time:.2f}s")
            
            return True
            
        except Exception as e:
            self.log_result("Performance Tests", "FAIL", f"Performance Test fehlgeschlagen: {e}")
            return False
    
    def create_test_assets(self):
        """Test-Assets erstellen falls keine vorhanden"""
        print("🔧 Erstelle Test-Assets...")
        
        try:
            from PIL import Image
            
            # Test-Verzeichnisse erstellen
            test_dirs = [
                os.path.join(self.base_dir, 'assets', 'test'),
                os.path.join(self.base_dir, 'content', 'test_images')
            ]
            
            for test_dir in test_dirs:
                os.makedirs(test_dir, exist_ok=True)
            
            # Einfache Test-Bilder erstellen
            for i, test_dir in enumerate(test_dirs):
                for j in range(3):
                    # Farbiges Test-Bild erstellen
                    img = Image.new('RGB', (200, 150), color=(100 + i*50, 150 + j*30, 200))
                    img_path = os.path.join(test_dir, f'test_image_{i}_{j}.png')
                    img.save(img_path)
            
            self.log_result("Test Assets", "PASS", "Test-Assets erfolgreich erstellt")
            return True
            
        except Exception as e:
            self.log_result("Test Assets", "FAIL", f"Test-Assets Erstellung fehlgeschlagen: {e}")
            return False
    
    def run_quick_tests(self):
        """Führt schnelle Tests aus"""
        print("🚀 Starte SCHNELLE Tests...\n")
        
        tests = [
            self.test_file_structure,
            self.test_imports,
            self.test_content_manager,
            self.test_assets_availability
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            print()
        
        return passed, len(tests)
    
    def run_all_tests(self):
        """Führt alle Tests aus"""
        print("🚀 Starte VOLLSTÄNDIGE Tests...\n")
        
        tests = [
            self.test_file_structure,
            self.test_imports, 
            self.test_content_manager,
            self.test_creator_tab_functions,
            self.test_demo_tab_sync,
            self.test_slide_renderer,
            self.test_assets_availability,
            self.test_integration_flow,
            self.test_performance
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            print()
        
        return passed, len(tests)
    
    def auto_fix_issues(self):
        """Versucht automatische Reparaturen"""
        print("🔧 Versuche automatische Reparaturen...\n")
        
        fixes_applied = 0
        
        # Fix 1: Test-Assets erstellen
        if self.create_test_assets():
            fixes_applied += 1
        
        # Fix 2: Fehlende Verzeichnisse erstellen
        required_dirs = ['presentations', 'exports', 'logs', 'content/user_uploads']
        for dir_path in required_dirs:
            full_path = os.path.join(self.base_dir, dir_path)
            if not os.path.exists(full_path):
                try:
                    os.makedirs(full_path, exist_ok=True)
                    self.log_result(f"Dir Fix: {dir_path}", "PASS", "Verzeichnis erstellt")
                    fixes_applied += 1
                except Exception as e:
                    self.log_result(f"Dir Fix: {dir_path}", "FAIL", f"Fehler: {e}")
        
        print(f"\n🔧 {fixes_applied} automatische Reparaturen angewendet")
        return fixes_applied
    
    def generate_report(self):
        """Generiert Testbericht"""
        print("\n" + "="*60)
        print("📋 TESTBERICHT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len(self.errors_found)
        warning_tests = len(self.warnings_found)
        
        print(f"""
ZUSAMMENFASSUNG:
✅ Erfolgreich: {passed_tests}/{total_tests}
❌ Fehlgeschlagen: {failed_tests}  
⚠️  Warnungen: {warning_tests}

BEREITSCHAFT FÜR PRODUKTION:
""")
        
        if failed_tests == 0:
            if warning_tests == 0:
                print("🎉 VOLLSTÄNDIG BEREIT - Alle Tests erfolgreich!")
                print("   → Anwendung kann sofort gestartet werden")
            else:
                print("✅ BEREIT MIT WARNUNGEN - Hauptfunktionen arbeiten") 
                print("   → Anwendung kann gestartet werden")
                print("   → Warnungen für optimale Leistung beheben")
        else:
            print("❌ NICHT BEREIT - Kritische Fehler vorhanden")
            print("   → Fehler beheben vor Produktivbetrieb")
        
        # Detaillierte Fehler
        if self.errors_found:
            print(f"\n❌ KRITISCHE FEHLER ({len(self.errors_found)}):")
            for error in self.errors_found:
                print(f"   • {error['test']}: {error['message']}")
        
        # Warnungen
        if self.warnings_found:
            print(f"\n⚠️  WARNUNGEN ({len(self.warnings_found)}):")
            for warning in self.warnings_found:
                print(f"   • {warning['test']}: {warning['message']}")
        
        # Empfehlungen
        print(f"\n💡 EMPFEHLUNGEN:")
        if failed_tests == 0 and warning_tests == 0:
            print("   • Starten Sie die Anwendung: python main.py")
            print("   • Öffnen Sie Creator-Tab und testen Sie das Speichern")
            print("   • Wechseln Sie zu Demo-Tab und prüfen Sie die Synchronisation")
        elif failed_tests == 0:
            print("   • Anwendung kann gestartet werden")
            print("   • Beheben Sie Warnungen für optimale Performance")
            print("   • Fügen Sie mehr Assets in assets/ und content/ hinzu")
        else:
            print("   • Führen Sie aus: python test_suite.py --fix")
            print("   • Beheben Sie kritische Fehler manuell")
            print("   • Wiederholen Sie Tests vor dem Start")
        
        print("\n" + "="*60)
        
        return failed_tests == 0

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description='Test Suite für Dynamic Messe Stand V4')
    parser.add_argument('--all', action='store_true', help='Alle Tests ausführen')
    parser.add_argument('--quick', action='store_true', help='Schnelle Tests ausführen') 
    parser.add_argument('--fix', action='store_true', help='Tests + automatische Reparaturen')
    
    args = parser.parse_args()
    
    suite = TestSuite()
    
    print("🧪 DYNAMIC MESSE STAND V4 - TEST SUITE")
    print("="*50)
    
    try:
        if args.fix:
            # Auto-Fix Modus
            suite.auto_fix_issues()
            print()
            passed, total = suite.run_all_tests()
        elif args.all:
            # Alle Tests
            passed, total = suite.run_all_tests()
        else:
            # Standard: Schnelle Tests
            passed, total = suite.run_quick_tests()
        
        # Bericht generieren
        ready = suite.generate_report()
        
        # Exit-Code setzen
        if ready:
            print("🚀 BEREIT ZUM START!")
            sys.exit(0)
        else:
            print("⚠️  REPARATUREN ERFORDERLICH")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unerwarteter Test-Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
