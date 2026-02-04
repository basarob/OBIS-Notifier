"""
BU DOSYA: Python logging modülü ile PyQt6 Arayüzü arasındaki köprüyü kurar.
Loglar 'signal' yoluyla arayüze taşınır.
"""

import logging
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

class QLogHandler(QObject, logging.Handler):
    """
    Log kayıtlarını PyQt sinyaline dönüştüren Handler.
    (Timestamp, Level, Message) formatında sinyal yayar.
    """
    # Sinyal: (timestamp, level_name, message)
    log_signal = pyqtSignal(str, str, str)

    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)
        
        # Formatlayıcı
        formatter = logging.Formatter('%(message)s')
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        """Log kaydı geldiğinde tetiklenir."""
        try:
            msg = self.format(record)
            timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
            level = record.levelname
            
            # Sistem mesajlarını ayırt etmek için özel keyword kontrolü yapılabilir
            # Örn: main.py içinde logger.info("[SYSTEM] ...") şeklinde kullanım varsa
            
            self.log_signal.emit(timestamp, level, msg)
            
        except Exception:
            self.handleError(record)

# Global erişim için tekil (Singleton-like) instance
qt_logger = QLogHandler()