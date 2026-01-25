"""
BU DOSYA: Kullanıcıya bildirim gönderme (E-posta ve Windows Bildirimi) işlemlerini yönetir.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

class NotificationService:
    """Bildirim işlemlerini (Mail, Windows Toast) yöneten servis sınıfı."""
    
    def __init__(self, 
                 sender_email: str, 
                 sender_password: str, 
                 notification_methods: List[str], 
                 notification_callback: Optional[Callable] = None):
        """
        Args:
            sender_email: Gönderen Gmail adresi
            sender_password: Gmail Uygulama Şifresi
            notification_methods: Seçili yöntemler listesi
            notification_callback: GUI tarafındaki Windows bildirimi fonksiyonu (callback)
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = sender_email 
        self.notification_methods = notification_methods
        self.notification_callback = notification_callback

    def send_email(self, subject: str, body: str) -> None:
        """
        SMTP protokolü ile e-posta gönderir.
        Gmail SMTP sunucusu (smtp.gmail.com:465 SSL) kullanılır.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
        except Exception as e:
            logging.error(f"Mail gönderme hatası: {e}")
            raise e

    def notify_changes(self, changes: List[Dict[str, Any]]) -> None:
        """
        .Tespit edilen değişiklikleri kullanıcının seçtiği yöntemlerle bildirir.
        """
        if not changes:
            return
        
        logging.info(f"{len(changes)} adet değişiklik için bildirim gönderiliyor...")
        
        for change in changes:
            ders_adi = change['ders']
            
            # Yeni not verisi
            yeni = change['yeni'] # .type: ignore
            
            # Mesaj gövdesini hazırla
            body = f"📚 {ders_adi}\n\n"
            if change['eski']:
                body += "🔄 Güncellendi:\n"
            else:
                body += "🆕 Yeni Ders/Not:\n"

            body += f"• Sınavlar: {yeni['Sınavlar']}\n"
            body += f"• Harf Notu: {yeni['Harf Notu']}\n"
            body += f"• Sonuç: {yeni['Sonuç']}\n"
            body += f"\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # 1. E-posta Bildirimi
            if "email" in self.notification_methods and self.sender_email:
                try:
                    email_subject = f"OBIS: {ders_adi}"
                    self.send_email(email_subject, body)
                    logging.info(f"E-posta gönderildi: {ders_adi}")
                except Exception as e:
                    logging.error(f"E-mail gönderimi başarısız: {str(e)}")
            
            # 2. Windows Bildirimi (Tray Icon veya Toast üzerinden)
            if "windows" in self.notification_methods and self.notification_callback:
                try:
                    summary_text = f"Sınavlar: {yeni['Sınavlar']}\nHarf: {yeni['Harf Notu']} | Sonuç: {yeni['Sonuç']}"
                    # GUI thread'ine callback ile bildir
                    self.notification_callback(f"📚 {ders_adi}", summary_text)
                    logging.info(f"Windows bildirimi tetiklendi: {ders_adi}")
                except Exception as e:
                    logging.error(f"Windows bildirimi hatası: {str(e)}")

    def send_test_notification(self) -> None:
        """Kullanıcının ayarlarını doğrulaması için test bildirimi gönderir."""
        logging.info("Test bildirimi gönderiliyor...")
        subject = "🧪 OBIS Notifier - Test"
        body = (f"Merhaba,\n\n"
                f"Bu bir test bildirimidir. Ayarlarınız doğru yapılandırılmış görünüyor.\n\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        if "email" in self.notification_methods:
            self.send_email(subject, body)
            
        if "windows" in self.notification_methods:
             if self.notification_callback:
                 self.notification_callback("Test Bildirimi", "Sistem başarıyla çalışıyor!")

    def send_failure_notification(self) -> None:
        """Sistem ardışık hatalar nedeniyle durduğunda bildirim gönderir."""
        subject = "⚠️ OBIS Notifier - Sistem Durduruldu"
        body = (f"Merhaba,\n\n"
                f"OBIS sistemine ardışık 3 kez giriş yapılamadı.\n"
                f"Güvenlik nedeniyle veya şifre değişikliği/sistem hatası nedeniyle izleme durduruldu.\n\n"
                f"Lütfen ayarlarınızı kontrol edip sistemi tekrar başlatın.\n\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # 1. E-posta Bildirimi
        if "email" in self.notification_methods:
            try:
                self.send_email(subject, body)
                logging.info("Başarısız giriş bildirim maili gönderildi.")
            except Exception as e:
                logging.error(f"Hata maili gönderilemedi: {e}")

        # 2. Windows Bildirimi
        if "windows" in self.notification_methods and self.notification_callback:
            try:
                self.notification_callback("⚠️ Sistem Durdu", "3 başarısız giriş denemesi. Lütfen şifrenizi kontrol edin.")
                logging.info("Başarısız giriş Windows bildirimi gönderildi.")
            except Exception as e:
                logging.error(f"Hata bildirimi gösterilemedi: {e}") 
