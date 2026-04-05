"""
BU DOSYA: Uygulama açılırken yapılacak işlemleri yönetir.
Uygulama açılırken önce UpdateWorker ile sürüm kontrolü,
ardından SystemCheckWorker ile Playwright tarayıcı kontrolü yapar.
"""

from PyQt6.QtCore import QObject, pyqtSignal
import os
import shutil
import logging
from PyQt6.QtWidgets import QApplication

from services.updater import UpdateWorker
from services.system_check import SystemCheckWorker

class StartupManager(QObject):
    status_changed = pyqtSignal(str)
    finished = pyqtSignal(bool) # success

    def __init__(self):
        super().__init__()
        self.update_worker = None
        self.system_worker = None

    def start_checks(self):
        self.status_changed.emit("Güncelleme Aranıyor...")
        self.update_worker = UpdateWorker()
        self.update_worker.status_signal.connect(self.status_changed.emit)
        self.update_worker.finished_signal.connect(self._on_update_finished)
        self.update_worker.start()

    def _on_update_finished(self, success: bool, param: str):
        self.update_worker = None
        if success and param:
            self.status_changed.emit("Güncelleme Uygulanıyor...")
            try:
                os.startfile(param)
            except Exception as e:
                logging.error(f"BAT calistirilamadi: {e}")
            QApplication.quit()
        else:
            self.status_changed.emit("Sistem Kontrol Ediliyor...")
            self.system_worker = SystemCheckWorker()
            self.system_worker.status_signal.connect(self.status_changed.emit)
            self.system_worker.finished_signal.connect(self._on_system_check_finished)
            self.system_worker.start()

    def _on_system_check_finished(self, success: bool):
        self.system_worker = None
        self.finished.emit(success)

    @staticmethod
    def cleanup_and_exit():
        """
        Bozuk/eksik Playwright dosyalarını temizler ve uygulamayı kapatır.
        Bir sonraki açılışta temiz bir kurulum yapılmasını garanti eder.
        """
        playwright_dir = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
        if playwright_dir and os.path.exists(playwright_dir):
            try:
                shutil.rmtree(playwright_dir, ignore_errors=True)
                logging.info(f"Playwright klasörü temizlendi: {playwright_dir}")
            except Exception as e:
                logging.error(f"Playwright klasörü silinemedi: {e}")
        
        logging.info("Uygulama tarayıcı kurulum hatası nedeniyle kapatılıyor.")
        QApplication.quit()
