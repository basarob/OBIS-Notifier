"""
BU DOSYA: Uygulamanın beyni (Core) olarak çalışır.
Diğer servisleri (Browser, Notification, Storage) koordine eder.

Yeni mimaride sonsuz döngü (schedule) kullanılmaz.
Dashboard tarafındaki QTimer her döngüde `check_grades_once()` metodunu
bir QThread içinden çağırır. Böylece UI donmaz ve geri sayım Dashboard'da
kontrollü şekilde yönetilir.
"""

import logging
import os
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

# Servisler
from services.browser import BrowserService
from services.grades import GradeService
from services.notification import NotificationService
from services.storage import GradeStorageService
from utils.system import get_user_data_dir


class OBISNotifier:
    """
    Ana kontrol sınıfı. Servisleri başlatır ve tek bir kontrol döngüsünü yürütür.
    Facade Design Pattern benzeri bir yapı sunar.
    """

    def __init__(self, settings: Dict[str, Any]) -> None:
        self.settings = settings

        # --- Ayarlar ---
        self.student_id: str = settings.get("student_id", "")
        self.password: str = settings.get("obis_password", "")
        self.semester: str = settings.get("semester", "")
        self.browser_type: str = settings.get("browser", "chromium")
        self.stop_on_failures: bool = settings.get("stop_on_failures", True)

        # --- Callback'ler (Dashboard Timeline ve bildirim) ---
        # timeline_callback(mesaj: str, tip: str) -> Dashboard timeline'a düşürülecek
        self.timeline_callback: Optional[Callable[[str, str], None]] = settings.get("timeline_callback", None)
        # notification_callback(title: str, message: str) -> Windows Toast bildirimi
        self.notification_callback: Optional[Callable[[str, str], None]] = settings.get("notification_callback", None)

        # --- Servislerin Başlatılması (Dependency Injection) ---

        # 1. Dosya Kayıt Servisi
        json_path = os.path.join(get_user_data_dir(), "grades_data.json")
        self.storage_service = GradeStorageService(json_path)

        # 2. Bildirim Servisi
        self.notification_service = NotificationService(
            sender_email=settings.get("sender_email", ""),
            sender_password=settings.get("gmail_app_password", ""),
            notification_methods=settings.get("notification_methods", ["email"]),
            notification_callback=self.notification_callback
        )

        # 3. Not İşleme Servisi
        self.grade_service = GradeService()

        # 4. Tarayıcı Servisi (Henüz başlatılmaz, ihtiyaç olunca açılır)
        self.browser_service = BrowserService(
            browser_type=self.browser_type,
            headless=True
        )

        # Durum Takibi
        self.consecutive_failures: int = 0

    def _emit_timeline(self, message: str, msg_type: str = "info") -> None:
        """Dashboard timeline'a kritik durum mesajı gönderir (thread-safe sinyal üzerinden)."""
        if self.timeline_callback:
            try:
                self.timeline_callback(message, msg_type)
            except Exception:
                pass  # Sinyal bağlantısı kopmuş olabilir, sessizce geç

    def check_grades_once(self) -> Dict[str, Any]:
        """
        Tek bir kontrol döngüsünü yürütür:
        Tarayıcı Aç -> Giriş -> Notları Al -> Kapat -> Karşılaştır -> Bildir

        Returns:
            Sonuç sözlüğü:
            - success (bool): İşlem başarılı mı
            - should_stop (bool): Art arda hata nedeniyle sistem durmalı mı
            - changes (list): Bulunan değişiklikler (varsa)
            - message (str): Kısa durum açıklaması
        """
        result: Dict[str, Any] = {
            "success": False,
            "should_stop": False,
            "changes": [],
            "message": ""
        }

        try:
            # --- Adım 1: Tarayıcı İşlemleri ---
            self.browser_service.start_browser()

            if self.browser_service.login(self.student_id, self.password):
                # Başarılı giriş -> Hata sayacını sıfırla
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
                            change_count = len(changes)
                            ders_listesi = ", ".join([c["ders"] for c in changes[:3]])
                            timeline_msg = f"{change_count} adet not değişikliği: {ders_listesi}"
                            if change_count > 3:
                                timeline_msg += f" +{change_count - 3} ders daha"

                            self._emit_timeline(timeline_msg, "warn")
                            logging.info(f"{change_count} adet değişiklik tespit edildi!")

                            self.notification_service.notify_changes(changes)
                        else:
                            self._emit_timeline("Kontrol tamamlandı, değişiklik yok.", "info")
                            logging.info("Herhangi bir değişiklik bulunamadı.")

                        self.storage_service.save_grades(new_grades)

                        result["success"] = True
                        result["changes"] = changes
                        result["message"] = status_msg
                        return result
                    else:
                        error_msg = "Not verileri çekilemedi (tablo boş olabilir)."
                        logging.error(error_msg)
                        self._emit_timeline(error_msg, "error")
                        result["message"] = error_msg
                else:
                    error_msg = "Notlar sayfasına gidilemedi."
                    logging.error(error_msg)
                    self._emit_timeline(error_msg, "error")
                    result["message"] = error_msg
            else:
                # Giriş başarısız
                self.consecutive_failures += 1
                error_msg = f"OBİS girişi başarısız! (Ardışık hata: {self.consecutive_failures}/3)"
                logging.error(error_msg)
                self._emit_timeline(error_msg, "error")
                result["message"] = error_msg

                # 3 ardışık başarısızlık kontrolü
                if self.stop_on_failures and self.consecutive_failures >= 3:
                    stop_msg = "3 ardışık başarısız giriş! Sistem güvenlik nedeniyle durduruluyor."
                    logging.error(stop_msg)
                    self._emit_timeline(stop_msg, "error")
                    self.notification_service.send_failure_notification()
                    result["should_stop"] = True

            return result

        except Exception as e:
            error_msg = f"Kontrol sırasında beklenmeyen hata: {str(e)}"
            logging.error(error_msg)
            self._emit_timeline(error_msg, "error")
            self.consecutive_failures += 1
            result["message"] = error_msg

            if self.stop_on_failures and self.consecutive_failures >= 3:
                result["should_stop"] = True
                self._emit_timeline("3 ardışık hata! Sistem durduruluyor.", "error")

            return result

        finally:
            # Kaynakları temizle
            self.browser_service.close_browser()

    def send_test_notification(self) -> None:
        """Kullanıcı isteğiyle test bildirimi gönderir (Wrapper)."""
        self.notification_service.send_test_notification()
