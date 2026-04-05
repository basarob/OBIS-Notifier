"""
BU DOSYA: Uygulamanın Playwright tarayıcı altyapısını kontrol eden 
ve indirme sürecini UI'yı dondurmadan yöneten QThread Sınıfını barındırır.
Ayrıca Playwright CLI üzerinden doğrudan indirme ve kontrol mantıklarını içerir.
"""

import logging
import os
import sys
import subprocess
from PyQt6.QtCore import pyqtSignal, QThread
from playwright.sync_api import sync_playwright

_active_process = None  # Kurulum sırasında iptal edilirse durdurabilmek için global değişken

def ensure_browsers_installed(status_callback=None) -> bool:
    """
    Playwright tarayıcılarının (Chromium ve Firefox) yüklü olup olmadığını kontrol eder.
    Eksik olan varsa indirme işlemini başlatır.
    
    Args:
        status_callback: İlerleme durumu bildirmek için opsiyonel callable.
                         Örn: status_callback("Tarayıcı kontrol ediliyor...")
    """
    def _notify(msg: str):
        """Durum bildirimini güvenli şekilde iletir."""
        if status_callback:
            status_callback(msg)
        logging.info(msg)
    
    _notify("Tarayıcı bileşenleri kontrol ediliyor...")
    
    # 1. Kontrol: Hem Chromium hem Firefox başlatılabilir mi?
    all_installed = True
    try:
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        _notify("Chromium tarayıcısı bulunamadı.")
        all_installed = False
    
    try:
        with sync_playwright() as p:
            p.firefox.launch(headless=True).close()
    except Exception:
        _notify("Firefox tarayıcısı bulunamadı.")
        all_installed = False
    
    if all_installed:
        _notify("Tüm tarayıcılar zaten yüklü.")
        return True
    
    # 2. İndirme İşlemi (PLAYWRIGHT_BROWSERS_PATH env var'ı main.py'de ayarlandı)
    _notify("Gerekli Bileşenler Kuruluyor...")
    try:
        # Mevcut ortam değişkenlerini alt processe aktar
        env = os.environ.copy()
        
        if getattr(sys, 'frozen', False):
            # EXE ortamında Playwright CLI install
            from playwright.__main__ import main as pw_main
            for browser_name in ["chromium", "firefox"]:
                old_argv = sys.argv
                sys.argv = ["playwright", "install", browser_name]
                try:
                    pw_main()
                except SystemExit:
                    pass
                finally:
                    sys.argv = old_argv
        else:
            # Geliştirme ortamında subprocess ile kurulum
            global _active_process
            _active_process = subprocess.Popen(
                [sys.executable, "-m", "playwright", "install", "chromium", "firefox"],
                env=env
            )
            _active_process.wait()
            ret = _active_process.returncode
            _active_process = None
            
            if ret != 0:
                raise Exception(f"Playwright install başarısız oldu (Hata Kodu: {ret})")
            
        _notify("Tarayıcı kurulumu tamamlandı.")
        return True
    except Exception as e:
        logging.error(f"Tarayıcı kurulumu sırasında kritik hata: {e}")
        _notify(f"Tarayıcı kurulumu başarısız: {e}")
        return False


class SystemCheckWorker(QThread):
    """
    Uygulama açılışında arka planda Playwright tarayıcı dosyalarını
    kontrol eder. Eksik veya güncel değilse indirme yapar.
    UI thread'ini bloklamadan çalışır.
    """
    status_signal = pyqtSignal(str)   # İlerleme durumu mesajı
    finished_signal = pyqtSignal(bool) # Başarılı mı?

    def run(self):
        """Tarayıcı kontrol ve kurulum işlemini arka planda yürütür."""
        result = ensure_browsers_installed(
            status_callback=lambda msg: self.status_signal.emit(msg)
        )
        self.finished_signal.emit(result)
