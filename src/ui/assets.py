"""
BU DOSYA: Uygulamanın ikon ve resim kaynaklarını yönetir (Asset Management).
EXE içinde (PyInstaller) veya geliştirme ortamında dosya yollarını doğru bulur.
"""

import sys
import os
import logging
from typing import Optional
from PIL import Image, ImageTk
import customtkinter as ctk

class AssetManager:
    """İkon ve resim yükleme işlerini yöneten yardımcı sınıf."""
    
    @staticmethod
    def get_base_path() -> str:
        """Kök dizini bulur (EXE veya Script)."""
        if getattr(sys, 'frozen', False):
            # PyInstaller ile paketlenmişse geçici dizin (sys._MEIPASS)
            return sys._MEIPASS
        else:
            # Normal çalıştırmada dosyanın bulunduğu klasörün 2 üstü (src/ui/assets.py -> src/)
            # Ancak biz projenin rootundan çalıştığımız için src'nin parent'ına inmeliyiz veya mantığı düzeltmeliyiz.
            # src/ui/assets.py konumundayız.
            # os.path.dirname(__file__) -> src/ui
            # parent -> src
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    @staticmethod
    def get_icon_path() -> str:
        """İkon dosyasının (.ico) tam yolunu döndürür."""
        base_path = AssetManager.get_base_path()
        # Kaynak kodda: src/images/icon.ico
        # Ama genelde runtime'da src klasörü olmayabilir, yapıya göre değişir.
        
        # 1. Olasılık: src/images içi
        path1 = os.path.join(base_path, "src", "images", "icon.ico")
        if os.path.exists(path1): return path1
        
        # 2. Olasılık: images/ içi (PyInstaller toplanmış hali)
        path2 = os.path.join(base_path, "images", "icon.ico")
        if os.path.exists(path2): return path2
        
        return ""

    @staticmethod
    def setup_app_icon(app: ctk.CTk) -> Optional[Image.Image]:
        """Ana pencereye ikon atar ve Tray için Image nesnesi döner."""
        icon_path = AssetManager.get_icon_path()
        
        if not icon_path or not os.path.exists(icon_path):
             logging.warning(f"İkon dosyası bulunamadı: {icon_path}")
             # PNG Fallback
             base_path = AssetManager.get_base_path()
             png_path = os.path.join(base_path, "src", "images", "icon.png") # Dev env
             if not os.path.exists(png_path):
                 png_path = os.path.join(base_path, "images", "icon.png") # Prod env

             if os.path.exists(png_path):
                 try:
                    img = Image.open(png_path)
                    photo = ImageTk.PhotoImage(img)
                    app.iconphoto(False, photo)
                    return img
                 except Exception: pass
             return None

        try:
            # 1. Pencere İkonu (.ico)
            app.iconbitmap(icon_path)
            
            # 2. Tray İkonu için Image nesnesi
            return Image.open(icon_path)
            
        except Exception as e:
            logging.error(f"İkon yüklenemedi: {e}")
            return None
