"""
BU DOSYA: Uygulamanın ana penceresini yönetir. Tüm bileşenleri 
(Settings, Control, Tray) burada birleştirir (Orchestrator).
"""

import threading
import ctypes
import logging
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
from win11toast import toast
import sys

# Bileşenler
from .panels.settings import SettingsPanel
from .panels.control import ControlPanel
from .managers.tray import TrayManager
from .assets import AssetManager
from .components.logger import setup_logging_to_queue

# Backend ve Utils
from ..core.notifier import OBISNotifier
from ..utils.updater import check_for_updates
from ..services.browser import ensure_browsers_installed
from ..config import CURRENT_VERSION

class App(ctk.CTk):
    """OBIS Notifier Ana Uygulama Sınıfı"""
    
    def __init__(self) -> None:
        super().__init__()
        
        # --- Pencere Ayarları ---
        self.title("OBIS Notifier")
        self.geometry("900x700")
        self.resizable(False, False)
        
        # .Tema
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Loglama
        setup_logging_to_queue()
        
        # --- Layout (Grid) ---
        self.grid_columnconfigure(0, weight=1) # Sol
        self.grid_columnconfigure(1, weight=1) # Sağ
        self.grid_rowconfigure(0, weight=1)
        
        # !--- Panellerin Oluşturulması ---
        
        # 1. Ayarlar Paneli (Sol)
        self.settings_panel = SettingsPanel(self, send_test_notification_callback=self.run_test_notification)
        self.settings_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 2. Kontrol Paneli (Sağ)
        version_str = f"Başar Orhanbulucu - OBIS Notifier {CURRENT_VERSION}"
        self.control_panel = ControlPanel(
            self, 
            start_stop_callback=self.toggle_monitoring, 
            check_updates_callback=self.run_update_check,
            version_text=version_str
        )
        self.control_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Logları akıtmaya başla
        self.control_panel.start_log_stream(self)
        
        # --- İkon ve Tray ---
        self.tray_manager: Optional[TrayManager] = None
        self._setup_icon_and_tray()
        
        # --- Durumlar ---
        self.notifier: Optional[OBISNotifier] = None
        self.notifier_thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        
        # Kapatma Olayı
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Başlangıç Ayarlarını Yükle
        self.settings_panel.load_settings()
        
        # Startup Kontrolleri
        self.after(200, self.run_startup_checks)

    def _setup_icon_and_tray(self) -> None:
        """İkonu yükler ve Tray Manager'ı başlatır."""
        icon_img = AssetManager.setup_app_icon(self)
        
        self.tray_manager = TrayManager(
            icon_image=icon_img, 
            app_name="OBIS Notifier", 
            show_callback=self.show_window, 
            quit_callback=self.quit_app
        )
        self.tray_manager.start()

    def run_startup_checks(self) -> None:
        """Açılışta tarayıcı ve güncelleme kontrolü yapar."""
        def _check():
            logging.info("Sistem bileşenleri kontrol ediliyor...")
            if not ensure_browsers_installed():
                messagebox.showwarning("Uyarı", "Tarayıcı bileşenleri eksik!")
            else:
                logging.info("Sistem kullanıma hazır.")
            
            # Güncelleme Kontrolü (Sessiz)
            self.run_update_check(manual=False)
        
        threading.Thread(target=_check, daemon=True).start()

    def toggle_monitoring(self) -> None:
        """Sistemi başlatır veya durdurur."""
        if self.is_running:
            # --- DURDUR ---
            logging.info("Durdurma isteği gönderildi...")
            if self.notifier:
                self.notifier.stop_monitoring()
            
            self.is_running = False
            self.control_panel.update_button_state(False)
            self.settings_panel.set_input_state("normal")

        else:
            # --- BAŞLAT ---
            # Önce ayarları doğrula ve kaydet
            if not self.settings_panel.save_settings():
                return 

            settings = self.settings_panel.get_settings_dict()
            
            # Callback Ekle
            settings["status_callback"] = self.control_panel.update_last_check_label
            settings["notification_callback"] = self.show_windows_notification
            settings["on_stop_callback"] = self.on_system_stopped
            
            self.notifier = OBISNotifier(settings)
            self.notifier_thread = threading.Thread(target=self.notifier.start_monitoring, daemon=True)
            self.notifier_thread.start()
            
            self.is_running = True
            self.control_panel.update_button_state(True)
            self.settings_panel.set_input_state("disabled")
            
            logging.info("Sistem başlatıldı.")

    def on_system_stopped(self) -> None:
        """Sistem otomatik durduğunda UI'ı günceller (Thread-safe)."""
        def _update_ui():
            self.is_running = False
            self.control_panel.update_button_state(False)
            self.settings_panel.set_input_state("normal")
            logging.info("Arayüz durduruldu durumuna getirildi.")
            
        self.after(0, _update_ui)

    def run_update_check(self, manual: bool = True) -> None:
        """Güncellemeleri kontrol eder."""
        def _run():
            if manual:
                self.control_panel.set_update_btn_loading(True)
            
            update_info = check_for_updates(CURRENT_VERSION)
            
            if manual:
                 self.control_panel.set_update_btn_loading(False)

            if update_info:
                self.after(0, lambda: self._show_update_popup(update_info))
            elif manual:
                self.after(0, lambda: messagebox.showinfo("Bilgi", "Uygulama zaten güncel!"))
        
        threading.Thread(target=_run, daemon=True).start()

    def _show_update_popup(self, info: dict) -> None:
        msg = f"Yeni sürüm: {info['version']}\n\n{info['body']}\n\nİndirmek ister misiniz?"
        if messagebox.askyesno("Güncelleme Mevcut", msg):
            import webbrowser
            webbrowser.open(info['url'])

    def run_test_notification(self) -> None:
        """Test bildirimini tetikler."""
        # Ayarları kaydetmeden test edemeyiz
        if not self.settings_panel.save_settings():
            return
            
        settings = self.settings_panel.get_settings_dict()
        # Callback ekle (Sadece Windows notifikasyonu için gerekli)
        settings["notification_callback"] = self.show_windows_notification
        
        def _test():
            try:
                self.settings_panel.btn_test_mail.configure(state="disabled", text="Gönderiliyor...")
                temp = OBISNotifier(settings) # Sadece notification servisi için
                temp.send_test_notification()
                messagebox.showinfo("Başarılı", "Test bildirimi gönderildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Test başarısız:\n{e}")
            finally:
                self.after(0, lambda: self.settings_panel.btn_test_mail.configure(state="normal", text="Test Bildirimi Gönder"))

        threading.Thread(target=_test, daemon=True).start()

    def show_windows_notification(self, title: str, message: str) -> None:
        """Windows Toast bildirimi (win11toast)."""
        icon_path = AssetManager.get_icon_path()
        try:
            toast(title, message, 
                  on_click=self.restore_window_from_toast, 
                  app_id="OBIS.Notifier", 
                  icon=icon_path if icon_path else None)
        except Exception:
            # Fallback: Tray balonu
            if self.tray_manager:
                self.tray_manager.notify(title, message)

    def restore_window_from_toast(self, args=None) -> None:
        """Bildirime tıklanınca pencereyi aç."""
        self.after(0, self.show_window)

    def show_window(self, icon: Any = None, item: Any = None) -> None:
        """Pencereyi görünür yap."""
        self.deiconify()
        self.lift()

    def on_closing(self) -> None:
        """X butonuna basılınca ne olacağını yönetir."""
        # Eğer ayarlarda minimize seçiliyse gizle
        minimize = self.settings_panel.minimize_var.get()
        if minimize:
            self.withdraw()
            # Kullanıcıya ilk seferde bilgi verilebilir (opsiyonel)
        else:
            self.quit_app()

    def quit_app(self, icon: Any = None, item: Any = None) -> None:
        """Tamamen kapat."""
        if self.tray_manager:
            self.tray_manager.stop()
        if self.notifier and self.is_running:
            self.notifier.stop_monitoring()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    # AppID ayarı
    try:
        myappid = 'OBIS.Notifier'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception: pass
    
    app = App()
    app.mainloop()
