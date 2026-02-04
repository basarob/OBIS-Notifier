"""
BU DOSYA: Uygulama genelinde kullanılacak animasyon yardımcılarını 
içerir. UI bileşenlerine Fade, Slide ve Shake gibi efektleri
kolayca uygulamak için tasarlanmıştır.
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QTimer, QAbstractAnimation, QParallelAnimationGroup
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

class OBISAnimations:
    """
    Widget animasyonlarını yöneten yardımcı sınıf.
    Kullanım: OBISAnimations.fade_in(my_widget)
    """

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 500, delay: int = 0):
        """
        Widget'ı opaklığını artırarak görünür yapar.
        """
        # Efekt varsa kullan, yoksa oluştur
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        # Başlangıç değeri
        effect.setOpacity(0)
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if delay > 0:
            QTimer.singleShot(delay, anim.start)
        else:
            anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            
        # Referansı korumak için widget'a ata
        widget._fade_anim = anim 

    @staticmethod
    def slide_in(widget: QWidget, direction: str = "up", offset: int = 30, duration: int = 600, delay: int = 0):
        """
        Widget'ı belirtilen yönden kayarak getirir.
        direction: 'up', 'down', 'left', 'right'
        """
        # Layout'un widget'ı yerleştirmesini bekle
        widget.updateGeometry()
        end_pos = widget.pos()
        start_pos = QPoint(end_pos)

        if direction == "up":
            start_pos.setY(end_pos.y() + offset) # Aşağıdan yukarı
        elif direction == "down":
            start_pos.setY(end_pos.y() - offset) # Yukarıdan aşağı
        elif direction == "left":
            start_pos.setX(end_pos.x() - offset) # Sağdan sola
        elif direction == "right":
            start_pos.setX(end_pos.x() + offset) # Soldan sağa
            
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(QEasingCurve.Type.OutBack) # Hafif yaylanma efekti
         
        def start_anim():
            widget.move(start_pos)
            widget.show() # Emin olmak için
            anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            
        widget._slide_anim = anim
        
        if delay > 0:
            QTimer.singleShot(delay, start_anim)
        else:
            start_anim()

    @staticmethod
    def entrance_anim(widget: QWidget, delay: int = 0):
        """
        Standart giriş animasyonu: Fade In + Slide Up
        """
        OBISAnimations.fade_in(widget, duration=600, delay=delay)
        OBISAnimations.slide_in(widget, direction="up", offset=40, duration=700, delay=delay)

    @staticmethod
    def shake(widget: QWidget, duration: int = 400, intensity: int = 5):
        """
        Widget'ı sağa sola sallar (Hatalı giriş vb. için).
        """
        pos = widget.pos()
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setLoopCount(1)
        
        # Key frame'ler
        anim.setKeyValueAt(0, pos)
        anim.setKeyValueAt(0.15, QPoint(pos.x() + intensity, pos.y()))
        anim.setKeyValueAt(0.3, QPoint(pos.x() - intensity, pos.y()))
        anim.setKeyValueAt(0.45, QPoint(pos.x() + int(intensity*0.6), pos.y()))
        anim.setKeyValueAt(0.6, QPoint(pos.x() - int(intensity*0.6), pos.y()))
        anim.setKeyValueAt(0.75, QPoint(pos.x() + int(intensity*0.3), pos.y()))
        anim.setKeyValueAt(0.9, QPoint(pos.x() - int(intensity*0.3), pos.y()))
        anim.setKeyValueAt(1, pos)
        
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        widget._shake_anim = anim

    @staticmethod
    def start_pulse_shadow(widget: QWidget, color_hex: str, radius: int = 20, duration: int = 1500):
        """
        Widget'a gelişmiş nefes alan (pulse) glow efekti uygular.
        Hem Shadow Opacity'si hem de Widget'ın kendi rengi (varsa) senkronize animasyonlanır.
        """
        # 1. Shadow Efekti Hazırla (Eski efekti temizle)
        if widget.graphicsEffect():
            widget.setGraphicsEffect(None)
            
        effect = QGraphicsDropShadowEffect(widget)
        widget.setGraphicsEffect(effect)
        
        # Sabitler
        effect.setOffset(0, 0)
        effect.setBlurRadius(radius)
        
        base_color = QColor(color_hex)
        
        # --- Animasyon Grubu ---
        group = QParallelAnimationGroup(widget)
        
        # A) Shadow Opacity Animasyonu (%8 -> %70)
        shadow_anim = QPropertyAnimation(effect, b"color")
        shadow_anim.setDuration(duration)
        shadow_anim.setLoopCount(-1)
        shadow_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        s_start = QColor(base_color)
        s_start.setAlpha(20) 
        s_mid = QColor(base_color)
        s_mid.setAlpha(180) 
        
        shadow_anim.setKeyValueAt(0.0, s_start)
        shadow_anim.setKeyValueAt(0.5, s_mid)
        shadow_anim.setKeyValueAt(1.0, s_start)
        
        group.addAnimation(shadow_anim)
        
        # B) Widget Color Animasyonu (Eğer 'color' property'si varsa)
        if widget.metaObject().indexOfProperty("color") != -1:
            widget_anim = QPropertyAnimation(widget, b"color")
            widget_anim.setDuration(duration)
            widget_anim.setLoopCount(-1)
            widget_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            
            w_start = QColor(base_color)
            w_start.setAlpha(100)
            w_mid = QColor(base_color)
            w_mid.setAlpha(255)
            
            widget_anim.setKeyValueAt(0.0, w_start)
            widget_anim.setKeyValueAt(0.5, w_mid)
            widget_anim.setKeyValueAt(1.0, w_start)
            
            group.addAnimation(widget_anim)

        # Temizlik ve Başlatma
        # Önceki animasyon grubunu temizle
        if hasattr(widget, '_pulse_anim_group'):
             widget._pulse_anim_group.stop()
             # Eski grup Python tarafından temizlenir

        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        # Referans sakla (Garbage Collection önlemi)
        widget._pulse_anim_group = group