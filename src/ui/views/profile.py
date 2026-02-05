"""
BU DOSYA: Kullanıcı profil bilgilerini gösterir ve 
çıkış (logout) işlemini yönetir.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ..components.card import OBISCard
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens, OBISStyles
from ..utils.animations import OBISAnimations
import qtawesome as qta

class ProfileView(QWidget):
    """
    Profile sayfası. Logout butonu içerir.
    """
    logout_requested = pyqtSignal() # Çıkış isteği
    back_requested = pyqtSignal()   # Geri dön isteği

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Arkaplan
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(OBISStyles.MAIN_BACKGROUND)
        
        # Ana Layout (Ekranı ortalar)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self._setup_ui()
        
    def showEvent(self, event):
        """Sayfa her görüntülendiğinde çalışır."""
        super().showEvent(event)
        
        # Animasyonları tetikle
        # Geri Butonu: Soldan kayarak gelir
        OBISAnimations.slide_in(self.btn_back, direction="right", offset=50, duration=600, delay=100)
        OBISAnimations.fade_in(self.btn_back, duration=500, delay=100)
        
        # Kart: Aşağıdan yukarı ve fade efekti
        OBISAnimations.entrance_anim(self.card, delay=200)

    def _setup_ui(self):
        """Arayüz elemanlarını oluşturur."""
        
        container_widget = QWidget()
        container_widget.setFixedWidth(460)
        container_widget.setStyleSheet("background: transparent;")
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setSpacing(2) # Buton ile kart arası boşluk
        container_layout.setContentsMargins(30, 10, 30, 40)
        
        # 1. Geri Dön Butonu (Kartın Sol Üstü)
        self.btn_back = OBISButton(" Geri Dön", "ghost", icon=qta.icon("fa5s.arrow-left", color=OBISColors.PRIMARY))
        # Buton stilini özelleştir
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                color: {OBISColors.PRIMARY};
                font-family: 'Inter', 'Segoe UI';
                font-size: {OBISDimens.TEXT_H3}px;
                font-weight: 600;
                background: transparent;
                border: none;
                text-align: left;
                padding: 0px; 
            }}
        """)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_requested.emit)
        self.btn_back.setFixedWidth(120) # Sola yaslanması için sınırlı genişlik

        # 2. Profil Kartı
        self.card = OBISCard(has_shadow=True)
        self.card.setFixedSize(400, 450)
        
        # Kart stili
        self.card.setStyleSheet(f"""
            OBISCard {{
                background-color: {OBISColors.SURFACE};
                border-radius: {OBISDimens.RADIUS_X_LARGE}px; 
                border: 0px; 
            }}
        """)
        
        self._setup_card_content()
        
        # Konteynere ekle
        container_layout.addWidget(self.btn_back, 0, Qt.AlignmentFlag.AlignLeft)
        container_layout.addWidget(self.card)
        
        # Ana Layout'a konteyneri ekle
        self.main_layout.addWidget(container_widget)

    def _setup_card_content(self):
        """Kartın iç yapısını oluşturur."""
        # Kart içeriği için container
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # 1. Avatar
        avatar = self._create_avatar_section()
        
        # 2. Üye Bilgileri
        self._create_info_section()
        
        # 3. Butonlar
        self._create_actions_section()
        
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(50)
        layout.addWidget(self.lbl_name)
        layout.addSpacing(5)
        layout.addWidget(self.lbl_id)
        layout.addSpacing(30)
        layout.addWidget(self.lbl_updated)
        layout.addSpacing(10)
        layout.addWidget(self.btn_update)
        layout.addSpacing(30)
        layout.addWidget(self.line_sep, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.btn_logout)
        
        self.card.add_widget(container)

    def _create_avatar_section(self) -> QLabel:
        """Avatar container oluşturur."""
        avatar_container = QLabel()
        avatar_container.setFixedSize(120, 120)
        avatar_container.setStyleSheet(f"""
            background-color: {OBISColors.AVATAR_BG}; 
            border-radius: {OBISDimens.RADIUS_FULL}px;
            border: 4px solid {OBISColors.SURFACE};
        """)
        
        icon_lbl = QLabel(avatar_container)
        icon_lbl.setPixmap(qta.icon("fa5s.user-graduate", color="white").pixmap(QSize(50, 50)))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setGeometry(0, 0, 120, 120)
        
        return avatar_container

    def _create_info_section(self):
        """İsim, numara ve tarih labellarını oluşturur."""
        self.lbl_name = QLabel("Ad Soyad")
        self.lbl_name.setFont(OBISFonts.get_font(18, "bold"))
        self.lbl_name.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; margin-top: 20px;")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_id = QLabel("Numara")
        self.lbl_id.setFont(OBISFonts.BODY)
        self.lbl_id.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}")
        self.lbl_id.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Son Güncelleme
        self.lbl_updated = QLabel("Tarih")
        self.lbl_updated.setFont(OBISFonts.get_font(8, "bold"))
        self.lbl_updated.setStyleSheet(f"color: {OBISColors.TEXT_GHOST}; letter-spacing: 0.5px;") 
        self.lbl_updated.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def _create_actions_section(self):
        """Aksiyon butonlarını oluşturur."""
        # 1. Bilgilerimi Güncelle
        self.btn_update = OBISButton(" Bilgilerimi Güncelle", "primary", icon=qta.icon("fa5s.sync-alt", color="white"))
        self.btn_update.setFixedHeight(50) 
        self.btn_update.setFont(OBISFonts.get_font(11, "bold"))
        
        # Ayırıcı çizgi
        self.line_sep = QFrame()
        self.line_sep.setFrameShape(QFrame.Shape.HLine)
        self.line_sep.setStyleSheet(f"color: {OBISColors.LINE}; max-height: 5px;")
        self.line_sep.setFixedWidth(150)
        
        # 2. Çıkış Yap
        self.btn_logout = OBISButton(" Çıkış Yap", "ghost", icon=qta.icon("fa5s.sign-out-alt", color=OBISColors.DANGER))
        self.btn_logout.setStyleSheet(f"""
            QPushButton {{
                color: {OBISColors.DANGER};
                background: transparent;
                border: none;
                font-weight: bold;
                font-family: 'Inter', 'Segoe UI';
            }}
            QPushButton:hover {{
                background: transparent;
            }}
        """)
        self.btn_logout.clicked.connect(self.logout_requested.emit)

    def set_user_data(self, name: str, student_num: str, last_update: str = ""):
        """Kullanıcı bilgilerini günceller."""
        if name:
            self.lbl_name.setText(name)
        if student_num:
            self.lbl_id.setText(f"Öğrenci Numarası: {student_num}")
        if last_update:
            self.lbl_updated.setText(f"SON GÜNCELLEME: {last_update}")