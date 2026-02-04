"""
BU DOSYA: Ekranın altında beliren, kullanıcıya bilgi veren 
geçici bildirim balonu. Material Design Snackbar mantığında çalışır.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
import qtawesome as qta

class OBISSnackbar(QWidget):
    """
    Ekranın altından yukarı kayarak gelen ve bir süre sonra kaybolan bildirim.
    Parent widget üzerine (overlay) olarak eklenir. (Child Widget)
    """
    
    # .Tipler
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Normal child widget olarak davranmalı
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Başlangıçta gizli
        self.hide()
        
        # .Timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._slide_out)
        
        # Ana Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container Frame
        self.container = QFrame()
        self.container.setObjectName("container") 
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 12, 16, 12)
        self.container_layout.setSpacing(8)
        
        self.main_layout.addWidget(self.container)
        
        # UI Elemanları
        self.icon_label = QLabel()
        self.msg_label = QLabel()
        self.msg_label.setFont(OBISFonts.get_font(9, "bold"))
        self.msg_label.setStyleSheet("border: none; background: transparent; color: white;")
        
        # Widgetları frame'e ekle
        self.container_layout.addWidget(self.icon_label)
        self.container_layout.addWidget(self.msg_label)
        
    def show_message(self, message: str, type: str = "info", duration: int = 3000):
        """Bildirimi gösterir."""
        
        # Renk ve İkon seçimi
        bg_color = OBISColors.PRIMARY
        icon_name = "fa5s.info-circle"
        
        if type == self.SUCCESS:
            bg_color = OBISColors.SUCCESS
            icon_name = "fa5s.check-circle"
        elif type == self.ERROR:
            bg_color = OBISColors.DANGER
            icon_name = "fa5s.exclamation-circle"
        elif type == self.WARNING:
            bg_color = OBISColors.WARNING
            icon_name = "fa5s.exclamation-triangle"
            
        # Stil Uygula - QFrame üzerine
        self.container.setStyleSheet(f"""
            QFrame#container {{
                background-color: {bg_color};
                border-radius: {OBISDimens.RADIUS_SMALL}px;
                border: 1px solid {OBISColors.WHITE_ALPHA_20};
            }}
            QLabel {{
                background-color: transparent;
                color: white;
            }}
        """)
        
        # İçeriği set et
        self.msg_label.setText(message)
        try:
            self.icon_label.setFixedSize(24, 24) # İkon boyutunu sabitle
            self.icon_label.setPixmap(qta.icon(icon_name, color="white").pixmap(24, 24))
        except Exception:
            pass
        
        # Boyut ve Konum (Parent'a göre)
        if self.parent():
            parent_rect = self.parent().rect()
            
            # Genişlik Sınırları ve Word Wrap Ayarı
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            
            # İçeriğe göre boyutlandır
            self.msg_label.setWordWrap(False) 
            self.adjustSize()
            
            # Genişliği bulunan doğal boyuta sabitle
            self.setFixedWidth(self.width())
            
            # Konum: Alt orta (Local Koordinatlar)
            target_x = (parent_rect.width() - self.width()) // 2
            self.target_y = parent_rect.height() - self.height() - 20 # 20px margin bottom
            self.start_y = parent_rect.height() # Ekranın hemen altı
            
            self.move(target_x, self.start_y)
            self.raise_() # En üste çıkart
            self.show()
            
            # Animasyon (Yukarı kayma)
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(300)
            self.anim.setStartValue(QPoint(target_x, self.start_y))
            self.anim.setEndValue(QPoint(target_x, int(self.target_y)))
            self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.anim.start()
            
            # Otomatik kapanma zamanlayıcısı
            self.timer.start(duration)
            
    def _slide_out(self):
        """Aşağı kayarak kaybolur."""
        if not self.parent(): return
        
        current_pos = self.pos()
        target_y = self.parent().height()
        target_pos = QPoint(current_pos.x(), target_y)
        
        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(300)
        self.anim_out.setStartValue(current_pos)
        self.anim_out.setEndValue(target_pos)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim_out.finished.connect(self.hide)
        self.anim_out.start()