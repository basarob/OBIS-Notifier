"""
BU DOSYA: Backend servislerini (OBISNotifier) ayrı bir thread
üzerinde çalıştırır. UI'ın donmasını engeller.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any

# Core import (Backend mantığı)
# .try bloğu, tasarım testi yaparken backend olmadan
# UI'ı çalıştırmaya yarar
try:
    from core.notifier import OBISNotifier
except ImportError:
    OBISNotifier = None

class OBISWorker(QThread):
    """
    Arka planda çalışan işçi thread (Worker Thread).
    Backend işlemlerini yürütür ve Sinyaller ile UI'a bilgi taşır.
    """
    log_signal = pyqtSignal(str, str) # level, message
    status_signal = pyqtSignal(bool) # is_running
    finished_signal = pyqtSignal()
    
    def __init__(self, settings: Dict[str, Any]):
        super().__init__()
        self.settings = settings
        self.notifier = None
        self._is_running = False
        
    def run(self):
        """Thread'in ana çalışma döngüsü (Entry Point)."""
        if OBISNotifier is None:
            self.log_signal.emit("ERROR", "Backend core modülleri bulunamadı!")
            return

        self._is_running = True
        self.status_signal.emit(True)
        self.log_signal.emit("INFO", "Worker thread başlatıldı...")
        
        try:
            # Backend'i başlat
            # Geri bildirim (Callback) fonksiyonlarını bağla
            self.settings["status_callback"] = self._on_status_update
            self.settings["notification_callback"] = self._on_notification
            
            self.notifier = OBISNotifier(self.settings)
            self.notifier.start_monitoring() # Bloklayan çağrı (döngü burada başlar)
            
        except Exception as e:
            self.log_signal.emit("ERROR", f"Kritik Hata: {str(e)}")
        finally:
            self._is_running = False
            self.status_signal.emit(False)
            self.log_signal.emit("INFO", "Worker thread durduruldu.")
            
    def stop(self):
        """Thread'i güvenli bir şekilde durdurur."""
        if self.notifier:
            self.notifier.stop_monitoring()
        self.terminate() # Eğer normal durmazsa zorla durdur (tercih edilmez)

    def _on_status_update(self, msg: str):
        """Backend'den gelen durum mesajlarını UI'a iletir."""
        self.log_signal.emit("INFO", msg)

    def _on_notification(self, title, msg):
        """Backend'den gelen bildirimleri UI'a iletir."""
        self.log_signal.emit("SUCCESS", f"{title}: {msg}")