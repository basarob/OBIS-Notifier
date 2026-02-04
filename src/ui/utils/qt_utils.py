"""
BU DOSYA: PyQt6 için yardımcı fonksiyonlar ve efektler (Gölge vb.).
"""

from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget, QLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ..styles.theme import OBISColors

def add_drop_shadow(widget: QWidget, 
                    blur_radius: int = 20, 
                    x_offset: int = 0, 
                    y_offset: int = 4, 
                    color: str = OBISColors.SHADOW, 
                    alpha: int = 15): 
    """
    Bir widget'a modern drop shadow efekti ekler.
    
    Args:
        widget: Efektin uygulanacağı widget
        blur_radius: Bulanıklık yarıçapı
        x_offset, y_offset: Gölge konumu
        color: Gölge rengi (Hex)
        alpha: Opaklık (0-255)
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    
    qcolor = QColor(color)
    qcolor.setAlpha(alpha)
    shadow.setColor(qcolor)
    
    widget.setGraphicsEffect(shadow)

def clear_layout(layout: QLayout):
    """Bir layout içindeki tüm widget'ları temizler."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        elif item.layout():
            clear_layout(item.layout())