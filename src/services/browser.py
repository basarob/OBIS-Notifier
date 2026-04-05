"""
BU DOSYA: Playwright kütüphanesini kullanarak tarayıcı otomasyonu,
login ve navigation işlemlerini yürütür.
"""

import logging
import os
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from config import OBISSelectors


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
            
            self.page.wait_for_timeout(1000)

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
            return "Ders Kayıt İşlemleri" in content and "Not Sınav İşlemleri" in content and "Açık Rıza İşlemleri" in content
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
            
            # 3. Dropdown görünürlüğünü bekle
            dropdown_list = self.page.locator(OBISSelectors.SEMESTER_DROPDOWN_LIST)
            dropdown_list.wait_for(state='visible')

            # 4. Dönem metnine göre seç
            semester_item = self.page.locator(f'li:has-text("{semester}")')
            
            if semester_item.count() == 0:
                 error_msg = f"Seçilen dönem ({semester}) listede bulunamadı."
                 logging.error(error_msg)
                 raise ValueError(error_msg)
            
            semester_item.click()
            
            self.page.wait_for_load_state('networkidle')
            
            # 5. Tablonun yüklenmesini bekle
            self.page.wait_for_selector(OBISSelectors.GRADES_TABLE_SELECTOR, state='visible')

            return True
            
        except ValueError:
            # Dönem bulunamadı gibi yapısal hatalar üst katmana (notifier) iletilmeli
            raise
        except Exception as e:
            logging.error(f"Notlar sayfasına geçişte hata: {str(e)}")
            return False

    def get_page_content(self) -> str:
        """Sayfanın o anki HTML içeriğini döner."""
        if self.page:
            return self.page.content()
        return ""

    def download_graduation_pdf(self) -> str:
        """
        Mezuniyet sayfasına gider, PDF'i indirir ve dosya yolunu döner.
        """
        logging.info("Mezuniyet sayfasına gidiliyor...")
        if not self.page: return ""

        try:
            # 1. Menüleri aç
            self.page.locator(OBISSelectors.MENU_PROFILE).click()
            self.page.locator(OBISSelectors.MENU_PROFILE_INFO).click()
            
            # 2. Sayfanın yüklenmesini bekle
            self.page.wait_for_load_state('networkidle')

            # 2. İndirme menüsünü açacak butona tıkla
            download_button = self.page.locator(OBISSelectors.PROFILE_DOWNLOAD_BUTTON)
            download_button.click()

            # 3. Menünün açılması için kısa bir süre bekle
            download_menu = self.page.locator(OBISSelectors.PROFILE_DOWNLOAD_MENU)
            download_menu.wait_for(state='visible')

            # 4. PDF butonuna tıkla
            pdf_button = self.page.locator(OBISSelectors.PROFILE_DOWNLOAD_PDF_OPTION)
            self.page.wait_for_timeout(1000)

            # 3."PDF" yazan seçeneğe tıkla ve indirmeyi bekle
            with self.page.expect_download(timeout=60000) as download_info:
                pdf_button.click(force=True)
                logging.info("PDF indiriliyor...")
            
            download = download_info.value
            
            # 4. İndirmenin bitmesini kesin olarak bekle
            download_error = download.failure()
            if download_error:
                logging.error(f"İndirme işlemi başarısız: {download_error}")
                return ""

            # KRİTİK ÇÖZÜM: Çalışma dizini yerine AppData içine kaydet
            appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'OBISNotifier')
            os.makedirs(appdata_dir, exist_ok=True) # Klasör yoksa oluştur
            
            # Geçici dosyayı AppData içine kaydet (CWD System32 olabilir)
            temp_path = os.path.join(appdata_dir, "temp_mezuniyet.pdf")
            download.save_as(temp_path)
            
            return temp_path
            
        except Exception as e:
            logging.error(f"PDF indirme hatası: {str(e)}")
            return ""