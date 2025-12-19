import json
import logging
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple, Union
import schedule
import requests
from packaging import version
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

CURRENT_VERSION = "v2.1"

def check_for_updates(current_version_str: str, repo_owner: str = "basarob", repo_name: str = "OBIS-Notifier") -> Optional[Dict[str, str]]:
    """GitHub releases üzerinden güncelleme kontrolü yapar."""
    try:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        latest_release = response.json()
        latest_tag = latest_release.get("tag_name", "v0.0.0")
        
        # 'v' harfini temizle ve karşılaştır
        try:
            v_current = version.parse(current_version_str.lstrip("v"))
            v_latest = version.parse(latest_tag.lstrip("v"))
            
            if v_latest > v_current:
                return {
                    "version": latest_tag,
                    "url": latest_release.get("html_url"),
                    "body": latest_release.get("body", "")
                }
        except Exception:
            # Versiyon parse edilemezse, string olarak karşılaştır
            if latest_tag != current_version_str:
                 return {
                    "version": latest_tag,
                    "url": latest_release.get("html_url"),
                    "body": latest_release.get("body", "")
                }

    except Exception as e:
        logging.error(f"Güncelleme kontrolü başarısız: {e}")
    
    return None

def set_auto_start(enable: bool = True) -> bool:
    """
    Windows başlangıç klasörüne kısayol oluşturarak otomatik başlatmayı ayarlar.
    Registry yerine bu yöntem kullanılır, böylece Görev Yöneticisi'nde "Python" yerine
    uygulama adı görünür.

    Args:
        enable (bool): True ise kısayol oluşturur, False ise siler.

    Returns:
        bool: İşlem başarılı ise True, değilse False.
    """
    try:
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_folder, "OBIS Notifier.lnk")
        
        if enable:
            if os.path.exists(shortcut_path):
                return True

            target = sys.executable
            cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
            arguments = ""
            
            # Eğer script olarak çalışıyorsa (exe değilse)
            if not getattr(sys, 'frozen', False):
                script_path = os.path.abspath(sys.argv[0])
                arguments = f'"{script_path}"'
            else:
                target = sys.executable
                cwd = os.path.dirname(target)
            
            icon_path = ""
            if getattr(sys, 'frozen', False):
                 icon_path = target
            else:
                 icon_candidate = os.path.join(cwd, "images", "icon.ico")
                 if os.path.exists(icon_candidate):
                     icon_path = icon_candidate

            # PowerShell ile kısayol oluşturma
            ps_command = (
                f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{shortcut_path}");'
                f'$s.TargetPath="{target}";'
                f'$s.Arguments=\'{arguments}\';'
                f'$s.WorkingDirectory="{cwd}";'
                f'if("{icon_path}" -ne ""){{$s.IconLocation="{icon_path}"}};'
                f'$s.Save()'
            )
            
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            logging.info(f"Otomatik başlatma kısayolu oluşturuldu: {shortcut_path}")
            
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                logging.info("Otomatik başlatma kısayolu silindi.")
        
        return True
    except Exception as e:
        logging.error(f"Otomatik başlatma ayarı yapılamadı: {e}")
        return False

def get_user_data_dir() -> str:
    """
    Kullanıcı veri dizinini (AppData/Local/OBISNotifier) döndürür.
    Klasör yoksa oluşturur.
    """
    app_data = os.getenv('LOCALAPPDATA')
    if not app_data:
        app_data = os.getenv('APPDATA') # Fallback
        
    data_dir = os.path.join(app_data, "OBISNotifier")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

# Loglama ayarlarının yapılması
log_file_path = os.path.join(get_user_data_dir(), 'obis_notifier.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def ensure_browsers_installed() -> bool:
    """
    Playwright tarayıcılarının (Chromium) yüklü olup olmadığını kontrol eder.
    Yüklü değilse indirme işlemini başlatır.
    
    Returns:
        bool: İşlem başarılı ise True, aksi halde False.
    """
    logging.info("Tarayıcı kontrolü yapılıyor...")
    
    # 1. Kontrol: Tarayıcı başlatmayı dene
    try:
        with sync_playwright() as p:
             p.chromium.launch(headless=True).close()
        logging.info("Tarayıcılar zaten yüklü.")
        return True
    except Exception:
        logging.warning("Chromium tarayıcısı bulunamadı, indiriliyor...")
    
    # 2. İndirme İşlemi
    try:
        # sys.frozen kontrolü (EXE mi yoksa script mi?)
        if getattr(sys, 'frozen', False):
            # EXE içinden playwright kurulumunu tetiklemek için main'i çağırıyoruz
            # Not: Bu yöntem Playwright CLI'ını simüle eder.
            from playwright.__main__ import main
            
            old_argv = sys.argv
            sys.argv = ["playwright", "install", "chromium"]
            
            try:
                main()
            except SystemExit:
                # Playwright install işlemi exit() çağırabilir, bunu yakalıyoruz
                pass
            finally:
                sys.argv = old_argv
                
        else:
            # Geliştirme ortamında (Script) normal komut satırı
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            
        logging.info("Tarayıcı kurulumu tamamlandı.")
        return True
        
    except Exception as e:
        logging.error(f"Tarayıcı kurulumu sırasında kritik hata: {e}")
        return False

class OBISNotifier:
    """
    OBIS sistemini izleyen, notları çeken ve değişiklik durumunda bildirim gönderen ana sınıf.
    """
    
    def __init__(self, settings: Dict[str, Any]) -> None:
        """
        Sınıfı başlatır ve ayarları yükler.

        Args:
            settings (Dict[str, Any]): Ayar sözlüğü.
        """
        self.settings = settings
        
        # Giriş Bilgileri
        self.student_id: str = settings.get("student_id", "")
        self.password: str = settings.get("obis_password", "")
        self.email: str = f"{self.student_id}@stu.adu.edu.tr"
        
        # Bildirim Ayarları
        self.notification_methods: List[str] = settings.get("notification_methods", ["email"])
        
        self.gonderen_email: str = settings.get("sender_email", "")
        self.gonderen_password: str = settings.get("gmail_app_password", "")
        self.alici_email: str = self.gonderen_email
        
        # Diğer Ayarlar
        self.yariyil: str = settings.get("semester", "")
        self.sure: int = int(settings.get("check_interval", 20))
        self.tarayici: str = settings.get("browser", "chromium")
        self.minimize_to_tray: bool = settings.get("minimize_to_tray", False)
        self.auto_start: bool = settings.get("auto_start", False)
        self.stop_on_failures: bool = settings.get("stop_on_failures", True)

        self.gorunurluk: bool = True # .Tarayıcının görünür olup olmadığı (True = Headless)
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None

        self.grades_file: str = os.path.join(get_user_data_dir(), "grades_data.json")
        self.running: bool = True

        self.consecutive_failures: int = 0  # Başarısız kontrollerin sayısını tutar
        self.check_count: int = 1  # Kontrol sayısını tutar
        
        # Callbacks
        self.status_callback = settings.get("status_callback", None)
        self.notification_callback = settings.get("notification_callback", None) # Windows bildirimi için GUI callback

        self.validate_config()

    def validate_config(self) -> None:
        """
        Yapılandırma ayarlarının eksiksiz olup olmadığını kontrol eder.
        Eksik alan varsa loga hata düşer.
        """
        eksik_alanlar = []

        if not self.student_id: eksik_alanlar.append("student_id")
        if not self.password: eksik_alanlar.append("obis_password")
        if not self.yariyil: eksik_alanlar.append("semester")
        
        if "email" in self.notification_methods:
            if not self.gonderen_email: eksik_alanlar.append("sender_email")
            if not self.gonderen_password: eksik_alanlar.append("gmail_app_password")

        if eksik_alanlar:
            logging.error(f"Ayarlarda eksik alan(lar) var: {', '.join(eksik_alanlar)}")

    def setup_browser(self) -> None:
        """
        Playwright kütüphanesini başlatır ve tarayıcıyı ayarlar.
        """
        logging.info("Tarayıcı başlatılıyor...")

        self.playwright = sync_playwright().start()

        browsers = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit
        }

        # Seçilen tarayıcıyı başlat
        browser_type = browsers.get(self.tarayici, self.playwright.chromium)
        self.browser = browser_type.launch(
            headless=self.gorunurluk,
            slow_mo=500
        )

        self.page = self.browser.new_page()
        self.page.set_viewport_size({"width": 1280, "height": 720})

    def login(self) -> bool:
        """
        OBİS sistemine giriş yapar.

        Returns:
            bool: Giriş başarılıysa True, değilse False.
        """
        logging.info("OBİS'e giriş yapılıyor...")

        if not self.page:
            logging.error("Sayfa nesnesi oluşturulmamış.")
            return False

        try:
            self.page.goto("https://obisnet.adu.edu.tr/GIRIS?sw=OBIS&u=o")
            self.page.wait_for_load_state('networkidle')

            # Kullanıcı adı ve şifre alanlarını doldur
            email_input = self.page.locator('input[name="ctl00$ctl00$cphMain$cphContent$loginRecaptcha$UserName"]')
            email_input.wait_for(state='visible')
            email_input.fill(self.email)

            password_input = self.page.locator('input[name="ctl00$ctl00$cphMain$cphContent$loginRecaptcha$Password"]')
            password_input.wait_for(state='visible')
            password_input.fill(self.password)

            login_button = self.page.locator('#ctl00_ctl00_cphMain_cphContent_loginRecaptcha_btnGiris')
            login_button.wait_for(state='visible')
            login_button.click()

            self.page.wait_for_load_state('networkidle')

            if self.check_login_success():
                logging.info("Giriş başarılı!")
                return True
            else:
                logging.error("Giriş başarısız! Mail veya şifre hatalı olabilir.")
                return False
        
        except Exception as e:
            logging.error(f"Giriş sırasında hata: {str(e)}")
            return False

    def check_login_success(self) -> bool:
        """
        Sayfa içeriğini kontrol ederek girişin başarılı olup olmadığını doğrular.

        Returns:
            bool: Başarılı ise True.
        """
        try:
            if not self.page:
                return False
            
            # Başarılı girişte görünmesi beklenen metinler
            page_content = self.page.content()
            success_indicators = ["Ders Kayıt İşlemleri", "Not Sınav İşlemleri"]

            for indicator in success_indicators:
                if indicator in page_content:
                    return True

            return False
        
        except Exception as e:
            logging.error(f"Giriş kontrolü hatası: {str(e)}")
            return False
    
    def stop_monitoring(self) -> None:
        """İzleme işlemini ve döngüyü durdurur."""
        logging.info("İzleme durduruluyor...")
        self.running = False
    
    def navigate_to_grades(self) -> bool:
        """
        Giriş yaptıktan sonra not görüntüleme sayfasına gider ve ilgili dönemi seçer.

        Returns:
            bool: İşlem başarılı ise True.
        """
        logging.info("Notlar sayfasına gidiliyor...")

        if not self.page:
            return False

        try:
            # Menü navigasyonu
            navigation_menu = self.page.locator('.rtLI:has-text("Not Sınav İşlemleri")')
            navigation_menu.wait_for(state='visible')
            navigation_menu.click()

            grade_button = self.page.locator('.rtIn:has-text("Öğrenci Not Görüntüle")')
            grade_button.wait_for(state='visible')
            grade_button.click()
            
            # Dönem seçimi
            combobox = self.page.locator('#ctl00_ctl00_cphMain_cphContent_cmbDonem_Arrow')
            combobox.wait_for(state='visible')
            combobox.click()

            dropdown_list = self.page.locator('#ctl00_ctl00_cphMain_cphContent_cmbDonem_DropDown')
            dropdown_list.wait_for(state='visible')

            semester = self.page.locator(f'li:has-text("{self.yariyil}")')
            if semester.count() == 0:
                 logging.error(f"Seçilen dönem ({self.yariyil}) bulunamadı.")
                 return False
            semester.click()
            
            self.page.wait_for_load_state('networkidle')
            
            # Not tablosunun yüklenmesini bekle
            self.page.wait_for_selector('#ctl00_ctl00_cphMain_cphContent_rgridOgrenciDersNot_ctl00', state='visible')

            logging.info("Dönem seçildi ve notlar sayfası hazır!")
            return True
            
        except Exception as e:
            logging.error(f"Notlar sayfasına geçişte hata: {str(e)}")
            return False
    
    def get_grades(self) -> Optional[List[Dict[str, str]]]:
        """
        Sayfadaki HTML tablosunu ayrıştırarak notları çeker.

        Returns:
            Optional[List[Dict[str, str]]]: Not listesi veya hata durumunda None.
        """
        logging.info("Notlar çekiliyor...")

        if not self.page:
            return None

        try:
            html_content = self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            grades = []
            table = soup.find("table", {"id": "ctl00_ctl00_cphMain_cphContent_rgridOgrenciDersNot_ctl00"})

            if not table:
                logging.error("Notlar tablosu bulunamadı!")
                return None
            
            tbody = table.find("tbody")
            if not tbody:
                 logging.error("Tablo içeriği (tbody) bulunamadı!")
                 return None

            rows = tbody.find_all("tr")
            if not rows:
                logging.error("Notlar tablosunda satır bulunamadı!")
                return None
            
            for row in rows:
                cells = row.find_all("td")
                if len(cells) > 4:
                    ders = cells[0].get_text(strip=True)
                    sinavlar = cells[1].get_text(strip=True)
                    harf_notu = cells[2].get_text(strip=True)
                    sonuc = cells[4].get_text(strip=True)
                    
                    grades.append({
                        "Ders Adı": ders,
                        "Sınavlar": sinavlar,
                        "Harf Notu": harf_notu,
                        "Sonuç": sonuc
                    })
        
            return grades
            
        except Exception as e:
            logging.error(f"Notlar çekilirken hata: {str(e)}")
            return None
    
    def load_previous_grades(self) -> Optional[Dict[str, Any]]:
        """
        Daha önce kaydedilmiş notları dosyadan okur.

        Returns:
            Optional[Dict]: Kaydedilmiş veriler veya None.
        """
        if os.path.exists(self.grades_file):
            try:
                with open(self.grades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Önceki notlar yüklenemedi: {str(e)}")
                return None
        return None
    
    def save_grades(self, grades: List[Dict[str, str]]) -> bool:
        """
        Mevcut notları dosyaya kaydeder.

        Args:
            grades (List[Dict]): Kaydedilecek not listesi.

        Returns:
            bool: Başarılı ise True.
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "grades": grades
            }
            with open(self.grades_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info("Notlar başarıyla kaydedildi!")
            return True
        except Exception as e:
            logging.error(f"Notlar kaydedilemedi: {str(e)}")
            return False
    
    def compare_grades(self, old_data: Optional[Dict[str, Any]], new_grades: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], str]:
        """
        Eski ve yeni notları karşılaştırır.

        Args:
            old_data (Optional[Dict]): Dosyadan okunan eski veriler.
            new_grades (List[Dict]): Yeni çekilen notlar.

        Returns:
            .Tuple[List, str]: Değişiklik listesi ve durum mesajı.
        """
        if not old_data or "grades" not in old_data:
            # İlk kez çalışıyorsa veya eski veri yoksa hepsini değişiklik olarak ekle
            changes = []
            for grade in new_grades:
                changes.append({
                "ders": grade["Ders Adı"],
                "eski": None,
                "yeni": grade
            })
            return changes, "İlk kontrol"
        
        old_grades_list = old_data["grades"]
        old_dict = {grade["Ders Adı"]: grade for grade in old_grades_list}
        new_dict = {grade["Ders Adı"]: grade for grade in new_grades}
        
        changes = []
        
        for ders_adi, new_grade in new_dict.items():
            if ders_adi in old_dict:
                old_grade = old_dict[ders_adi]
                # Değişiklik kontrolü
                if (old_grade["Sınavlar"] != new_grade["Sınavlar"] or 
                    old_grade["Harf Notu"] != new_grade["Harf Notu"] or 
                    old_grade["Sonuç"] != new_grade["Sonuç"]):
                    
                    changes.append({
                        "ders": ders_adi,
                        "eski": old_grade,
                        "yeni": new_grade
                    })
            else:
                # Yeni bir ders eklenmişse
                changes.append({
                    "ders": ders_adi,
                    "eski": None,
                    "yeni": new_grade
                })
        
        return changes, "Değişiklik bulundu" if changes else "Değişiklik yok"
    
    def send_notification(self, changes: List[Dict[str, Any]]) -> None:
        """
        Değişiklikleri seçilen yöntemlerle (Mail/Windows) bildirir.

        Args:
            changes (List[Dict]): Değişiklik listesi.
        """
        if not changes:
            return
        
        logging.info("Bildirimler gönderiliyor...")
        
        for change in changes:
            ders_adi = change['ders']
            subject = f"📚 {ders_adi}"
            
            yeni = change['yeni'] # .type: ignore
            
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
            if "email" in self.notification_methods and self.gonderen_email:
                try:
                    email_subject = f"OBIS: {ders_adi}"
                    self.send_email(email_subject, body)
                    logging.info(f"E-posta gönderildi: {ders_adi}")
                except Exception as e:
                    logging.error(f"E-mail bildirimi hatası: {str(e)}")
            
            # 2. Windows Bildirimi (Tray Icon üzerinden)
            if "windows" in self.notification_methods and self.notification_callback:
                try:
                    summary_text = f"Sınavlar: {yeni['Sınavlar']}\nHarf: {yeni['Harf Notu']} | Sonuç: {yeni['Sonuç']}"
                    self.notification_callback(subject, summary_text)
                    logging.info(f"Windows bildirimi tetiklendi: {ders_adi}")
                except Exception as e:
                    logging.error(f"Windows bildirimi hatası: {str(e)}")

    def send_email(self, subject: str, body: str) -> None:
        """
        Genel SMTP e-posta gönderme fonksiyonu.

        Args:
            subject (str): Konu başlığı.
            body (str): Mesaj içeriği.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.gonderen_email
            msg['To'] = self.alici_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Gmail SMTP SSL portu 465
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.gonderen_email, self.gonderen_password)
                server.sendmail(self.gonderen_email, self.alici_email, msg.as_string())
        except Exception as e:
            logging.error(f"Mail gönderme hatası: {e}")
            raise e
    
    def send_test_notification(self) -> None:
        """
        Ayarların doğruluğunu test etmek için kullanıcıya test bildirimi gönderir.
        """
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

        logging.info("Test bildirimi tamamlandı.")

    def send_failure_notification(self) -> None:
        """
        Ardışık başarısız giriş denemeleri sonrası uyarı maili gönderir.
        """
        subject = "⚠️ OBIS Notifier - Sistem Durduruldu"
        body = (f"Merhaba,\n\n"
                f"OBIS sistemine ardışık 3 kez giriş yapılamadı.\n"
                f"Güvenlik nedeniyle veya şifre değişikliği/sistem hatası nedeniyle izleme durduruldu.\n\n"
                f"Lütfen ayarlarınızı kontrol edip sistemi tekrar başlatın.\n\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        try:
            self.send_email(subject, body)
            logging.info("Başarısız giriş bildirim maili gönderildi.")
        except Exception:
            pass            

    def cleanup(self) -> None:
        """
        .Tarayıcı ve Playwright kaynaklarını temizler/kapatır.
        """
        logging.info("Temizlik yapılıyor...")
        
        try:
            if self.browser:
                self.browser.close()
            
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
             logging.error(f"Temizlik sırasında hata: {e}")
        
        logging.info("Temizlik tamamlandı!")
    
    def check_grades_once(self) -> bool:
        """
        .Tek seferlik tam kontrol döngüsü: Giriş -> Notları Çek -> Karşılaştır -> Kaydet.

        Returns:
            bool: Döngü başarıyla tamamlandıysa True.
        """
        try:
            logging.info(f"====== {self.check_count}. KONTROL ======")
            self.check_count += 1
            
            self.setup_browser()
            
            if self.login():
                self.consecutive_failures = 0 # Başarılı girişte ardışık başarısız sayısını sıfırlar
                
                if self.navigate_to_grades():
                    new_grades = self.get_grades()
                    
                    if new_grades is not None:
                        old_grades_data = self.load_previous_grades()
                        changes, status = self.compare_grades(old_grades_data, new_grades)
                        
                        if changes:
                            self.send_notification(changes)
                        else:
                            logging.info("Herhangi bir değişiklik bulunamadı.")
                        
                        self.save_grades(new_grades)
                        
                        # Arayüz için callback
                        if self.status_callback:
                             timestamp = datetime.now().strftime('%H:%M')
                             self.status_callback(f"Son Kontrol: {timestamp} (Başarılı)")
                             
                        return True
                    else:
                        logging.error("Notlar çekilemedi! (Liste boş veya tablo hatası)")
                        if self.status_callback: self.status_callback("Son Kontrol: Başarısız")
                        return False
                else:
                    logging.error("Notlar sayfasına gidilemedi!")
                    if self.status_callback: self.status_callback("Son Kontrol: Başarısız")
                    return False
            else:
                # Giriş başarısız
                if self.status_callback: self.status_callback("Son Kontrol: Başarısız")
                self.consecutive_failures += 1
                logging.error(f"Giriş yapılamadı! ({self.consecutive_failures})")
                
                if self.stop_on_failures and self.consecutive_failures >= 3:
                     logging.error("3 ardışık başarısız giriş denemesi. Program durduruluyor.")
                     self.send_failure_notification()
                     self.stop_monitoring()
                     
                return False
        
        except Exception as e:
            logging.error(f"Kontrol sırasında hata: {str(e)}")
            return False
        
        finally:
            self.cleanup()

    def start_monitoring(self) -> None:
        """
        Sürekli izleme döngüsünü başlatır. Schedule kütüphanesini kullanır.
        """
        logging.info("Sürekli izleme başlatılıyor...")
        
        # İlk kontrol hemen başlasın
        self.check_grades_once()
        
        schedule.every(self.sure).minutes.do(self.check_grades_once)

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("İzleme durduruldu (KeyboardInterrupt)!")
            self.running = False

def main() -> None:
    logging.info("OBIS Notifier başlatılıyor...")
    # .Test amaçlı dummy settings
    settings = {
        "obis_mail": "test",
        "obis_password": "test",
        "interval": 20
    }

    notifier = OBISNotifier(settings)
    notifier.start_monitoring()

if __name__ == "__main__":
    main()