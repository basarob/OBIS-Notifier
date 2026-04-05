"""
BU DOSYA: Kullanıcıya e-posta bildirimi gönderme işlemlerini yönetir.
Kritik hatalar (SMTP hataları vb.) timeline callback üzerinden Dashboard'a bildirilir.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional, Callable
from ui.styles.email_templates import OBISEmailTemplates

class NotificationService:
    """E-posta bildirim işlemlerini yöneten servis sınıfı."""
    
    def __init__(self, 
                 sender_email: str, 
                 sender_password: str, 
                 notification_methods: List[str], 
                 timeline_callback: Optional[Callable[[str, str], None]] = None):
        """
        Args:
            sender_email: Gönderen Gmail adresi
            sender_password: Gmail Uygulama Şifresi
            notification_methods: Seçili yöntemler listesi
            timeline_callback: Dashboard timeline'a mesaj göndermek için callback
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = sender_email 
        self.notification_methods = notification_methods
        self.timeline_callback = timeline_callback

    def _emit_timeline(self, message: str, msg_type: str = "error") -> None:
        """Timeline callback'e mesaj gönderir (varsa)."""
        if self.timeline_callback:
            try:
                self.timeline_callback(message, msg_type)
            except Exception:
                pass

    def send_email(self, subject: str, body: str, is_html: bool = False, suppress_timeline: bool = False) -> None:
        """
        SMTP protokolü ile e-posta gönderir.
        Gmail SMTP sunucusu (smtp.gmail.com:465 SSL) kullanılır.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
        except Exception as e:
            error_msg = f"Mail gönderme hatası: {e}"
            logging.error(error_msg)
            if not suppress_timeline:
                self._emit_timeline(error_msg, "error")
            raise e

    def notify_changes(self, changes: List[Dict[str, Any]]) -> Optional[str]:
        """
        Tespit edilen değişiklikleri kullanıcının seçtiği yöntemlerle bildirir.
        """
        if not changes:
            return None
        
        logging.info(f"{len(changes)} adet değişiklik için bildirim gönderiliyor...")
        
        error_msg = None
        error_reported = False
        for change in changes:
            ders_adi = change['ders']
            yeni = change['yeni']
            
            html_body = OBISEmailTemplates.get_grade_change_template(ders_adi, yeni)
            
            # E-posta Bildirimi
            if "email" in self.notification_methods and self.sender_email:
                try:
                    subject = f"OBIS Notifier - Ders Güncellemesi 📚"
                    self.send_email(subject, html_body, is_html=True, suppress_timeline=error_reported)
                    logging.info(f"E-posta gönderildi: {ders_adi}")
                except Exception as e:
                    logging.error(f"E-mail gönderimi başarısız: {str(e)}")
                    if not error_reported:
                        error_msg = f"Mail gönderme hatası: {str(e)}"
                    error_reported = True
        return error_msg

    def send_test_notification(self) -> None:
        """Kullanıcının ayarlarını doğrulaması için test bildirimi gönderir."""
        logging.info("Test bildirimi gönderiliyor...")
        subject = "OBIS Notifier - Test 🧪"
        html_body = OBISEmailTemplates.get_test_notification_template()
        
        if "email" in self.notification_methods:
            self.send_email(subject, html_body, is_html=True)

    def send_failure_notification(self) -> None:
        """Sistem ardışık hatalar nedeniyle durduğunda bildirim gönderir."""
        subject = "OBIS Notifier - Sistem Durduruldu ⚠️"
        html_body = OBISEmailTemplates.get_failure_notification_template()
        
        # E-posta Bildirimi
        if "email" in self.notification_methods:
            try:
                self.send_email(subject, html_body, is_html=True)
                logging.info("Başarısız giriş bildirim maili gönderildi.")
            except Exception as e:
                logging.error(f"Hata maili gönderilemedi: {e}")
