"""
BU DOSYA: Proje genelindeki constant'ları, 
versiyon bilgisini ve HTML/CSS Selector'ları barındırır.
"""

# !Uygulama Versiyonu
CURRENT_VERSION = "v2.1"

class OBISSelectors:
    """
    OBIS sistemi web arayüzü için gerekli HTML/CSS Selector'ları tutar.
    """
    # !--- Genel ---
    OBIS_URL = "https://obisnet.adu.edu.tr/GIRIS?sw=OBIS&u=o"

    # !--- Giriş Ekranı ---
    # Kullanıcı adı input alanı (name attribute ile seçim)
    LOGIN_USERNAME_INPUT = 'input[name="ctl00$ctl00$cphMain$cphContent$loginRecaptcha$UserName"]'
    # Şifre input alanı
    LOGIN_PASSWORD_INPUT = 'input[name="ctl00$ctl00$cphMain$cphContent$loginRecaptcha$Password"]'
    # Giriş butonu ID'si
    LOGIN_BUTTON = '#ctl00_ctl00_cphMain_cphContent_loginRecaptcha_btnGiris'
    
    # !--- Navigasyon Menüsü ---
    # Soldaki menü öğesi
    MENU_NOT_SINAV = '.rtLI:has-text("Not Sınav İşlemleri")'
    MENU_OGRENCI_NOT = '.rtIn:has-text("Öğrenci Not Görüntüle")'
    
    # !--- Dönem Seçimi ---
    # Dropdown kutusunu açan ok işareti
    SEMESTER_COMBOBOX_ARROW = '#ctl00_ctl00_cphMain_cphContent_cmbDonem_Arrow'
    # Dropdown list
    SEMESTER_DROPDOWN_LIST = '#ctl00_ctl00_cphMain_cphContent_cmbDonem_DropDown'
    
    # !--- Not Tablosu ---
    # .Tablonun ham ID'si (BeautifulSoup için)
    GRADES_TABLE_ID = "ctl00_ctl00_cphMain_cphContent_rgridOgrenciDersNot_ctl00"
    # Playwright için ID seçici (# ile başlar)
    GRADES_TABLE_SELECTOR = f'#{GRADES_TABLE_ID}'
