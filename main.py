from config import mail, sifre, yariyil, tarayici
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time

class OBISNotifier:
    def __init__(self):
        self.email = mail
        self.password = sifre
        self.browser = None
        self.page = None
    
    def setup_browser(self):
        print("🔧 Tarayıcı başlatılıyor...")

        self.playwright = sync_playwright().start()

        browsers = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit
        }
        
        self.browser = browsers[tarayici].launch(
            headless=False,  # Görmek için False, production'da True yap
            slow_mo=500
        )

        self.page = self.browser.new_page()

        self.page.set_viewport_size({"width": 1280, "height": 720})
    
    def login(self):
        print("🔐 OBİS'e giriş yapılıyor...")

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
                    print("✅ Giriş başarılı!")
                    return True
            else:
                print("❌ Giriş başarısız!")
                return False
        
        except Exception as e:
            print(f"❌ Giriş sırasında hata: {str(e)}")
            return False
    
    def check_login_success(self):
        try:
            page_content = self.page.content()

            success_indicators = ["ADÜ E-Üniversite Otomasyonu", "Anasayfa", "Duyurular"]

            for indicators in success_indicators:
                if indicators in page_content:
                    return True
                
            return False
        
        except Exception as e:
            print(f"❌ Giriş kontrolü hatası: {str(e)}")
            return False
    
    def navigate_to_grades(self):
        print("📊 Notlar sayfasına gidiliyor...")

        try:
            self.page.goto("https://obisnet.adu.edu.tr/676360FCF558D08E3E756B0BA226FA")
            self.page.wait_for_load_state('networkidle')
            
            combobox = self.page.locator('#ctl00_ctl00_cphMain_cphContent_cmbDonem_Arrow')
            combobox.wait_for(state='visible')
            combobox.click()

            dropdown_list = self.page.locator('#ctl00_ctl00_cphMain_cphContent_cmbDonem_DropDown')
            dropdown_list.wait_for(state='visible')

            semester = self.page.locator(f'li:has-text("{yariyil}")')
            semester.click()
            
            self.page.wait_for_load_state('networkidle')

            print("✅ Dönem seçildi ve notlar sayfası hazır!")
            return True
            
        except Exception as e:
            print(f"❌ Notlar sayfasına geçişte hata: {str(e)}")
            return False
        
    def get_grades(self):
        print("📋 Notlar çekiliyor...")

        try:
            html_content = self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            table = soup.find("table", {"id": "ctl00_ctl00_cphMain_cphContent_rgridOgrenciDersNot_ctl00"})
            grades = []

            rows = table.find("tbody").find_all("tr")
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
            print(f"❌ Notlar çekilirken hata: {str(e)}")
            return None
    
    def cleanup(self):
        print("🧹 Temizlik yapılıyor...")
        
        if self.browser:
            self.browser.close()
        
        if hasattr(self, 'playwright'):
            self.playwright.stop()
        
        print("✅ Temizlik tamamlandı!")


def main():
    print("🚀 OBIS Notifier başlatılıyor...")

    notifier = OBISNotifier()

    try:
        notifier.setup_browser()
        
        # Giriş yap
        if notifier.login():
            # Notlar sayfasına git
            if notifier.navigate_to_grades():
                # Notları çek
                grades = notifier.get_grades()
                if grades:
                    print("📊 Notlar başarıyla çekildi!")
                    print(notifier.get_grades())
                else:
                    print("❌ Notlar çekilemedi!")
            else:
                print("❌ Notlar sayfasına gidilemedi!")
        else:
            print("❌ Giriş yapılamadı!")
    
    except Exception as e:
        print(f"❌ Genel hata: {str(e)}")
    
    finally:
        # Her durumda temizlik yap
        notifier.cleanup()

if __name__ == "__main__":
    main()