"""
BU DOSYA: Sistem tepsisi (System Tray) simgesini ve sağ tık menüsünü yönetir.
Programın arka planda çalışmasını sağlar.
"""

import threading
import pystray
from PIL import Image
from typing import Callable, Optional

class TrayManager:
    """Sistem tepsisi (Tray) işlemleri yöneticisi."""
    
    def __init__(self, 
                 icon_image: Optional[Image.Image], 
                 app_name: str, 
                 show_callback: Callable, 
                 quit_callback: Callable):
        """
        Args:
            icon_image: Tray'de görünecek ikon (PIL Image)
            app_name: Hover durumunda görünecek isim
            show_callback: "Göster" menüsüne tıklanınca çağrılacak fonksiyon
            quit_callback: "Çıkış" menüsüne tıklanınca çağrılacak fonksiyon
        """
        self.icon_image = icon_image
        self.app_name = app_name
        self.show_callback = show_callback
        self.quit_callback = quit_callback
        
        self.tray_icon: Optional[pystray.Icon] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Tray ikonunu ayrı bir thread'de başlatır."""
        if not self.icon_image:
            # İkon yoksa varsayılan oluştur
            self.icon_image = Image.new('RGB', (64, 64), color = (73, 109, 137))
        
        # Menü Tanımı
        menu = (
            pystray.MenuItem('Göster', self.show_callback, default=True),
            pystray.MenuItem('Çıkış', self.quit_callback)
        )
        
        self.tray_icon = pystray.Icon("ObisNotifier", self.icon_image, self.app_name, menu)
        
        # Pystray mainloop'u bloklayıcıdır, bu yüzden thread açıyoruz
        self.thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Tray ikonunu durdurur ve temizler."""
        if self.tray_icon:
            self.tray_icon.stop()

    def notify(self, title: str, message: str) -> None:
        """Windows bildirimi (Baloncuk) gösterir."""
        if self.tray_icon:
            self.tray_icon.notify(message, title)
