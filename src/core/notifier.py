"""
BU DOSYA: Uygulamanın beyni (Core) olarak çalışır.
Diğer servisleri (Browser, Notification, Storage) koordine eder.
"""

import logging
import time
import os
import schedule
from typing import Dict, Any, Optional
from datetime import datetime

# Servisler
from ..services.browser import BrowserService
from ..services.grades import GradeService
from ..services.notification import NotificationService
from ..services.storage import GradeStorageService
from ..utils.system import get_user_data_dir

class OBISNotifier:
    """
    Ana kontrol sınıfı. Servisleri başlatır ve akışı yönetir.
    Facade Design Pattern benzeri bir yapı sunar.
    """
    
    def __init__(self, settings: Dict[str, Any]) -> None:
        self.settings = settings
        self.running = True
        
        # --- Ayarlar ---
        self.student_id = settings.get("student_id", "")
        self.password = settings.get("obis_password", "")
        self.semester = settings.get("semester", "")
        self.interval = int(settings.get("check_interval", 20))
        self.browser_type = settings.get("browser", "chromium")
        self.stop_on_failures = settings.get("stop_on_failures", True)
        
        # --- Servislerin Başlatılması (Dependency Injection) ---
        
        # 1. Dosya Kayıt Servisi
        json_path = os.path.join(get_user_data_dir(), "grades_data.json")
        self.storage_service = GradeStorageService(json_path)
        
        # 2. Bildirim Servisi
        self.notification_service = NotificationService(
            sender_email=settings.get("sender_email", ""),
            sender_password=settings.get("gmail_app_password", ""),
            notification_methods=settings.get("notification_methods", ["email"]),
            notification_callback=settings.get("notification_callback", None)
        )
        
        # 3. Not İşleme Servisi
        self.grade_service = GradeService()
        
        # 4. Tarayıcı Servisi (Henüz başlatılmaz, ihtiyaç olunca açılır)
        self.browser_service = BrowserService(
            browser_type=self.browser_type,
            headless=True
        )

        # Durum Takibi
        self.check_count = 1
        self.consecutive_failures = 0
        self.status_callback = settings.get("status_callback", None)
        self.on_stop_callback = settings.get("on_stop_callback", None)

    def check_grades_once(self) -> bool:
        """
        .Tek bir kontrol döngüsünü yürütür:
        .Tarayıcı Aç -> Giriş -> Notları Al -> Kapat -> Karşılaştır -> Bildir
        """
        try:
            logging.info(f"====== {self.check_count}. KONTROL ======")
            self.check_count += 1
            
            # --- Adım 1: Tarayıcı İşlemleri ---
            self.browser_service.start_browser()
            
            if self.browser_service.login(self.student_id, self.password):
                # t Başarılı giriş
                self.consecutive_failures = 0 
                
                if self.browser_service.navigate_to_grades(self.semester):
                    html_content = self.browser_service.get_page_content()
                    
                    # --- Adım 2: Veri İşleme ---
                    new_grades = self.grade_service.parse_grades(html_content)
                    
                    if new_grades is not None:
                        # --- Adım 3: Karşılaştırma ve Kayıt ---
                        old_data = self.storage_service.load_previous_grades()
                        changes, status_msg = self.grade_service.compare_grades(old_data, new_grades)
                        
                        if changes:
                            # --- Adım 4: Bildirim ---
                            self.notification_service.notify_changes(changes)
                        else:
                            logging.info("Herhangi bir değişiklik bulunamadı.")
                        
                        self.storage_service.save_grades(new_grades)
                        
                        if self.status_callback:
                             timestamp = datetime.now().strftime('%H:%M')
                             self.status_callback(f"Son Kontrol: {timestamp} (Başarılı)")
                             
                        return True
                    else:
                        logging.error("Notlar çekilemedi! (Liste boş olabilir)")
                else:
                    logging.error("Notlar sayfasına gidilemedi.")
            else:
                # t Giriş başarısız
                self.consecutive_failures += 1
                logging.error(f"Giriş yapılamadı! ({self.consecutive_failures})")
                
                if self.stop_on_failures and self.consecutive_failures >= 3:
                     logging.error("3 ardışık başarısızlık. Durduruluyor.")
                     self.notification_service.send_failure_notification()
                     self.stop_monitoring()

            if self.status_callback: 
                self.status_callback("Son Kontrol: Başarısız")
            return False

        except Exception as e:
            logging.error(f"Kontrol sırasında genel hata: {str(e)}")
            return False
            
        finally:
            # Kaynakları temizle
            self.browser_service.close_browser()

    def start_monitoring(self) -> None:
        """Sürekli izleme döngüsünü başlatır."""
        logging.info("Sürekli izleme başlatılıyor...")
        
        # İlk kontrolü hemen yap
        self.check_grades_once()
        
        schedule.every(self.interval).minutes.do(self.check_grades_once)

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1) # CPU kullanımını düşürmek için kısa bekleme
        except KeyboardInterrupt:
            logging.info("İzleme durduruldu.")
            self.running = False

    def stop_monitoring(self) -> None:
        """İzlemeyi sonlandırır."""
        self.running = False
        schedule.clear()
        if self.on_stop_callback:
            self.on_stop_callback()

    def send_test_notification(self) -> None:
        """Kullanıcı isteğiyle test bildirimi gönderir (Wrapper)."""
        self.notification_service.send_test_notification()
