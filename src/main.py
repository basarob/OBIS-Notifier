"""
BU DOSYA: Uygulamanın Başlangıç Noktasıdır (Entry Point).
Sadece UI uygulamasını (MainWindow) başlatır.
"""

import sys
sys.dont_write_bytecode = True  # __pycache__ klasörünü oluşturmaz

import os
import ctypes
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

# Local Imports
from utils.logger_qt import qt_logger
from ui.main_window import MainWindow
from ui.styles.theme import OBISFonts

# Playwright tarayıcı dosyalarının merkezi konumu.
_playwright_dir = os.path.join(os.getenv('LOCALAPPDATA', ''), "OBISNotifier", "Playwright")
os.makedirs(_playwright_dir, exist_ok=True)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _playwright_dir

def setup_logging():
    """Logging yapılandırmasını başlatır."""
    
    # Log Klasörü: %LOCALAPPDATA%/OBISNotifier
    app_data = os.getenv('LOCALAPPDATA')
    log_dir = os.path.join(app_data, "OBISNotifier")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "obis_log.log")
    
    # Root Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Duplicate Handler Önlemi
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 1. Dosya Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)
    
    # 2. Qt Signal Handler (UI için)
    logger.addHandler(qt_logger)

def main():
    setup_logging() # Logları başlat
    
    # Windows Taskbar Icon Fix
    try:
        myappid = 'OBIS.Notifier.v3.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Global Paths
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # Application Icon
    icon_path = os.path.join(base_path, "images", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Font Kurulumu
    font_family = OBISFonts.init_fonts()
    app.setFont(QFont(font_family, 10))

    # Global QSS (Stil) Dosyasını Yükle
    qss_path = os.path.join(base_path, "ui", "styles", "global.qss")
    try:
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
    except Exception as e:
        logging.error(f"Global QSS yuklenemedi: {e}")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()