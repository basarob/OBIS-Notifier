from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import importlib.util
import os
import sys
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "ms-playwright"
from datetime import datetime
import time
import schedule
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def load_config():
    if getattr(sys, 'frozen', False):
        base_path = os.getcwd()
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(base_path, "config.py")

    if not os.path.exists(config_path):
        logging.error(f"Config dosyası bulunamadı: {config_path}")
        print(f"[HATA] Config dosyası bulunamadı: {config_path}")
        exit(1)

    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('obis_notifier.log'),
        logging.StreamHandler()
    ]
)

class OBISNotifier:
    def __init__(self):
        config = load_config()

        self.email = config.obis_mail
        self.password = config.obis_sifre
        self.yariyil = config.yariyil
        self.gonderen_email = config.gonderen_email
        self.gonderen_password = config.gonderen_password
        self.alici_email = config.alici_email
        self.telegram_chat_id = config.telegram_chat_id
        self.telegram_bot_token = config.telegram_bot_token
        self.use_email = config.use_email
        self.use_telegram = config.use_telegram
        self.tarayici = config.tarayici
        self.gorunurluk = config.gorunurluk
        self.sure = config.sure

        self.browser = None
        self.page = None

        self.grades_file = "grades_data.json"
        self.running = True

        self.validate_config()

    def validate_config(self):
        eksik_alanlar = []

        if not self.email: eksik_alanlar.append("obis_mail")
        if not self.password: eksik_alanlar.append("obis_sifre")
        if not self.yariyil: eksik_alanlar.append("yariyil")
        if not self.gonderen_email: eksik_alanlar.append("gonderen_mail")
        if not self.gonderen_password: eksik_alanlar.append("gonderen_password")
        if not self.alici_email: eksik_alanlar.append("alici_email")
        if not self.telegram_bot_token: eksik_alanlar.append("telegram_bot_token")
        if not self.telegram_chat_id: eksik_alanlar.append("telegram_chat_id")
        if not isinstance(self.use_email, bool):
            eksik_alanlar.append("use_email (True veya False olmalı)")
        if not isinstance(self.use_telegram, bool):
            eksik_alanlar.append("use_telegram (True veya False olmalı)")
        if not self.tarayici: eksik_alanlar.append("tarayici")

        if eksik_alanlar:
            logging.error(f"config.py dosyasında eksik alan(lar) var: {', '.join(eksik_alanlar)}")
            print(f"\n[HATA] config.py dosyasındaki şu alan(lar) eksik veya boş: {', '.join(eksik_alanlar)}")
            print("Lütfen config.py dosyasını açıp eksik bilgileri tamamlayın.")
            exit(1)

    def setup_browser(self):
        logging.info("Tarayıcı başlatılıyor...")

        self.playwright = sync_playwright().start()

        browsers = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit
        }

        self.browser = browsers[self.tarayici].launch(
            headless=self.gorunurluk,
            slow_mo=500
        )

        self.page = self.browser.new_page()
        self.page.set_viewport_size({"width": 1280, "height": 720})
    
    def login(self):
        logging.info("OBİS'e giriş yapılıyor...")

        try:

            self.page.goto("https://obisnet.adu.edu.tr/GIRIS?sw=OBIS&u=o")
            self.page.wait_for_load_state('networkidle')

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
    
    def check_login_success(self):
        try:
            page_content = self.page.content()
            success_indicators = ["Ders Kayıt İşlemleri", "Not Sınav İşlemleri"]

            for indicators in success_indicators:
                if indicators in page_content:
                    return True

            return False
        
        except Exception as e:
            logging.error(f"Giriş kontrolü hatası: {str(e)}")
            return False
    
    def navigate_to_grades(self):
        logging.info("Notlar sayfasına gidiliyor...")

        try:
            navigation_menu = self.page.locator('.rtLI:has-text("Not Sınav İşlemleri")')
            navigation_menu.wait_for(state='visible')
            navigation_menu.click()

            grade_button = self.page.locator('.rtIn:has-text("Öğrenci Not Görüntüle")')
            grade_button.wait_for(state='visible')
            grade_button.click()
            
            combobox = self.page.locator('#ctl00_ctl00_cphMain_cphContent_cmbDonem_Arrow')
            combobox.wait_for(state='visible')
            combobox.click()

            dropdown_list = self.page.locator('#ctl00_ctl00_cphMain_cphContent_cmbDonem_DropDown')
            dropdown_list.wait_for(state='visible')

            semester = self.page.locator(f'li:has-text("{self.yariyil}")')
            semester.click()
            
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_selector('#ctl00_ctl00_cphMain_cphContent_rgridOgrenciDersNot_ctl00',state='visible')

            logging.info("Dönem seçildi ve notlar sayfası hazır!")
            return True
            
        except Exception as e:
            logging.error(f"Notlar sayfasına geçişte hata: {str(e)}")
            return False
        
    def get_grades(self):
        logging.info("Notlar çekiliyor...")

        try:
            html_content = self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            grades = []
            table = soup.find("table", {"id": "ctl00_ctl00_cphMain_cphContent_rgridOgrenciDersNot_ctl00"})

            if not table:
                logging.error("Notlar tablosu bulunamadı!")
                return None
            rows = table.find("tbody").find_all("tr")
            if not rows:
                logging.error("Notlar tablosunda satır bulunamadı!")
                return None
            
            for row in rows:
                cells = row.find_all("td")
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
        
    def load_previous_grades(self):
        if os.path.exists(self.grades_file):
            try:
                with open(self.grades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Önceki notlar yüklenemedi: {str(e)}")
                return None
        return None
    
    def save_grades(self, grades):
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
    
    def compare_grades(self, old_grades, new_grades):
        if not old_grades:
            changes = []
            for grade in new_grades:
                changes.append({
                "ders": grade["Ders Adı"],
                "eski": None,
                "yeni": grade
            })
            return changes, "İlk kontrol"
        
        old_dict = {grade["Ders Adı"]: grade for grade in old_grades["grades"]}
        new_dict = {grade["Ders Adı"]: grade for grade in new_grades}
        
        changes = []
        
        for ders_adi, new_grade in new_dict.items():
            if ders_adi in old_dict:
                old_grade = old_dict[ders_adi]
                if (old_grade["Sınavlar"] != new_grade["Sınavlar"] or 
                    old_grade["Harf Notu"] != new_grade["Harf Notu"] or 
                    old_grade["Sonuç"] != new_grade["Sonuç"]):
                    
                    changes.append({
                        "ders": ders_adi,
                        "eski": old_grade,
                        "yeni": new_grade
                    })
            else:
                changes.append({
                    "ders": ders_adi,
                    "eski": None,
                    "yeni": new_grade
                })
        
        return changes, "Değişiklik bulundu" if changes else "Değişiklik yok"
    
    def send_email_notification(self, changes):
        if not changes:
            return
        
        logging.info("E-mail bildirimi gönderiliyor...")
        
        for change in changes:
            subject = f"📚 OBIS Not Güncellemesi - {change['ders']}"
            body = f"📚 {change['ders']}\n\n"
            
            if change['eski']:
                body += "🔄 Güncellendi:\n"
                body += f"• Sınavlar: {change['yeni']['Sınavlar']}\n"
                body += f"• Harf Notu: {change['yeni']['Harf Notu']}\n"
                body += f"• Sonuç: {change['yeni']['Sonuç']}\n"
            else:
                body += "🆕 Yeni Ders:\n"
                body += f"• Sınavlar: {change['yeni']['Sınavlar']}\n"
                body += f"• Harf Notu: {change['yeni']['Harf Notu']}\n"
                body += f"• Sonuç: {change['yeni']['Sonuç']}\n"
            
            body += f"\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            try:
                msg = MIMEMultipart()
                msg['From'] = self.gonderen_email
                msg['To'] = self.alici_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(self.gonderen_email, self.gonderen_password)
                    server.sendmail(self.gonderen_email, self.alici_email, msg.as_string())
                
                logging.info(f"E-posta gönderildi: {change['ders']}")

            except Exception as e:
                logging.error(f"E-mail bildirimi hatası: {str(e)}")

    def send_telegram_notification(self, changes):
        if not changes:
            return
        
        logging.info("Telegram bildirimi gönderiliyor...")
        
        for change in changes:
            message = f"📚 *{change['ders']}*\n\n"
            
            if change['eski']:
                message += "🔄 *Güncellendi:*\n"
                message += f"• Sınavlar: {change['yeni']['Sınavlar']}\n"
                message += f"• Harf Notu: {change['yeni']['Harf Notu']}\n"
                message += f"• Sonuç: {change['yeni']['Sonuç']}\n"
            else:
                message += "🆕 *Yeni Ders:*\n"
                message += f"• Sınavlar: {change['yeni']['Sınavlar']}\n"
                message += f"• Harf Notu: {change['yeni']['Harf Notu']}\n"
                message += f"• Sonuç: {change['yeni']['Sonuç']}\n"
            
            message += f"\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            try:
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    logging.info(f"Telegram bildirimi gönderildi: {change['ders']}")
                else:
                    logging.error(f"Telegram bildirimi gönderilemedi: {response.text}")
                    
            except Exception as e:
                logging.error(f"Telegram bildirimi hatası: {str(e)}")

    def cleanup(self):
        logging.info("Temizlik yapılıyor...")
        
        if self.browser:
            self.browser.close()
        
        if hasattr(self, 'playwright'):
            self.playwright.stop()
        
        logging.info("Temizlik tamamlandı!")
    
    def check_grades_once(self):
        try:
            self.setup_browser()
            
            if self.login():
                if self.navigate_to_grades():
                    new_grades = self.get_grades()
                    if new_grades:
                        old_grades = self.load_previous_grades()
                        changes, status = self.compare_grades(old_grades, new_grades)
                        
                        if changes:
                            if self.use_email:
                                self.send_email_notification(changes)
                            if self.use_telegram:
                                self.send_telegram_notification(changes)
                        else:
                            logging.info("Herhangi bir değişiklik bulunamadı.")
                        
                        self.save_grades(new_grades)
                        return True
                    else:
                        logging.error("Notlar çekilemedi!")
                        return False
                else:
                    logging.error("Notlar sayfasına gidilemedi!")
                    return False
            else:
                logging.error("Giriş yapılamadı!")
                return False
        
        except Exception as e:
            logging.error(f"Kontrol sırasında hata: {str(e)}")
            return False
        
        finally:
            self.cleanup()

    def start_monitoring(self):
        logging.info("Sürekli izleme başlatılıyor...")
        
        self.check_grades_once()
        
        schedule.every(self.sure).minutes.do(self.check_grades_once)

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("İzleme durduruldu!")
            self.running = False

def main():
    
    logging.info("OBIS Notifier başlatılıyor...")
    
    notifier = OBISNotifier()
    notifier.start_monitoring()

if __name__ == "__main__":
    main()