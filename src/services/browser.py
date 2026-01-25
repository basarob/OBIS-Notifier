"""
BU DOSYA: Playwright kütüphanesini kullanarak tarayıcı otomasyonu,
login ve navigation işlemlerini yürütür.
"""

import logging
import sys
import subprocess
from typing import Optional, Dict

# Playwright importları
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

# Konfigürasyon ve Selector importu (Relative import)
from ..config import OBISSelectors

def ensure_browsers_installed() -> bool:
    """
    Playwright tarayıcılarının (Chromium) yüklü olup olmadığını kontrol eder.
    Yüklü değilse indirme işlemini başlatır.
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
        if getattr(sys, 'frozen', False):
            # EXE ortamında Playwright CLI install simülasyonu
            from playwright.__main__ import main
            old_argv = sys.argv
            sys.argv = ["playwright", "install", "chromium"]
            try:
                main()
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv
        else:
            # Geliştirme ortamında subprocess
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            
        logging.info("Tarayıcı kurulumu tamamlandı.")
        return True
    except Exception as e:
        logging.error(f"Tarayıcı kurulumu sırasında kritik hata: {e}")
        return False


class BrowserService:
    """Tarayıcı yaşam döngüsünü ve sayfa etkileşimlerini yönetir."""

    def __init__(self, browser_type: str = "chromium", headless: bool = True):
        self.browser_name = browser_type
        self.headless = headless
        
        # Playwright nesneleri
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def start_browser(self) -> None:
        """Playwright motorunu ve tarayıcıyı başlatır."""
        logging.info("Tarayıcı başlatılıyor...")
        
        self.playwright = sync_playwright().start()
        
        browsers = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit
        }
        
        launcher = browsers.get(self.browser_name, self.playwright.chromium)
        
        # .Tarayıcıyı aç
        self.browser = launcher.launch(
            headless=self.headless,
            slow_mo=500 # İnsan benzeri davranış için gecikme
        )
        
        # Sayfa boyutlarını ayarla (Responsive tasarımlarda sorun olmaması için)
        self.page = self.browser.new_page()
        self.page.set_viewport_size({"width": 1280, "height": 720})

    def close_browser(self) -> None:
        """Tarayıcıyı ve kaynakları temizler."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logging.error(f"Tarayıcı kapatılırken hata: {e}")

    def login(self, student_id: str, password: str) -> bool:
        """
        Öğrenci girişi yapar.
        
        Returns:
            Giriş başarılı ise True.
        """
        logging.info("OBİS'e giriş yapılıyor...")

        if not self.page:
            logging.error("Tarayıcı sayfası açık değil!")
            return False

        try:
            email = f"{student_id}@stu.adu.edu.tr"
            
            # Login sayfasına git
            self.page.goto(OBISSelectors.OBIS_URL)
            self.page.wait_for_load_state('networkidle')

            # Selectors sınıfından seçicileri kullan
            self.page.locator(OBISSelectors.LOGIN_USERNAME_INPUT).fill(email)
            self.page.locator(OBISSelectors.LOGIN_PASSWORD_INPUT).fill(password)
            
            # Giriş butonuna tıkla
            self.page.locator(OBISSelectors.LOGIN_BUTTON).click()

            self.page.wait_for_load_state('networkidle')

            # Başarılı olup olmadığını kontrol et
            if self._check_login_success():
                logging.info("Giriş başarılı!")
                return True
            else:
                logging.error("Giriş başarısız! (Şifre yanlış veya captcha çıkmış olabilir)")
                return False
        
        except Exception as e:
            logging.error(f"Giriş sırasında hata: {str(e)}")
            return False

    def _check_login_success(self) -> bool:
        """Sayfa içeriğinde başarı belirteçlerini arar."""
        try:
            if not self.page: return False
            content = self.page.content()
            # Başarılı girişte görünen menüler
            return "Ders Kayıt İşlemleri" in content or "Not Sınav İşlemleri" in content
        except Exception:
            return False

    def navigate_to_grades(self, semester: str) -> bool:
        """
        Notlar sayfasına gider ve ilgili dönemi seçer.
        """
        logging.info("Notlar sayfasına gidiliyor...")

        if not self.page: return False

        try:
            # 1. Menüleri aç
            self.page.locator(OBISSelectors.MENU_NOT_SINAV).click()
            self.page.locator(OBISSelectors.MENU_OGRENCI_NOT).click()
            
            # 2. Dönem Combobox'ını aç
            self.page.locator(OBISSelectors.SEMESTER_COMBOBOX_ARROW).click()
            
            # 3. Listeden dönemi seç (Dropdown görünür olmalı)
            dropdown_list = self.page.locator(OBISSelectors.SEMESTER_DROPDOWN_LIST)
            dropdown_list.wait_for(state='visible')

            # Dönem metnine göre seç (örn: "2024/2025 Güz")
            semester_item = self.page.locator(f'li:has-text("{semester}")')
            
            if semester_item.count() == 0:
                 logging.error(f"Seçilen dönem ({semester}) listede bulunamadı.")
                 return False
            
            semester_item.click()
            
            self.page.wait_for_load_state('networkidle')
            
            # 4. Tablonun yüklenmesini bekle
            self.page.wait_for_selector(OBISSelectors.GRADES_TABLE_SELECTOR, state='visible')

            return True
            
        except Exception as e:
            logging.error(f"Notlar sayfasına geçişte hata: {str(e)}")
            return False

    def get_page_content(self) -> str:
        """Sayfanın o anki HTML içeriğini döner."""
        if self.page:
            return self.page.content()
        return ""
