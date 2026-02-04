"""
BU DOSYA: Solunda ikon olabilen, modern görünümlü input bileşeni.
"""

from PyQt6.QtWidgets import QLineEdit, QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from ..styles.theme import OBISColors, OBISDimens, OBISFonts
from .button import OBISIconButton
import qtawesome as qta

class OBISInput(QFrame):
    """
    İkon ve Placeholder destekli gelişmiş input alanı.
    Görünüş olarak bir Frame içindeki LineEdit'tir.
    """
    
    returnPressed = pyqtSignal()

    def __init__(self, placeholder: str = "", icon_name: str = None, is_password: bool = False, height: int = 48, bg_color: str = None, parent=None):
        super().__init__(parent)
                
        self.setFixedHeight(height) # Yükseklik (Parametrik)
        self.setObjectName("InputContainer")
        
        # Arkaplan rengini belirle
        default_bg = bg_color if bg_color else OBISColors.INPUT_BG
        
        # Container Stili
        self._default_style = f"""
            #InputContainer {{
                background-color: {default_bg};
                border: 2px solid transparent;
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
            }}
            #InputContainer:hover {{
                border: 2px solid {OBISColors.BORDER};
            }}
        """
        
        self._focus_style = f"""
            #InputContainer {{
                background-color: {OBISColors.SURFACE};
                border: 1.5px solid {OBISColors.PRIMARY};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
            }}
        """
        self._error_style = f"""
            #InputContainer {{
                background-color: {OBISColors.SURFACE};
                border: 1.5px solid {OBISColors.DANGER};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
            }}
        """
        self.setStyleSheet(self._default_style)
        self.is_error = False

        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 15, 0)
        self.layout.setSpacing(10)

        # İkon (Varsa)
        if icon_name:
            self.icon_label = QLabel()
            icon = qta.icon(icon_name, color=OBISColors.TEXT_SECONDARY)
            self.icon_label.setPixmap(icon.pixmap(QSize(20, 20)))
            self.icon_label.setStyleSheet("background-color: transparent; border: none;") # Arkaplan düzeltmesi
            self.layout.addWidget(self.icon_label)

        # LineEdit (Giriş Alanı)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setFont(OBISFonts.BODY)
        
        if is_password:
            self.set_password_mode(True)
        
        # LineEdit Stili (Transparan)
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                color: {OBISColors.TEXT_PRIMARY};
                padding: 0px;
            }}
            QLineEdit::placeholder {{
                color: {OBISColors.TEXT_GHOST};
            }}
        """)
        
        # Focus olaylarını dinle
        self.line_edit.focusInEvent = self._on_focus_in
        self.line_edit.focusOutEvent = self._on_focus_out
        
        # Metin değişince hatayı sil
        self.line_edit.textChanged.connect(lambda: self.set_error(False))
        
        # Enter tuşunu dışarı aktar
        self.line_edit.returnPressed.connect(self.returnPressed.emit)
        
        self.layout.addWidget(self.line_edit)

    def set_password_mode(self, enabled: bool):
        """Şifre modunu ve fontunu ayarlar."""
        if enabled:
            self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            # Noktalar için daha küçük font
            self.line_edit.setFont(OBISFonts.get_font(OBISDimens.TEXT_PASSWORD, "normal"))
        else:
            self.line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            # Normal metin için standart font
            self.line_edit.setFont(OBISFonts.BODY)
        
    def _on_focus_in(self, event):
        """Odaklanınca çerçeve rengini değiştir (Hata yoksa)."""
        if not self.is_error:
            self.setStyleSheet(self._focus_style)
            self.style().polish(self) # Stili zorla güncelle
        QLineEdit.focusInEvent(self.line_edit, event) # Orijinal eventi çağır

    def set_error(self, has_error: bool):
        """Hata durumunu yönetir (Kırmızı çerçeve)."""
        self.is_error = has_error
        if has_error:
            self.setStyleSheet(self._error_style)
        else:
            if self.line_edit.hasFocus():
                self.setStyleSheet(self._focus_style)
            else:
                self.setStyleSheet(self._default_style)

    def add_action_button(self, icon_name: str, callback):
        """Sağ tarafa buton ekler (Örn: Göz ikonu)."""
        btn = OBISIconButton(icon_name, size=30, parent=self)
        btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn

    def _on_focus_out(self, event):
        """Odak çıkınca eski haline dön."""
        if not self.is_error:
            self.setStyleSheet(self._default_style)
            self.style().polish(self) # Stili zorla güncelle
        QLineEdit.focusOutEvent(self.line_edit, event)

    def text(self) -> str:
        return self.line_edit.text()
    
    def setText(self, text: str):
        self.line_edit.setText(text)