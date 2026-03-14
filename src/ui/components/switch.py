"""
BU DOSYA: iOS tarzı animasyonlu Switch (Toggle) bileşeni içerir.
QCheckBox yerine tamamen özelleştirilmiş bir widget'tır.
"""

from PyQt6.QtWidgets import QWidget, QCheckBox
from PyQt6.QtCore import Qt, QSize, QPoint, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent

from ..styles.theme import OBISColors, OBISDimens

class OBISSwitch(QWidget):
    """
    iOS tarzı animasyonlu Switch (Toggle) bileşeni.
    """
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, width=40, height=22):
        super().__init__(parent)
        
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Durum
        self._checked = False
        self._enabled = True
        
        # Animasyon Değişkeni (Knob Pozisyonu - Float 0.0 sol, 1.0 sağ)
        self._position = 0.0 
        
        # Animasyon Nesnesi
        self._anim = QPropertyAnimation(self, b"position")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Renkler
        self._bg_color = QColor(OBISColors.INPUT_BG)
        self._circle_color = QColor(OBISColors.SURFACE)
        self._active_color = QColor(OBISColors.PRIMARY)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, checked: bool):
        """Durumu programsal olarak değiştirir (Sinyal tetiklemez, sadece görsel)."""
        self._checked = checked
        self._position = 1.0 if checked else 0.0
        self.update()

    def set_active_color(self, color_hex: str):
        """Aktif olduğundaki arka plan rengini değiştirir."""
        self._active_color = QColor(color_hex)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Tıklama olayı ile durumu değiştir ve animasyonu başlat."""
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            
            # Animasyonu Başlat
            self._anim.stop()
            self._anim.setStartValue(self.position)
            self._anim.setEndValue(1.0 if self._checked else 0.0)
            self._anim.start()
            
            self.toggled.emit(self._checked) # Sinyal gönder
            
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Switch'i çizer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Arka Planı Çiz
        # Geçiş efekti için renk interpolasyonu
        if self._position > 0.5:
            # Aktif renge yakın
            bg = self._active_color
        else:
            # Pasif renge yakın (Gri)
            # INPUT_BG çok açık, biraz koyultalım ki beyaz zeminde görünsün
            bg = QColor("#E5E7EB") 
            
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        
        rect = self.rect()
        radius = rect.height() / 2
        painter.drawRoundedRect(rect, radius, radius)
        
        # 2. Yuvarlak Düğmeyi (Knob) Çiz
        # Padding (Kenar boşluğu)
        padding = 2
        knob_size = rect.height() - (padding * 2)
        
        # Hareket alanı
        x_min = padding
        x_max = rect.width() - knob_size - padding
        
        # Pozisyona göre X koordinatı
        current_x = x_min + (x_max - x_min) * self._position
        
        knob_rect = QRect(int(current_x), padding, knob_size, knob_size)
        
        painter.setBrush(QBrush(self._circle_color))
        # Hafif gölge efekti için ince border
        painter.setPen(QPen(QColor(0,0,0, 20), 1)) 
        painter.drawEllipse(knob_rect)
