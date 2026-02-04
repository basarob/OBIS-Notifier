"""
BU DOSYA: Uygulamanın sol tarafındaki sabit navigasyon menüsü.
Yenilenmiş Tasarım: Header (Logo/İsim), Navigasyon, Footer (Durum).
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QBrush
from ..styles.theme import OBISColors, OBISDimens, OBISFonts
from ..utils.animations import OBISAnimations
import qtawesome as qta

class StatusIndicator(QWidget):
    """
    Animasyonlu durum indikatörü (Nokta).
    Renk değişimini performant şekilde yapabilmek için custom paint kullanır.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = QColor(OBISColors.SUCCESS) # Varsayılan renk

    @pyqtProperty(QColor)
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.update() # Repaint tetikle

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Daire çiz
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

class SidebarButton(QPushButton):
    """Sidebar için özel tasarlanmış buton."""
    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(text, parent)
        self.icon_name = icon_name
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(OBISFonts.get_font(10, "medium"))
        
        self.setCheckable(True)
        self.setAutoExclusive(True)
        
        # Varsayılan stil (Padding ve Margin ayarları)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                text-align: left;
                padding-left: 20px;
                color: {OBISColors.TEXT_SECONDARY};
                border-radius: {OBISDimens.RADIUS_SMALL}px;
                margin-left: 10px;
                margin-right: 10px;
            }}
            QPushButton:hover {{
                background-color: {OBISColors.HOVER_LIGHT};
                color: {OBISColors.PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {OBISColors.HOVER_BLUE};
                color: {OBISColors.PRIMARY};
                font-weight: bold;
            }}
        """)
        
        # Başlangıç ikonu
        self._update_icon(OBISColors.TEXT_SECONDARY)
        
        # Checked durumu değiştiğinde ikonu güncelle
        self.toggled.connect(self._on_toggle)

    def _on_toggle(self, checked: bool):
        """Seçim durumuna göre ikon rengini güncelle."""
        color = OBISColors.PRIMARY if checked else OBISColors.TEXT_SECONDARY
        self._update_icon(color)

    def _update_icon(self, color):
        """İkonu belirtilen renkte yeniden oluşturur."""
        icon = qta.icon(self.icon_name, color=color)
        self.setIcon(icon)
        self.setIconSize(QSize(20, 20))

class OBISSidebar(QFrame):
    """
    Sol Navigasyon Paneli.
    Header: Logo + İsim
    Body: Navigasyon Butonları
    Footer: Sistem Durumu
    """
    page_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedWidth(OBISDimens.SIDEBAR_WIDTH)
        self.setStyleSheet(f"""
            OBISSidebar {{
                background-color: {OBISColors.SIDEBAR_BG};
                border-right: 1px solid {OBISColors.BORDER};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Header (Logo & İsim)
        self._setup_header()
        
        # Ayırıcı Çizgi 1
        self._add_separator()
        
        # 2. Navigasyon (Butonlar)
        self._setup_nav()
        
        # Boşluk (Footer'ı aşağı iter)
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Ayırıcı Çizgi 2
        self._add_separator()

        # 3. Footer (Sistem Durumu)
        self._setup_footer()
        
        # Varsayılan Seçim
        self.btn_dashboard.setChecked(True)

    def _add_separator(self):
        """Yatay ayırıcı çizgi ekler."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.NoFrame)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {OBISColors.BORDER};")
        self.layout.addWidget(line)

    def _setup_header(self):
        """Üst kısım: Logo ve İsim. Topbar ile eşit yükseklikte."""
        header_container = QWidget()
        header_container.setFixedHeight(OBISDimens.TOPBAR_HEIGHT)
        
        h_layout = QHBoxLayout(header_container)
        h_layout.setContentsMargins(20, 0, 20, 0)
        h_layout.setSpacing(12)
        
        # Logo Arkaplanı
        logo_bg = QLabel()
        logo_bg.setFixedSize(40, 40)
        logo_bg.setStyleSheet(f"""
            background-color: {OBISColors.PRIMARY};
            border-radius: {OBISDimens.RADIUS_MEDIUM}px;
        """)
        logo_bg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo İkonu
        logo_icon = qta.icon("fa5s.graduation-cap", color="white")
        logo_bg.setPixmap(logo_icon.pixmap(QSize(18, 18)))
        
        # Yazı Grubu
        text_container = QWidget()
        t_layout = QVBoxLayout(text_container)
        t_layout.setContentsMargins(0, 5, 0, 5) 
        t_layout.setSpacing(0)
        t_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        title = QLabel("OBIS NOTIFIER")
        title.setFont(OBISFonts.get_font(10, "bold"))
        title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY};")
        
        subtitle = QLabel("Akademik Asistan")
        subtitle.setFont(OBISFonts.get_font(8, "medium"))
        subtitle.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        
        t_layout.addWidget(title)
        t_layout.addWidget(subtitle)
        
        h_layout.addWidget(logo_bg)
        h_layout.addWidget(text_container)
        h_layout.addStretch()
        
        self.layout.addWidget(header_container)

    def _setup_nav(self):
        """Orta kısım: Menü Butonları"""
        nav_container = QWidget()
        n_layout = QVBoxLayout(nav_container)
        n_layout.setContentsMargins(0, 20, 0, 20)
        n_layout.setSpacing(8)
        
        self.btn_dashboard = SidebarButton("Ana Menü", "fa5s.th-large", parent=nav_container)
        self.btn_settings = SidebarButton("Ayarlar", "fa5s.cog", parent=nav_container)
        self.btn_logs = SidebarButton("Loglar", "fa5s.file-alt", parent=nav_container)
        
        # Sinyaller
        self.btn_dashboard.clicked.connect(lambda: self.page_changed.emit(0))
        self.btn_settings.clicked.connect(lambda: self.page_changed.emit(1))
        self.btn_logs.clicked.connect(lambda: self.page_changed.emit(2))
        
        n_layout.addWidget(self.btn_dashboard)
        n_layout.addWidget(self.btn_settings)
        n_layout.addWidget(self.btn_logs)
        
        self.layout.addWidget(nav_container)

    def _setup_footer(self):
        """Alt kısım: Sistem Durumu Kartı"""
        footer_container = QWidget()
        f_layout = QVBoxLayout(footer_container)
        f_layout.setContentsMargins(15, 15, 15, 20)
        
        # Durum Kartı Background
        self.status_card = QFrame()
        self.status_card.setObjectName("StatusCard")
        
        card_layout = QHBoxLayout(self.status_card)
        card_layout.setContentsMargins(15, 12, 15, 12)
        card_layout.setSpacing(10)
        
        # Metin (Solda)
        self.lbl_status = QLabel()
        self.lbl_status.setFont(OBISFonts.get_font(10, "bold"))
        
        # İndikatör (Sağda nokta)
        self.status_indicator = StatusIndicator()
        
        card_layout.addWidget(self.lbl_status)
        card_layout.addStretch()
        card_layout.addWidget(self.status_indicator)
        
        f_layout.addWidget(self.status_card)
        self.layout.addWidget(footer_container)
        
        # Başlangıç durumu
        self.set_system_status(False)

    def set_system_status(self, is_running: bool):
        """Sistem durumunu günceller ve renkleri değiştirir."""
        
        if is_running:
            bg_color = OBISColors.SUCCESS_BG
            fg_color = OBISColors.SUCCESS
            status_text = "Sistem Çalışıyor"
        else:
            bg_color = OBISColors.DANGER_BG
            fg_color = OBISColors.DANGER
            status_text = "Sistem Durduruldu"

        # 1. Kart Stilini Güncelle
        self.status_card.setStyleSheet(f"""
            QFrame#StatusCard {{
                background-color: {bg_color};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                border: 1px solid {bg_color};
            }}
        """)
        
        # 2. İndikatörü ve Animasyonu Güncelle
        self.status_indicator.color = QColor(fg_color)
        OBISAnimations.start_pulse_shadow(self.status_indicator, fg_color, radius=25, duration=1500)

        # 3. Etiketi Güncelle
        self.lbl_status.setText(status_text)
        self.lbl_status.setStyleSheet(f"color: {fg_color}; background: transparent; border: none;")