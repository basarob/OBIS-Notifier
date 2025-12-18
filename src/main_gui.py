import json
import logging
import os
import queue
import sys
import threading
from typing import Any, Dict, Optional

import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw, ImageTk
from tkinter import messagebox

from backend import OBISNotifier, set_auto_start, ensure_browsers_installed

# Playwright tarayıcı yolu düzeltmesi (PyInstaller ile uyumluluk için)
if getattr(sys, 'frozen', False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getenv("LOCALAPPDATA"), "ms-playwright")

# Sabitler
SETTINGS_FILE = "settings.json"

# Loglama için kuyruk (Queue)
log_queue: queue.Queue = queue.Queue()

class QueueHandler(logging.Handler):
    """Log kayıtlarını bir kuyruğa (Queue) gönderen özel logging handler."""
    def emit(self, record: logging.LogRecord) -> None:
        log_queue.put(self.format(record))

class ToolTip:
    """
    Arayüz elemanları üzerine gelindiğinde (hover) açıklama gösteren sınıf.
    """
    def __init__(self, widget: ctk.CTkBaseClass, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[ctk.CTkToplevel] = None

        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: Any = None) -> None:
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            self.tooltip_window, 
            text=self.text, 
            fg_color="gray20", 
            corner_radius=5, 
            text_color="white", 
            padx=10, 
            pady=5
        )
        label.pack()

    def hide_tooltip(self, event: Any = None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class App(ctk.CTk):
    """
    OBIS Notifier Ana Uygulama Sınıfı.
    """
    def __init__(self) -> None:
        super().__init__()

        self.title("OBIS Notifier")
        self.geometry("900x600")
        self.resizable(False, False)

        # .Tema ayarları
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Grid yapılandırması
        self.grid_columnconfigure(0, weight=1) # Ayarlar (Sol)
        self.grid_columnconfigure(1, weight=1) # Loglar/Kontrol (Sağ)
        self.grid_rowconfigure(0, weight=1)

        # Arayüz Panelleri
        self._init_panels()
        
        self.tray_icon: Optional[pystray.Icon] = None

        # Değişkenler
        self.obis_mail_var = ctk.StringVar()
        self.obis_password_var = ctk.StringVar()
        self.sender_email_var = ctk.StringVar()
        self.gmail_password_var = ctk.StringVar()
        self.semester_var = ctk.StringVar()
        self.interval_var = ctk.StringVar(value="20")
        self.browser_var = ctk.StringVar(value="chromium")
        self.minimize_var = ctk.BooleanVar()
        self.autostart_var = ctk.BooleanVar()
        self.stop_failure_var = ctk.BooleanVar(value=True)

        # Arayüz Elemanlarını Oluştur
        self.create_settings_widgets()
        self.create_control_widgets()

        # Ayarları Yükle
        self.load_settings()

        # Backend referansı
        self.notifier: Optional[OBISNotifier] = None
        self.notifier_thread: Optional[threading.Thread] = None
        self.is_running: bool = False

        # Loglama Başlat
        self.setup_logging()
        self.after(100, self.update_log_display)
        
        # Kapatma olayını yakala
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # İkon ayarla
        self.icon_image: Optional[Image.Image] = None
        self.setup_icon()

        # Başlangıç Kontrolleri
        self.after(200, self.run_startup_checks)

    def run_startup_checks(self) -> None:
        """Uygulama açılışında gerekli kontrolleri yapar."""
        def _check():
            logging.info("Sistem bileşenleri kontrol ediliyor...")
            if not ensure_browsers_installed():
                messagebox.showwarning("Uyarı", "Tarayıcı bileşenleri eksik veya yüklenemedi.\nProgram çalışmayabilir.")
            else:
                logging.info("Sistem kullanıma hazır.")
        
        threading.Thread(target=_check, daemon=True).start()

    def _init_panels(self) -> None:
        """Sol ve Sağ panelleri (Frame) başlatır."""
        # Sol Panel (Ayarlar)
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0)
        self.settings_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.settings_frame.grid_columnconfigure(1, weight=1)
        
        # Sol Panel Scrollable
        self.scrollable = ctk.CTkScrollableFrame(self.settings_frame, label_text="Ayarlar")
        self.scrollable.pack(fill="both", expand=True, padx=5, pady=5)
        self.scrollable.grid_columnconfigure(1, weight=1)

        # Sağ Panel (Kontrol ve Loglar)
        self.control_frame = ctk.CTkFrame(self, corner_radius=0)
        self.control_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_rowconfigure(1, weight=1)

    def setup_icon(self) -> None:
        """Uygulama ikonunu ayarlar."""
        base_path = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            
        icon_path = os.path.join(base_path, "images", "icon.ico")
        if os.path.exists(icon_path):
            try:
                # 1. Pencere İkonu
                self.iconbitmap(icon_path)
                
                # 2. Tray İkonu için Image nesnesi
                self.icon_image = Image.open(icon_path)
                
            except Exception as e:
                logging.error(f"İkon yüklenemedi: {e}")
        else:
             # Fallback: PNG
             png_path = os.path.join(base_path, "images", "icon.png")
             if os.path.exists(png_path):
                 try:
                    self.icon_image = Image.open(png_path)
                    self.icon_photo = ImageTk.PhotoImage(self.icon_image)
                    self.iconphoto(False, self.icon_photo)
                 except Exception: 
                     pass
             else:
                logging.warning(f"İkon dosyası bulunamadı: {icon_path}")

    def create_info_label(self, parent: Any, text: str) -> ctk.CTkLabel:
        """Yardım (Tooltip) ikonu oluşturur."""
        info_label = ctk.CTkLabel(parent, text="?", width=20, height=20, corner_radius=10, fg_color="gray50", text_color="white")
        ToolTip(info_label, text)
        return info_label

    def create_settings_widgets(self) -> None:
        """Ayarlar menüsündeki widget'ları oluşturur."""
        # 1. OBIS Mail
        ctk.CTkLabel(self.scrollable, text="OBIS Mail:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.entry_obis_mail = ctk.CTkEntry(self.scrollable, textvariable=self.obis_mail_var)
        self.entry_obis_mail.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.create_info_label(self.scrollable, "ADÜ Öğrenci mail adresiniz.\nÖrn: 123@stu.adu.edu.tr").grid(row=0, column=2, padx=5)

        # 2. OBIS Şifre
        ctk.CTkLabel(self.scrollable, text="OBIS Şifre:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.entry_obis_pass = ctk.CTkEntry(self.scrollable, textvariable=self.obis_password_var, show="*")
        self.entry_obis_pass.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        # 3. Bildirim Maili
        ctk.CTkLabel(self.scrollable, text="Bildirim Maili:").grid(row=2, column=0, padx=5, pady=10, sticky="w")
        self.entry_sender_email = ctk.CTkEntry(self.scrollable, textvariable=self.sender_email_var)
        self.entry_sender_email.grid(row=2, column=1, padx=5, pady=10, sticky="ew")
        self.create_info_label(self.scrollable, "Bildirimlerin gönderileceği ve\nalınacağı Gmail adresiniz.").grid(row=2, column=2, padx=5)

        # 4. Gmail Uygulama Şifresi
        ctk.CTkLabel(self.scrollable, text="Uygulama Şifresi:").grid(row=3, column=0, padx=5, pady=10, sticky="w")
        self.entry_gmail_pass = ctk.CTkEntry(self.scrollable, textvariable=self.gmail_password_var, show="*")
        self.entry_gmail_pass.grid(row=3, column=1, padx=5, pady=10, sticky="ew")
        self.create_info_label(self.scrollable, "\"https://myaccount.google.com/apppasswords\"\nAdresinden uygulama şifrenizi almalısınız.").grid(row=3, column=2, padx=5)

        # 5. Yarıyıl
        ctk.CTkLabel(self.scrollable, text="Yarıyıl:").grid(row=4, column=0, padx=5, pady=10, sticky="w")
        self.combo_semester = ctk.CTkComboBox(self.scrollable, variable=self.semester_var, 
                                              state="readonly",
                                              values=["25/26 Güz", "25/26 Bahar", "26/27 Güz", "26/27 Bahar"])
        self.combo_semester.grid(row=4, column=1, padx=5, pady=10, sticky="ew")
        self.create_info_label(self.scrollable, "Sitede bulunmayan yarıyıl seçildiğinde hata alırsınız!").grid(row=4, column=2, padx=5)

        # 6. Kontrol Süresi
        ctk.CTkLabel(self.scrollable, text="Süre (dk):").grid(row=5, column=0, padx=5, pady=10, sticky="w")
        self.combo_interval = ctk.CTkComboBox(self.scrollable, variable=self.interval_var,
                                              state="readonly",
                                              values=["15", "20", "25", "30", "45", "60"])
        self.combo_interval.grid(row=5, column=1, padx=5, pady=10, sticky="ew")
        self.create_info_label(self.scrollable, "Kontrol sıklığı.").grid(row=5, column=2, padx=5)

        # 7. Tarayıcı
        ctk.CTkLabel(self.scrollable, text="Tarayıcı:").grid(row=6, column=0, padx=5, pady=10, sticky="w")
        self.combo_browser = ctk.CTkComboBox(self.scrollable, variable=self.browser_var,
                                             state="readonly",
                                             values=["chromium", "firefox", "webkit"])
        self.combo_browser.grid(row=6, column=1, padx=5, pady=10, sticky="ew")

        # Checkboxes
        self.check_minimize = ctk.CTkCheckBox(self.scrollable, text="Simge durumunda çalıştır", variable=self.minimize_var)
        self.check_minimize.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.create_info_label(self.scrollable, "Pencere kapatıldığında simge durumunda küçültür.").grid(row=7, column=2, padx=5)

        self.check_autostart = ctk.CTkCheckBox(self.scrollable, text="Otomatik Başlat", variable=self.autostart_var, command=self.on_autostart_change)
        self.check_autostart.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.create_info_label(self.scrollable, "Windows oturumu açıldığında otomatik olarak sistem başlatılır.").grid(row=8, column=2, padx=5)

        self.check_stop_failure = ctk.CTkCheckBox(self.scrollable, text="3 Başarısız Girişte Durdur", variable=self.stop_failure_var)
        self.check_stop_failure.grid(row=9, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.create_info_label(self.scrollable, "Art arda 3 başarısız girişte uygulama durdurulur.").grid(row=9, column=2, padx=5)

        # Kaydet Butonu
        self.btn_save = ctk.CTkButton(self.scrollable, text="Ayarları Kaydet", command=self.save_settings, fg_color="green")
        self.btn_save.grid(row=10, column=0, columnspan=3, padx=20, pady=20, sticky="ew")

        # .Test Bildirimi Butonu
        self.btn_test_mail = ctk.CTkButton(self.scrollable, text="Test Bildirimi Gönder", command=self.send_test_mail, fg_color="gray")
        self.btn_test_mail.grid(row=11, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")

    def create_control_widgets(self) -> None:
        """Kontrol paneli widget'larını oluşturur."""
        # Başlat/Durdur Butonu
        self.btn_start_stop = ctk.CTkButton(self.control_frame, text="Sistemi Başlat", command=self.toggle_monitoring, height=50, font=("Arial", 18, "bold"))
        self.btn_start_stop.pack(padx=20, pady=20, fill="x")

        # Log Başlığı
        ctk.CTkLabel(self.control_frame, text="Sistem Logları:").pack(padx=20, anchor="w")

        # Log Alanı
        self.log_text = ctk.CTkTextbox(self.control_frame)
        self.log_text.pack(padx=20, pady=10, fill="both", expand=True)
        self.log_text.configure(state="disabled")

        # Alt Bilgi Paneli (Son Kontrol)
        self.info_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.info_frame.pack(padx=20, pady=(0, 5), fill="x", side="bottom")

        self.lbl_last_check = ctk.CTkLabel(self.info_frame, text="Son Kontrol: -", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_last_check.pack(side="right") # Sağa yasla

        # Footer (İmza)
        footer_label = ctk.CTkLabel(self.control_frame, text="Başar Orhanbulucu - OBIS Notifier v2.0", text_color="gray60", font=("Arial", 10))
        footer_label.pack(side="bottom", pady=5)

    def setup_logging(self) -> None:
        """Global logging yapılandırmasını kurar."""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Queue Handler ekle
        queue_handler = QueueHandler()
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

    def update_log_display(self) -> None:
        """Kuyruktaki logları ekrana yazar."""
        try:
            while True:
                record = log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", record + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self.update_log_display)

    def load_settings(self) -> None:
        """Ayarları JSON dosyasından yükler."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.obis_mail_var.set(settings.get("obis_mail", ""))
                    self.obis_password_var.set(settings.get("obis_password", ""))
                    self.sender_email_var.set(settings.get("sender_email", ""))
                    self.gmail_password_var.set(settings.get("gmail_app_password", ""))
                    self.semester_var.set(settings.get("semester", ""))
                    self.interval_var.set(str(settings.get("check_interval", 20)))
                    self.browser_var.set(settings.get("browser", "chromium"))
                    self.minimize_var.set(settings.get("minimize_to_tray", False))
                    self.autostart_var.set(settings.get("auto_start", False))
                    self.stop_failure_var.set(settings.get("stop_on_failures", True))
                    
                    if not self.obis_mail_var.get() or not self.obis_password_var.get() or not self.sender_email_var.get() or not self.gmail_password_var.get():
                        messagebox.showwarning("Eksik Ayar", "Lütfen tüm ayarları eksiksiz doldurunuz.")
                        
            except Exception as e:
                logging.error(f"Ayarlar yüklenemedi: {e}")
        else:
             messagebox.showinfo("Hoşgeldiniz", "Lütfen önce ayarları yapılandırıp 'Ayarları Kaydet' butonuna basınız.")

    def on_autostart_change(self) -> None:
        """Otomatik başlat onay kutusu değiştiğinde çağrılır."""
        # İşlem "Ayarları Kaydet" butonuna basılınca yapılır.
        pass 

    def save_settings(self) -> bool:
        """
        Ayarları doğrular ve dosyaya kaydeder.

        Returns:
            bool: Kayıt başarılı ise True.
        """
        if not self.obis_mail_var.get() or not self.obis_password_var.get() or not self.sender_email_var.get() or not self.gmail_password_var.get() or not self.semester_var.get():
             messagebox.showerror("Hata", "Tüm alanlar zorunludur!")
             return False

        obis_mail = self.obis_mail_var.get()
        if not obis_mail.endswith("@stu.adu.edu.tr"):
            logging.error("HATA: OBIS Mail adresi @stu.adu.edu.tr ile bitmelidir!")
            messagebox.showerror("Hata", "OBIS Mail adresi @stu.adu.edu.tr ile bitmelidir!")
            return False
        
        sender_email = self.sender_email_var.get()
        if not sender_email.endswith("@gmail.com"):
            logging.error("HATA: Bildirim Mail adresi @gmail.com ile bitmelidir!")
            messagebox.showerror("Hata", "Bildirim Mail adresi @gmail.com ile bitmelidir!")
            return False
        
        try:
            interval = int(self.interval_var.get())
        except ValueError:
            logging.error("HATA: Süre sayısal olmalıdır!")
            return False

        settings = {
            "obis_mail": obis_mail,
            "obis_password": self.obis_password_var.get(),
            "sender_email": self.sender_email_var.get(),
            "gmail_app_password": self.gmail_password_var.get(),
            "semester": self.semester_var.get(),
            "check_interval": interval,
            "browser": self.browser_var.get(),
            "minimize_to_tray": self.minimize_var.get(),
            "auto_start": self.autostart_var.get(),
            "stop_on_failures": self.stop_failure_var.get()
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            logging.info("Ayarlar doğrulandı ve kaydedildi.")
            
            # Auto Start Ayarını Uygula
            if self.autostart_var.get():
                set_auto_start(True)
            else:
                set_auto_start(False)
            
            return True
            
        except Exception as e:
            logging.error(f"Ayarlar kaydedilirken hata: {e}")
            return False

    def toggle_monitoring(self) -> None:
        """İzleme işlemini başlatır veya durdurur."""
        if self.is_running:
            # Durdurma
            logging.info("Durdurma isteği gönderildi...")
            if self.notifier:
                self.notifier.stop_monitoring()
            self.is_running = False
            self.btn_start_stop.configure(text="Sistemi Başlat", fg_color=["#3B8ED0", "#1F6AA5"])
            self.set_settings_state("normal")
        else:
            # Başlatma
            if not self.save_settings():
                logging.error("Ayarlar doğrulanamadığı için sistem başlatılamadı!")
                return                

            settings = {
                "obis_mail": self.obis_mail_var.get(),
                "obis_password": self.obis_password_var.get(),
                "sender_email": self.sender_email_var.get(),
                "gmail_app_password": self.gmail_password_var.get(),
                "semester": self.semester_var.get(),
                "check_interval": int(self.interval_var.get()),
                "browser": self.browser_var.get(),
                "minimize_to_tray": self.minimize_var.get(),
                "auto_start": self.autostart_var.get(),
                "stop_on_failures": self.stop_failure_var.get(),
                "status_callback": self.update_status_label
            }

            self.notifier = OBISNotifier(settings)
            
            self.notifier_thread = threading.Thread(target=self.notifier.start_monitoring, daemon=True)
            self.notifier_thread.start()
            
            self.is_running = True
            self.btn_start_stop.configure(text="Sistemi Durdur", fg_color="red")
            self.set_settings_state("disabled")
            
            logging.info("Sistem başlatıldı.")

    def set_settings_state(self, state: str) -> None:
        """Ayar widget'larının durumunu (aktif/pasif) değiştirir."""
        self.entry_obis_mail.configure(state=state)
        self.entry_obis_pass.configure(state=state)
        self.entry_sender_email.configure(state=state)
        self.entry_gmail_pass.configure(state=state)
        self.combo_semester.configure(state="readonly" if state=="normal" else "disabled")
        self.combo_interval.configure(state="readonly" if state=="normal" else "disabled")
        self.combo_browser.configure(state="readonly" if state=="normal" else "disabled")
        self.check_minimize.configure(state=state)
        self.check_autostart.configure(state=state)
        self.check_stop_failure.configure(state=state)
        self.btn_save.configure(state=state)
        self.btn_test_mail.configure(state=state)

    def update_status_label(self, text: str) -> None:
        """Sol alt köşedeki durum bilgisini günceller (Thread safe)."""
        self.after(0, lambda: self.lbl_last_check.configure(text=text))

    def send_test_mail(self) -> None:
        """Test maili gönderme işlemini ayrı bir thread'de başlatır."""
        if not self.save_settings():
            return
            
        settings = {
                "obis_mail": self.obis_mail_var.get(),
                "obis_password": self.obis_password_var.get(),
                "semester": self.semester_var.get(),
                "sender_email": self.sender_email_var.get(),
                "gmail_app_password": self.gmail_password_var.get(),
                "check_interval": 15,
                "browser": "chromium",
                "status_callback": None
        }
        
        def run_test():
            try:
                self.btn_test_mail.configure(state="disabled", text="Gönderiliyor...")
                temp_notifier = OBISNotifier(settings) # .type: ignore
                temp_notifier.send_test_email()
                messagebox.showinfo("Başarılı", "Test maili başarıyla gönderildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Test maili gönderilemedi:\n{e}")
            finally:
                self.after(0, lambda: self.btn_test_mail.configure(state="normal", text="Test Bildirimi Gönder"))

        threading.Thread(target=run_test, daemon=True).start()

    def on_closing(self) -> None:
        """Pencere kapatıldığında çağrılır."""
        if self.minimize_var.get():
            self.withdraw() # Pencereyi gizle
            self.show_tray_icon()
        else:
            self.quit_app()

    def show_tray_icon(self) -> None:
        """Sistem tepsisi (Tray) ikonunu oluşturur."""
        if self.icon_image:
            image = self.icon_image
        else:
            # Varsayılan mavi kare
            image = Image.new('RGB', (64, 64), color = (73, 109, 137))
            d = ImageDraw.Draw(image)
            d.rectangle([16,16,48,48], fill="white")
        
        menu = (pystray.MenuItem('Göster', self.show_window, default=True), pystray.MenuItem('Çıkış', self.quit_app))
        self.tray_icon = pystray.Icon("ObisNotifier", image, "OBIS Notifier", menu)
        
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon: Any = None, item: Any = None) -> None:
        """Gizlenen pencereyi tekrar gösterir."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.deiconify()
        self.lift()

    def quit_app(self, icon: Any = None, item: Any = None) -> None:
        """Uygulamadan tamamen çıkar."""
        if self.tray_icon:
            self.tray_icon.stop()
        if self.notifier and self.is_running:
            self.notifier.stop_monitoring()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.mainloop()
