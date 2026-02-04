"""
BU DOSYA: İçerik gruplamak için kullanılan modern, gölgeli kart bileşeni.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget
from ..styles.theme import OBISColors, OBISDimens
from ..utils.qt_utils import add_drop_shadow

class OBISCard(QFrame):
    """
    Standart beyaz, yuvarlak köşeli ve gölgeli kart.
    """
    def __init__(self, parent=None, has_shadow=True):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            OBISCard {{
                background-color: {OBISColors.SURFACE};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                border: 1px solid {OBISColors.BORDER};
            }}
        """)
        
        # İçerik Layout'u
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(OBISDimens.PADDING_MEDIUM, 
                                       OBISDimens.PADDING_MEDIUM, 
                                       OBISDimens.PADDING_MEDIUM, 
                                       OBISDimens.PADDING_MEDIUM)
        
        if has_shadow:
            add_drop_shadow(self, blur_radius=50, y_offset=4, alpha=15) # Geniş ve hafif gölge

    def add_widget(self, widget: QWidget):
        """Karta widget ekler (Layout mantığı)."""
        self.layout.addWidget(widget)

    def set_content(self, widget: QWidget):
        """Mevcut içeriği temizler ve yeni widget'ı ekler."""
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.layout.addWidget(widget)