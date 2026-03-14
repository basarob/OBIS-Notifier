"""
BU DOSYA: Özelleştirilmiş ComboBox bileşeni içerir.
Standart QComboBox üzerine modern tema uygulanmıştır.
"""

from PyQt6.QtWidgets import QComboBox, QListView
from PyQt6.QtCore import Qt
from ..styles.theme import OBISColors, OBISDimens, OBISFonts

class OBISCombobox(QComboBox):
    """
    Modern tasarımlı, yuvarlatılmış köşeli ComboBox.
    """
    def __init__(self, items=None, parent=None, height=45):
        super().__init__(parent)
        
        if items:
            self.addItems(items)
            
        self.setFixedHeight(height)
        self.setFont(OBISFonts.BODY)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Liste Görünümü (Popup) Ayarları
        self.setView(QListView())
        
        # Stil Uygulama
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {OBISColors.INPUT_BG};
                color: {OBISColors.TEXT_PRIMARY};
                border-radius: {OBISDimens.RADIUS_SMALL}px;
                padding-left: 35px; /* İkon için ekstra boşluk */
                border: 1px solid {OBISColors.BORDER};
            }}
            
            QComboBox:hover {{
                background-color: {OBISColors.HOVER_LIGHT};
                border: 1px solid {OBISColors.PRIMARY_HOVER};
            }}
            
            QComboBox:on {{ /* Açıkken */
                border: 1px solid {OBISColors.PRIMARY};
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 36px;
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: none; /* SVG bulunamadığı için kaldırıldı. Qtawesome kullanılacak */
            }}
            
            /* --- Popup Listesi --- */
            QComboBox QAbstractItemView {{
                background-color: {OBISColors.SURFACE};
                border: 1px solid rgba(0,0,0,0.06);
                outline: none;
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                padding: 8px 4px;
            }}
            
            QComboBox QAbstractItemView::item {{
                min-height: 36px;
                padding-left: 12px;
                border-radius: {OBISDimens.RADIUS_SMALL}px;
                margin: 2px 4px;
                color: {OBISColors.TEXT_PRIMARY};
            }}
            
            QComboBox QAbstractItemView::item:hover {{
                background-color: {OBISColors.HOVER_LIGHT};
                color: {OBISColors.PRIMARY};
            }}
            
            QComboBox QAbstractItemView::item:selected {{
                background-color: {OBISColors.HOVER_BLUE};
                color: {OBISColors.PRIMARY};
                font-weight: bold;
            }}
        """)
        
        # İç ikon eklentisi
        self.icon_label = None
        self.right_icon_label = None
        
        # Sağ Ok İkonu Ekleme (Sahte down-arrow)
        self._add_right_caret()

    def _add_right_caret(self):
        """Standard SVG yerine QTAwesome kullanan açılır simge"""
        from PyQt6.QtWidgets import QLabel
        import qtawesome as qta
        self.right_icon_label = QLabel(self)
        self.right_icon_label.setStyleSheet("background: transparent; border: none;")
        self.right_icon_label.setFixedSize(16, 16)
        self.right_icon_label.setPixmap(qta.icon("fa5s.chevron-down", color=OBISColors.TEXT_SECONDARY).pixmap(12, 12))
        
        # Parent resize olduğunda ikonun yerini hep sağa hizalamak için event
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self and event.type() == QEvent.Type.Resize:
            if self.right_icon_label:
                # İkonu sağa yasla (Sağdan 12px içeride, dikeyde ortada)
                self.right_icon_label.move(self.width() - 24, (self.height() - 16) // 2)
        return super().eventFilter(obj, event)

    def set_left_icon(self, qta_icon_name: str, color: str = OBISColors.TEXT_SECONDARY):
        """Combobox'ın sol tarafına QTAwesome ikonu ekler."""
        if not self.icon_label:
            from PyQt6.QtWidgets import QLabel
            import qtawesome as qta
            self.icon_label = QLabel(self)
            self.icon_label.setStyleSheet("background: transparent; border: none;")
            
            # İkonun konumunu ayarla
            self.icon_label.move(12, (self.height() - 16) // 2) 
            self.icon_label.setFixedSize(16, 16)
            
        import qtawesome as qta
        self.icon_label.setPixmap(qta.icon(qta_icon_name, color=color).pixmap(16, 16))
