"""
BU DOSYA: Farklı stillerde (Primary, Danger, Ghost) buton bileşeni.
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QCursor
import qtawesome as qta
from ..styles.theme import OBISColors, OBISDimens, OBISFonts

class OBISButton(QPushButton):
    """
    Özelleştirilmiş buton bileşeni.
    Stiller: 'primary', 'danger', 'ghost', 'outline'
    """
    def __init__(self, text: str = "", button_type: str = "primary", icon=None, parent=None):
        super().__init__(text, parent)
        
        self.button_type = button_type
        self.setFont(OBISFonts.BUTTON)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(40) # Standart yükseklik
        
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))
            
        self._apply_style()

    def _apply_style(self):
        """CSS stillerini tipe göre uygular."""
        
        radius = OBISDimens.RADIUS_MEDIUM
        base_style = f"""
            QPushButton {{
                border-radius: {radius}px;
                padding: 0 16px;
                background-color: transparent;
                border: none;
            }}
        """

        if self.button_type == "primary":
            style = base_style + f"""
                QPushButton {{
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {OBISColors.PRIMARY}, stop:1 {OBISColors.PRIMARY_HOVER});
                    color: {OBISColors.TEXT_WHITE};
                }}
                QPushButton:hover {{
                    background-color: {OBISColors.PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {OBISColors.PRIMARY_PRESSED};
                }}
            """
        
        elif self.button_type == "danger":
             style = base_style + f"""
                QPushButton {{
                    background-color: {OBISColors.DANGER};
                    color: {OBISColors.TEXT_WHITE};
                }}
                QPushButton:hover {{
                    background-color: {OBISColors.DANGER_HOVER};
                }}
            """
             
        elif self.button_type == "outline":
            style = base_style + f"""
                QPushButton {{
                    border: 1px solid {OBISColors.BORDER};
                    color: {OBISColors.TEXT_PRIMARY};
                    background-color: {OBISColors.SURFACE};
                }}
                QPushButton:hover {{
                    background-color: {OBISColors.BACKGROUND};
                    border-color: {OBISColors.PRIMARY};
                }}
            """
            
        elif self.button_type == "ghost":
            style = base_style + f"""
                QPushButton {{
                    color: {OBISColors.PRIMARY};
                    background-color: transparent;
                }}
                QPushButton:hover {{
                    background-color: {OBISColors.HOVER_BLUE}; /* Açık mavi hover */
                }}
            """
        
        else: # Default
             style = base_style
             
        self.setStyleSheet(style)

class OBISIconButton(QPushButton):
    """
    Sadece ikon içeren, yuvarlak veya kare buton.
    Kullanım: Şifre göster/gizle, kapatma butonu vb.
    """
    def __init__(self, icon_name: str, size: int = 30, color: str = OBISColors.TEXT_SECONDARY, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # İkon ayarla
        icon_obj = qta.icon(icon_name, color=color)
        self.setIcon(icon_obj)
        self.setIconSize(QSize(size-10, size-10))
        
        # Stil (Hover efekti)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {size//2}px;
            }}
            QPushButton:hover {{
                background-color: {OBISColors.HOVER_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {OBISColors.PRESSED_LIGHT};
            }}
        """)

    def update_icon(self, icon_name: str, color: str = OBISColors.TEXT_SECONDARY):
        """İkonu dinamik değiştirir."""
        icon_obj = qta.icon(icon_name, color=color)
        self.setIcon(icon_obj)