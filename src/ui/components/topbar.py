"""
BU DOSYA: Ekranın sağ üst köşesindeki kullanıcı bilgi çubuğu.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from ..styles.theme import OBISColors, OBISDimens, OBISFonts
import qtawesome as qta

class OBISTopBar(QFrame):
    """
    Üst Bar. Sayfa başlığı, Son Kontrol Bilgisi ve Profil Widget'ını içerir.
    """
    # Profil tıklanması için sinyal
    profile_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(OBISDimens.TOPBAR_HEIGHT)
        # Sadece TopBar ID'sine sahip elemana stil uygula (Child widgetlara sızmasını engeller)
        self.setStyleSheet(f"""
            #TopBar {{
                background-color: {OBISColors.SURFACE}; 
                border-bottom: 1px solid {OBISColors.BORDER};
            }}
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(30, 0, 30, 0)
        
        # --- 1. SOL TARAF (Başlık + Son Kontrol) ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 15, 0, 15)
        left_layout.setSpacing(2)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Sayfa Başlığı
        self.lbl_title = QLabel("Ana Menü")
        self.lbl_title.setFont(OBISFonts.H2)
        self.lbl_title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; border: none; background: transparent;")
        
        # Alt Bilgi (İkon + Metin)
        info_container = QWidget()
        info_layout = QHBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)
        
        # Saat İkonu
        lbl_icon = QLabel()
        icon = qta.icon("fa5s.history", color=OBISColors.TEXT_SECONDARY)
        lbl_icon.setPixmap(icon.pixmap(QSize(14, 14)))
        lbl_icon.setStyleSheet("border: none; background: transparent;")
        
        # Bilgi Metni
        self.lbl_last_check = QLabel("Son Kontrol:-")
        self.lbl_last_check.setFont(OBISFonts.SMALL)
        self.lbl_last_check.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; border: none; background: transparent;")
        
        info_layout.addWidget(lbl_icon)
        info_layout.addWidget(self.lbl_last_check)
        info_layout.addStretch()
        
        left_layout.addWidget(self.lbl_title)
        left_layout.addWidget(info_container)
        
        # --- 2. SAĞ TARAF (Bildirim + Ayraç + Profil) ---
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Bildirim İkonu
        btn_bell = QPushButton()
        btn_bell.setIcon(qta.icon("fa5s.bell", color=OBISColors.TEXT_SECONDARY))
        btn_bell.setIconSize(QSize(20, 20))
        btn_bell.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_bell.setStyleSheet("border: none; background: transparent;")
        
        # Dikey Ayraç
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedHeight(30)
        separator.setStyleSheet(f"color: {OBISColors.BORDER}; border: 0px; background-color: {OBISColors.BORDER}; width: 1px;")

        # Profil Kartı (Frame olarak yeniden tasarlandı)
        self.profile_widget = QFrame()
        self.profile_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_widget.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: {OBISColors.HOVER_LIGHT};
            }}
        """)
        
        self.profile_widget.mousePressEvent = lambda event: self.profile_clicked.emit()

        p_layout = QHBoxLayout(self.profile_widget)
        p_layout.setContentsMargins(10, 5, 10, 5) # .Tıklanabilir alan için iç boşluk
        p_layout.setSpacing(15) # İsim ve Avatar arası boşluk
        
        # İsim Label
        text_container = QWidget()
        t_layout = QVBoxLayout(text_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(2)
        t_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.lbl_name = QLabel("Misafir Kullanıcı")
        self.lbl_name.setFont(OBISFonts.get_font(10, "bold"))
        self.lbl_name.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; border: none; background: transparent;")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.lbl_student_id = QLabel("Öğrenci No: --")
        self.lbl_student_id.setFont(OBISFonts.SMALL)
        self.lbl_student_id.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; border: none; background: transparent;")
        self.lbl_student_id.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        t_layout.addWidget(self.lbl_name)
        t_layout.addWidget(self.lbl_student_id)
        
        # Avatar
        self.avatar = QLabel()
        self.avatar.setFixedSize(42, 42)
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {OBISColors.AVATAR_BG};
                border-radius: 21px; 
                border: 2px solid {OBISColors.SURFACE}; 
                outline: 1px solid {OBISColors.PRIMARY}; 
            }}
        """)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Avatar İkon
        avatar_icon = qta.icon("fa5s.user-graduate", color=OBISColors.SURFACE) # Öğrenci ikonu
        self.avatar.setPixmap(avatar_icon.pixmap(QSize(22, 22)))
        
        p_layout.addWidget(text_container)
        p_layout.addWidget(self.avatar)
        
        right_layout.addWidget(btn_bell)
        right_layout.addWidget(separator)
        right_layout.addWidget(self.profile_widget)
        
        self.layout.addWidget(left_container)
        self.layout.addStretch()
        self.layout.addWidget(right_container)

    def set_title(self, title: str):
        self.lbl_title.setText(title)

    def set_user_info(self, name: str, student_id: str):
        self.lbl_name.setText(name)
        self.lbl_student_id.setText(f"Öğrenci No: {student_id}")

    def set_last_check_time(self, time_str: str):
        """Son kontrol saatini günceller. Örn: '14:47 (Başarılı)'"""
        self.lbl_last_check.setText(f"Son kontrol: {time_str}")