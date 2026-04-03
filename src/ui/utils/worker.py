"""
BU DOSYA: Arka plan işlemlerini (Worker Thread) yönetir.
Uzun süren UI-Bloke edici işlemleri (Not kontrolü, E-posta testi vb.)
ayrı bir thread üzerinde asenkron olarak yürüterek ana döngüyü rahatlatır.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import time
import logging

# Core mantığı
try:
    from core.notifier import OBISNotifier
except ImportError:
    OBISNotifier = None

from services.notification import NotificationService

class CheckWorker(QThread):
    """
    Arka planda tek bir not kontrol döngüsünü çalıştıran QThread.
    Her çalıştırıldığında OBISNotifier.check_grades_once() metodunu çalıştırır
    ve sonucunu sinyal ile Dashboard'a bildirir.
    """
    # Sinyal: (success: bool, should_stop: bool, changes: list, message: str, elapsed: float)
    check_finished = pyqtSignal(bool, bool, list, str, float)

    def __init__(self, notifier: 'OBISNotifier'):
        super().__init__()
        self.notifier = notifier

    def run(self):
        """Thread'in ana çalışma noktası. Tek bir kontrol döngüsü yürütür."""
        start_time = time.time()
        try:
            result = self.notifier.check_grades_once()
            elapsed = time.time() - start_time
            self.check_finished.emit(
                result.get("success", False),
                result.get("should_stop", False),
                result.get("changes", []),
                result.get("message", ""),
                elapsed
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logging.error(f"CheckWorker beklenmeyen hata: {e}")
            self.check_finished.emit(False, False, [], str(e), elapsed)

class TestMailWorker(QThread):
    """
    E-Posta bildirim sistemini asenkron test eden QThread sınıfı.
    """
    result_signal = pyqtSignal(bool, str)

    def __init__(self, email: str, pwd: str):
        super().__init__()
        self.email = email
        self.pwd = pwd

    def run(self):
        try:
            service = NotificationService(
                sender_email=self.email,
                sender_password=self.pwd,
                notification_methods=["email"]
            )
            service.send_test_notification()
            self.result_signal.emit(True, "Test bildirimi başarıyla gönderildi.")
        except Exception as e:
            logging.error(f"TestMailWorker Hatası: {e}")
            self.result_signal.emit(False, "Test maili gönderilemedi. Bilgileri/İnternet bağlantınızı kontrol edin.")