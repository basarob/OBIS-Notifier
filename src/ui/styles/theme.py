"""
BU DOSYA: Uygulamanın renk paletini, fontlarını ve stil sabitlerini tutar.
Referans görsellere uygun piksel mükemmelliğinde tasarım sağlar.
"""

from PyQt6.QtGui import QColor, QFont, QFontDatabase
import os
import sys

class OBISColors:
    """
    Uygulama genelinde kullanılan renk paleti.
    """
    # Ana Renkler
    PRIMARY = "#4F46E5"         # Morumsu Mavi
    PRIMARY_HOVER = "#4338CA"   # Daha koyu ton
    PRIMARY_PRESSED = "#3730A3" # En koyu ton
    
    # Arka Planlar
    BACKGROUND = "#F8FAFC"       # Ana Arka Plan (Çok açık gri)
    BACKGROUND_LIGHT = "#F0F4FF" # Açık Mavi Tonlu Arka Plan (Gradyan için)
    SURFACE = "#FFFFFF"          # Kartlar ve Paneller (Beyaz)
    SIDEBAR_BG = "#FFFFFF"       # Sidebar Arka Planı (Beyaz)
    INPUT_BG = "#F3F4F6"       # Input alanı arka planı
    
    # Metin Renkleri
    TEXT_PRIMARY = "#111827"   # Başlıklar (Neredeyse Siyah)
    TEXT_SECONDARY = "#6B7280" # Alt metinler (Gri)
    TEXT_GHOST = "#9CA3AF"     # Pasif placeholder text
    TEXT_WHITE = "#FFFFFF"     # Beyaz Metin (Primary butondaki yazı)
    
    # Durum Renkleri
    SUCCESS = "#10B981"        # Yeşil (Aktif/Başarılı)
    SUCCESS_BG = "#D1FAE5"     # Yeşil Arka Plan (Badge için)
    DANGER = "#EF4444"         # Kırmızı (Hata/Çıkış)
    DANGER_BG = "#FEE2E2"      # Kırmızı Arka Plan
    WARNING = "#F59E0B"        # Turuncu
    WARNING_BG = "#FEF3C7"     # Turuncu Arka Plan
    INFO = "#3B82F6"           # Mavi
    
    # Ekstra Renkler
    PURPLE = "#7E22CE"         # Mor
    PURPLE_BG = "#F3E8FF"      # Mor Arka Plan
    
    # Border ve Çizgiler
    BORDER = "#EEEEEE"         # İnce grid çizgileri (Daha açık gri)
    LINE = "#BFBFBF"           # Çizgiler
    
    # Efekt ve Etkileşimler
    SHADOW = "#000000"         # Gölge Rengi
    DANGER_HOVER = "#DC2626"   # Kırmızı Hover
    HOVER_LIGHT = "#F3F4F6"    # Açık Gri Hover (Sidebar, IconBtn)
    HOVER_BLUE = "#EFF6FF"     # Açık Mavi Hover (Ghost Btn, Sidebar Checked)
    PRESSED_LIGHT = "#E5E7EB"  # .Tıklama efekti (Gri)
    AVATAR_BG = "#FCA35F"      # Avatar Arka Planı
    WHITE_ALPHA_20 = "rgba(255, 255, 255, 0.2)" # Saydam Beyaz

    # Log Seviyesi Renkleri
    LOG_DEBUG = "#9CA3AF"      # Gri
    LOG_INFO = "#3B82F6"       # Mavi
    LOG_SUCCESS = "#10B981"    # Yeşil
    LOG_WARN = "#F59E0B"       # .Turuncu
    LOG_ERROR = "#EF4444"      # Kırmızı
    LOG_SYSTEM = "#8B5CF6"     # Mor (Sistem mesajları)
    
    # .Terminal UI Renkleri
    TERMINAL_HEADER = "#181b21"
    TERMINAL_BODY = "#0f1115"
    TERMINAL_BORDER = "#2d3748"
    TERMINAL_TEXT_HEADER = "#6B7280"
    TERMINAL_TEXT_BODY = "#D1D5DB"
    TERMINAL_MESSAGE = "#E5E7EB"
    TERMINAL_ICON = "#9CA3AF"
    TERMINAL_SCROLL_BG = "#1F2937"
    TERMINAL_SCROLL_HANDLE = "#4B5563"

class OBISDimens:
    """
    Boyutlandırma ve boşluk sabitleri.
    """
    # Yarıçaplar
    RADIUS_SMALL = 8          # Küçük elemanlar (Badge, Tag)
    RADIUS_MEDIUM = 12        # Standart elemanlar (Kart, Input)
    RADIUS_LARGE = 20         # Büyük elemanlar
    RADIUS_X_LARGE = 24       # Çok Büyük (Login Kartı vb.)
    RADIUS_FULL = 60          # .Tam yuvarlak (Capsule)

    # Boşluklar
    PADDING_LARGE = 24        # Geniş boşluk
    PADDING_MEDIUM = 16       # Standart boşluk
    PADDING_SMALL = 8         # Küçük boşluk
    
    # Boyutlar
    SIDEBAR_WIDTH = 220       # Sabit Sidebar genişliği
    TOPBAR_HEIGHT = 80        # .Topbar yüksekliği
    ICON_SIZE_DEFAULT = 24    # Standart ikon boyutu

    # Font Boyutları
    TEXT_H1 = 24              # Büyük Başlıklar
    TEXT_H2 = 18              # Kart Başlıkları
    TEXT_H3 = 14              # Alt Başlıklar / Normal Metin
    TEXT_BODY = 10            # Gövde Metni / Butonlar
    TEXT_SMALL = 9            # Küçük Açıklamalar
    TEXT_PASSWORD = 6         # Şifre gizli mod (noktalar için)

class OBISStyles:
    """
    Uygulama genelinde kullanılan ortak stiller.
    """
    # Ana Arka Plan (Radyal Gradyan)
    MAIN_BACKGROUND = f"""
        background-color: qradialgradient(cx:0.5, cy:0.0, radius: 1.0,
                                          fx:0.5, fy:0.0,
                                          stop:0 {OBISColors.BACKGROUND_LIGHT}, 
                                          stop:1 {OBISColors.BACKGROUND});
    """

    # Ana Kart
    MAIN_CARD = f"""
        background-color: {OBISColors.SURFACE};
        border-radius: {OBISDimens.RADIUS_X_LARGE}px; 
        border: 0px; 
    """

    LOG_TABLE = f"""
        QTableWidget {{
            background-color: transparent;
            border: none;
            color: {OBISColors.TERMINAL_TEXT_BODY};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        }}
        QTableWidget::item {{
            padding: 4px;
            border-bottom: 1px solid rgba(55, 65, 81, 0.2);
        }}
        QTableWidget::item:selected {{
            background-color: rgba(59, 130, 246, 0.1);
        }}
        QScrollBar:vertical {{
            background: {OBISColors.TERMINAL_SCROLL_BG};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {OBISColors.TERMINAL_SCROLL_HANDLE};
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """

class OBISFonts:
    """
    Uygulama font tanımları.
    """
    @staticmethod
    def init_fonts():
        """
        Özel fontları (Inter) yükler.
        """
        # Font dizinini bul
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__)) # styles/
            base_path = os.path.join(base_dir, "fonts")
            
        font_files = [
            "Inter-Regular.ttf",
            "Inter-Medium.ttf",
            "Inter-Bold.ttf"
        ]
        
        loaded_families = []
        for font_file in font_files:
            font_path = os.path.join(base_path, font_file)
            if os.path.exists(font_path):
                id = QFontDatabase.addApplicationFont(font_path)
                if id != -1:
                    families = QFontDatabase.applicationFontFamilies(id)
                    loaded_families.extend(families)
            else:
                pass
        
        # Inter fontunu aile içinde ara
        for family in loaded_families:
            if "Inter" in family:
                return family

        return "Segoe UI"

    @staticmethod
    def get_font(size=10, weight="normal"):
        """Dinamik font oluşturucu."""
        # Font ailesini belirle
        family = "Inter"
        
        font = QFont()
        font.setFamily(family) 

        font.setPointSize(size)
        
        if weight == "bold":
            font.setBold(True)
        elif weight == "medium":
            font.setWeight(QFont.Weight.Medium)
            
        # Font optimizasyonu
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        return font

    # Ön tanımlı fontlar
    H1 = get_font(OBISDimens.TEXT_H1, "bold")       # Büyük Başlıklar
    H2 = get_font(OBISDimens.TEXT_H2, "bold")       # Kart Başlıkları
    H3 = get_font(OBISDimens.TEXT_H3, "medium")     # Alt Başlıklar
    
    BODY = get_font(OBISDimens.TEXT_BODY, "normal")   # Düz Metin
    SMALL = get_font(OBISDimens.TEXT_SMALL, "normal") # Küçük açıklama metinleri
    BUTTON = get_font(OBISDimens.TEXT_BODY, "bold")   # Buton yazıları