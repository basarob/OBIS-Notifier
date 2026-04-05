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
from services.browser import BrowserService
from services.pdf_parser import PDFParserService
from services.storage import ProfileStorageService
import os

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

class LoginWorker(QThread):
    """
    Arka planda BrowserService ile giriş dener ve profil bilgilerini çeker.
    """
    result_signal = pyqtSignal(bool, str) # success, message
    status_signal = pyqtSignal(str) # UI durum bilgisini günceller

    def __init__(self, user, pwd):
        super().__init__()
        self.user = user
        self.pwd = pwd

    def run(self):
        try:
            # .Tarayıcıyı headless (görünmez) başlat
            browser = BrowserService(headless=True)
            browser.start_browser()
            
            # Login dene
            is_success = browser.login(self.user, self.pwd)
            
            if is_success:
                # Başarılı girişten sonra profile verisini kontrol et
                profile_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'OBISNotifier')
                os.makedirs(profile_dir, exist_ok=True)
                profile_file = os.path.join(profile_dir, 'profile.json')
                
                if not os.path.exists(profile_file):
                    self.status_signal.emit("Profil Bilgileri Alınıyor...")
                    try:
                        logging.info("Bilgileri çekme işlemi başlatılıyor...")
                        pdf_path = browser.download_graduation_pdf()
                        if pdf_path and os.path.exists(pdf_path):
                            logging.info(f"PDF başarıyla indi: {pdf_path}")
                            
                            parser_service = PDFParserService()
                            storage_service = ProfileStorageService(profile_file)
                            
                            parsed_data = parser_service.extract_graduation_data(pdf_path)

                            if storage_service.save_profile_data(parsed_data):
                                logging.info("Profil JSON dosyasına başarıyla kaydedildi!")
                            else:
                                logging.error("Profil JSON kaydedilemedi!")
                            
                            try:
                                os.remove(pdf_path)
                                logging.info("PDF dosyası silindi.")
                            except OSError:
                                logging.error("PDF dosyası silinemedi!")
                        else:
                            logging.error("PDF yolu alınamadı veya dosya mevcut değil!")

                    except Exception as pdf_err:
                        logging.error(f"Bilgileri çekme sırasında hata: {pdf_err}")
                        
                browser.close_browser()
                self.result_signal.emit(True, "Giriş Başarılı! Yönlendiriliyorsunuz...")
            else:
                browser.close_browser()
                self.result_signal.emit(False, "Giriş Başarısız! Lütfen bilgilerinizi kontrol ediniz.")
                
        except Exception as e:
            self.result_signal.emit(False, f"Sistem hatası: {str(e)}")