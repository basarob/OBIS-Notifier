from win11toast import toast
import ctypes
import json
import logging
import os
import queue
import sys
import threading
import webbrowser
from typing import Any, Dict, Optional, List
import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw, ImageTk
from tkinter import messagebox
from backend import OBISNotifier, set_auto_start, ensure_browsers_installed, CURRENT_VERSION, check_for_updates, get_user_data_dir

# Playwright tarayıcı yolu düzeltmesi (PyInstaller ile uyumluluk için)
if getattr(sys, 'frozen', False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getenv("LOCALAPPDATA"), "ms-playwright")

# Sabitler
SETTINGS_FILE = os.path.join(get_user_data_dir(), "settings.json")

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
        self.geometry("900x700")
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
        self.student_id_var = ctk.StringVar()
        self.obis_password_var = ctk.StringVar()
        
        self.notify_email_var = ctk.BooleanVar(value=False)
        self.notify_windows_var = ctk.BooleanVar(value=False)
        
        self.sender_email_var = ctk.StringVar()
        self.gmail_password_var = ctk.StringVar()
        self.semester_var = ctk.StringVar()
        self.interval_var = ctk.StringVar(value="20")
        
        # Gelişmiş Ayarlar
        self.advanced_settings_visible = False
        self.browser_var = ctk.StringVar(value="chromium")
        self.minimize_var = ctk.BooleanVar()
        self.autostart_var = ctk.BooleanVar()
        self.stop_failure_var = ctk.BooleanVar(value=True)

        # Şifre Göster/Gizle Durumu
        self.show_obis_pass = False
        self.show_gmail_pass = False

        # Arayüz Elemanlarını Oluştur
        self.create_settings_widgets()
        self.create_control_widgets()

        # Ayarları Yükle
        self.load_settings()

        # Event Bindings (Dinamik Arayüz için)
        self.notify_email_var.trace_add("write", self.update_email_fields_visibility)

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
        
        # .Tray ikonunu başlat (Bildirimler için gerekli)
        self.init_tray_icon()

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
            
            # Güncelleme Kontrolü (Sessiz)
            self.check_updates(manual=False)
        
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
        
        # === TEMEL AYARLAR ===
        
        # 1. Öğrenci Numarası
        ctk.CTkLabel(self.scrollable, text="Öğrenci No:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.entry_student_id = ctk.CTkEntry(self.scrollable, textvariable=self.student_id_var, placeholder_text="Örn: 201812345")
        self.entry_student_id.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        # 2. OBIS Şifre
        ctk.CTkLabel(self.scrollable, text="OBIS Şifre:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        pass_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")
        pass_frame.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        pass_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_obis_pass = ctk.CTkEntry(pass_frame, textvariable=self.obis_password_var, show="*")
        self.entry_obis_pass.grid(row=0, column=0, sticky="ew")
        
        self.btn_toggle_obis_pass = ctk.CTkButton(pass_frame, text="👁", width=30, command=self.toggle_obis_pass_visibility)
        self.btn_toggle_obis_pass.grid(row=0, column=1, padx=(5,0))

        # 3. Yarıyıl
        ctk.CTkLabel(self.scrollable, text="Yarıyıl:").grid(row=2, column=0, padx=5, pady=10, sticky="w")
        self.combo_semester = ctk.CTkComboBox(self.scrollable, variable=self.semester_var, 
                                              state="readonly",
                                              values=["25/26 Güz", "25/26 Bahar", "26/27 Güz", "26/27 Bahar"])
        self.combo_semester.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        # 4. Kontrol Süresi
        ctk.CTkLabel(self.scrollable, text="Süre (dk):").grid(row=3, column=0, padx=5, pady=10, sticky="w")
        self.combo_interval = ctk.CTkComboBox(self.scrollable, variable=self.interval_var,
                                              state="readonly",
                                              values=["15", "20", "25", "30", "45", "60"])
        self.combo_interval.grid(row=3, column=1, padx=5, pady=10, sticky="ew")

        # 5. Bildirim Tercihi
        ctk.CTkLabel(self.scrollable, text="Bildirim Tercihi:", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, padx=5, pady=(20, 10), sticky="w")
        
        notify_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")
        notify_frame.grid(row=4, column=1, columnspan=2, padx=20, pady=10, sticky="w")
        
        self.check_email = ctk.CTkSwitch(notify_frame, text="E-posta", variable=self.notify_email_var)
        self.check_email.pack(side="left", padx=(0, 20))
        
        self.check_windows = ctk.CTkSwitch(notify_frame, text="Windows", variable=self.notify_windows_var)
        self.check_windows.pack(side="left")

        # === E-POSTA AYARLARI GROUP (Dinamik) ===
        self.email_settings_frame = ctk.CTkFrame(self.scrollable)
        self.email_settings_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        self.email_settings_frame.grid_columnconfigure(1, weight=1)
        
        # 6. Bildirim Maili (Gmail)
        ctk.CTkLabel(self.email_settings_frame, text="Gmail Adresi:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.entry_sender_email = ctk.CTkEntry(self.email_settings_frame, textvariable=self.sender_email_var)
        self.entry_sender_email.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        # 7. Gmail Uygulama Şifresi
        ctk.CTkLabel(self.email_settings_frame, text="Uygulama Şifresi:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        gmail_pass_frame = ctk.CTkFrame(self.email_settings_frame, fg_color="transparent")
        gmail_pass_frame.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        gmail_pass_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_gmail_pass = ctk.CTkEntry(gmail_pass_frame, textvariable=self.gmail_password_var, show="*")
        self.entry_gmail_pass.grid(row=0, column=0, sticky="ew")
        
        self.btn_toggle_gmail_pass = ctk.CTkButton(gmail_pass_frame, text="👁", width=30, command=self.toggle_gmail_pass_visibility)
        self.btn_toggle_gmail_pass.grid(row=0, column=1, padx=(5,5))
        
        self.btn_get_app_pass = ctk.CTkButton(gmail_pass_frame, text="Şifre Al", width=60, fg_color="#E0A800", text_color="black", hover_color="#C69500", command=self.open_app_password_url)
        self.btn_get_app_pass.grid(row=0, column=2)

        # 2FA Uyarısı
        twofa_frame = ctk.CTkFrame(self.email_settings_frame, fg_color="transparent")
        twofa_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10), sticky="w")
        
        ctk.CTkLabel(twofa_frame, text="⚠️ Hesabınızın 2 adımlı doğrulaması açık olmalı!", text_color="orange", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        ctk.CTkButton(twofa_frame, text="Aktifleştir", width=80, height=24, fg_color="transparent", border_width=1, border_color="orange", text_color="orange", hover_color=("gray90", "gray20"), font=ctk.CTkFont(size=11), command=self.open_2fa_url).pack(side="left")

        # === GELİŞMİŞ AYARLAR ===
        self.btn_toggle_advanced = ctk.CTkButton(self.scrollable, text="▼ Gelişmiş Ayarlar", 
                                                 fg_color="transparent", border_width=1, 
                                                 text_color=("gray10", "gray90"), 
                                                 command=self.toggle_advanced_settings)
        self.btn_toggle_advanced.grid(row=6, column=0, columnspan=3, pady=(20, 5), sticky="ew")

        self.advanced_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")
        
        self.advanced_frame.grid_columnconfigure(1, weight=1)
        
        # .Tarayıcı
        ctk.CTkLabel(self.advanced_frame, text="Tarayıcı:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.combo_browser = ctk.CTkComboBox(self.advanced_frame, variable=self.browser_var,
                                             state="readonly",
                                             values=["chromium", "firefox", "webkit"])
        self.combo_browser.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.create_info_label(self.advanced_frame, "OBIS'e bağlanmak için kullanılacak tarayıcı motoru.\nChromium önerilir.").grid(row=0, column=2, padx=5)

        # Checkboxes
        self.check_minimize = ctk.CTkCheckBox(self.advanced_frame, text="Simge durumunda çalıştır", variable=self.minimize_var)
        self.check_minimize.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.create_info_label(self.advanced_frame, "Program kapatıldığında sistem tepsisine küçültür\nve arka planda çalışır.").grid(row=1, column=2, padx=5)

        self.check_autostart = ctk.CTkCheckBox(self.advanced_frame, text="Otomatik Başlat", variable=self.autostart_var)
        self.check_autostart.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.create_info_label(self.advanced_frame, "Windows açıldığında uygulama otomatik başlar.").grid(row=2, column=2, padx=5)

        self.check_stop_failure = ctk.CTkCheckBox(self.advanced_frame, text="3 Başarısız Girişte Durdur", variable=self.stop_failure_var)
        self.check_stop_failure.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.create_info_label(self.advanced_frame, "Hesabınızın kilitlenmemesi için\nüst üste hatalı girişlerde programı durdurur.").grid(row=3, column=2, padx=5)

        # Kaydet Butonu
        self.btn_save = ctk.CTkButton(self.scrollable, text="Ayarları Kaydet", command=self.save_settings, fg_color="green", height=40)
        self.btn_save.grid(row=8, column=0, columnspan=3, padx=20, pady=20, sticky="ew")

        # .Test Bildirimi
        self.btn_test_mail = ctk.CTkButton(self.scrollable, text="Test Bildirimi Gönder", command=self.send_test_notification, fg_color="gray")
        self.btn_test_mail.grid(row=9, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")

    def toggle_obis_pass_visibility(self) -> None:
        self.show_obis_pass = not self.show_obis_pass
        self.entry_obis_pass.configure(show="" if self.show_obis_pass else "*")
        self.btn_toggle_obis_pass.configure(text="🔒" if self.show_obis_pass else "👁")

    def toggle_gmail_pass_visibility(self) -> None:
        self.show_gmail_pass = not self.show_gmail_pass
        self.entry_gmail_pass.configure(show="" if self.show_gmail_pass else "*")
        self.btn_toggle_gmail_pass.configure(text="🔒" if self.show_gmail_pass else "👁")
        
    def open_app_password_url(self) -> None:
        webbrowser.open("https://myaccount.google.com/apppasswords")

    def open_2fa_url(self) -> None:
        webbrowser.open("https://myaccount.google.com/signinoptions/two-step-verification")

    def update_email_fields_visibility(self, *args: Any) -> None:
        if self.notify_email_var.get():
            self.email_settings_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        else:
            self.email_settings_frame.grid_forget()

    def toggle_advanced_settings(self) -> None:
        self.advanced_settings_visible = not self.advanced_settings_visible
        if self.advanced_settings_visible:
            self.advanced_frame.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            self.btn_toggle_advanced.configure(text="▲ Gelişmiş Ayarlar")
        else:
            self.advanced_frame.grid_forget()
            self.btn_toggle_advanced.configure(text="▼ Gelişmiş Ayarlar")

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

        # Footer (Alt Bilgi ve Güncelleme)
        footer_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=5)
        
        # Ortalamak için bir container
        footer_container = ctk.CTkFrame(footer_frame, fg_color="transparent")
        footer_container.pack(side="top", anchor="center")

        # Versiyon ve İsim
        version_text = f"Başar Orhanbulucu - OBIS Notifier {CURRENT_VERSION} "
        self.footer_label = ctk.CTkLabel(footer_container, text=version_text, text_color="gray60", font=("Arial", 10))
        self.footer_label.pack(side="left", padx=(0, 5))
        
        # Güncelleme Kontrol Butonu
        self.btn_check_updates = ctk.CTkButton(footer_container, 
                                               text="Güncellemeleri Kontrol Et", 
                                               width=120, 
                                               height=20,
                                               font=ctk.CTkFont(size=10),
                                               fg_color="transparent", 
                                               border_width=1,
                                               text_color=("gray60", "gray40"),
                                               hover_color=("gray90", "gray20"),
                                               command=lambda: self.check_updates(manual=True))
        self.btn_check_updates.pack(side="left", padx=(5, 0))

    def check_updates(self, manual: bool = True) -> None:
        """Güncelleme kontrolünü başlatır."""
        def run_check():
            if manual:
                 self.btn_check_updates.configure(state="disabled", text="Kontrol ediliyor...")
            
            update_info = check_for_updates(CURRENT_VERSION)
            
            if manual:
                 self.btn_check_updates.configure(state="normal", text="Güncellemeleri Kontrol Et")

            if update_info:
                # Ana thread'de popup göster
                self.after(0, lambda: self.show_update_popup(update_info))
            elif manual:
                # Manuel kontrolde güncelsek bilgi ver
                self.after(0, lambda: messagebox.showinfo("Bilgi", "Uygulama güncel!"))
        
        threading.Thread(target=run_check, daemon=True).start()

    def show_update_popup(self, update_info: dict) -> None:
        """Güncelleme varsa kullanıcıya sorar."""
        msg = f"Yeni bir sürüm mevcut: {update_info['version']}\n\n{update_info['body']}\n\nİndirmek ister misiniz?"
        if messagebox.askyesno("Güncelleme Mevcut", msg):
            webbrowser.open(update_info['url'])

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
                    self.student_id_var.set(settings.get("student_id", ""))
                    self.obis_password_var.set(settings.get("obis_password", ""))
                    
                    # Bildirim Yöntemleri
                    methods = settings.get("notification_methods", ["email"])
                    self.notify_email_var.set("email" in methods)
                    self.notify_windows_var.set("windows" in methods)

                    self.sender_email_var.set(settings.get("sender_email", ""))
                    self.gmail_password_var.set(settings.get("gmail_app_password", ""))
                    self.semester_var.set(settings.get("semester", ""))
                    self.interval_var.set(str(settings.get("check_interval", 20)))
                    self.browser_var.set(settings.get("browser", "chromium"))
                    self.minimize_var.set(settings.get("minimize_to_tray", False))
                    self.autostart_var.set(settings.get("auto_start", False))
                    self.stop_failure_var.set(settings.get("stop_on_failures", True))
                        
            except Exception as e:
                logging.error(f"Ayarlar yüklenemedi: {e}")
        else:
             messagebox.showinfo("Hoşgeldiniz", "Lütfen önce ayarları yapılandırıp 'Ayarları Kaydet' butonuna basınız.")

        self.update_email_fields_visibility()

    def save_settings(self) -> bool:
        """
        Ayarları doğrular ve dosyaya kaydeder.
        """
        # 1. Genel Kontroller
        student_id = self.student_id_var.get()
        if not student_id or not student_id.isdigit():
             messagebox.showerror("Hata", "Öğrenci numarası sadece rakamlardan oluşmalıdır!")
             return False

        if not self.obis_password_var.get() or not self.semester_var.get():
             messagebox.showerror("Hata", "OBIS şifresi ve yarıyıl zorunludur!")
             return False

        # 2. Bildirim Kontrolleri
        methods = []
        if self.notify_email_var.get(): methods.append("email")
        if self.notify_windows_var.get(): methods.append("windows")

        if not methods:
            messagebox.showerror("Hata", "En az bir bildirim yöntemi seçmelisiniz!")
            return False

        # 3. Email Özel Kontrolleri
        if "email" in methods:
            sender_email = self.sender_email_var.get()
            if not sender_email.endswith("@gmail.com"):
                messagebox.showerror("Hata", "Bildirim Mail adresi @gmail.com ile bitmelidir!")
                return False
            
            if not self.gmail_password_var.get():
                messagebox.showerror("Hata", "Email bildirimi için Uygulama Şifresi zorunludur!")
                return False
        
        try:
            interval = int(self.interval_var.get())
        except ValueError:
            logging.error("HATA: Süre sayısal olmalıdır!")
            return False

        settings = {
            "student_id": student_id,
            "obis_password": self.obis_password_var.get(),
            "notification_methods": methods,
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

            methods = []
            if self.notify_email_var.get(): methods.append("email")
            if self.notify_windows_var.get(): methods.append("windows")

            settings = {
                "student_id": self.student_id_var.get(),
                "obis_password": self.obis_password_var.get(),
                "notification_methods": methods,
                "sender_email": self.sender_email_var.get(),
                "gmail_app_password": self.gmail_password_var.get(),
                "semester": self.semester_var.get(),
                "check_interval": int(self.interval_var.get()),
                "browser": self.browser_var.get(),
                "minimize_to_tray": self.minimize_var.get(),
                "auto_start": self.autostart_var.get(),
                "stop_on_failures": self.stop_failure_var.get(),
                "status_callback": self.update_status_label,
                "notification_callback": self.show_windows_notification
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
        self.entry_student_id.configure(state=state)
        self.entry_obis_pass.configure(state=state)
        
        self.check_email.configure(state=state)
        self.check_windows.configure(state=state)
        
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

    def restore_window_from_toast(self, args=None):
        """Bildirime tıklandığında pencereyi güvenli şekilde açar."""
        self.after(0, self.show_window)

    def show_windows_notification(self, title: str, message: str) -> None:
        """Windows Toast bildirimi gösterir (win11toast)."""
        try:
            # İkon yolunu bul
            icon_path = ""
            if getattr(sys, 'frozen', False):
                 base_path = sys._MEIPASS
            else:
                 base_path = os.path.dirname(os.path.abspath(__file__))
            
            # src/images/icon.ico veya images/icon.ico durumuna göre
            candidate = os.path.join(base_path, "images", "icon.ico")
            if os.path.exists(candidate):
                icon_path = candidate
            
            # win11toast ile kalıcı bildirim
            # app_id: Bildirimin başlığında "Python" yerine görünmesi için
            # icon: Bildirimin solunda görünmesi için
            toast(title, message, 
                  on_click=self.restore_window_from_toast, 
                  app_id="OBIS.Notifier", 
                  icon=icon_path)
                  
            logging.info(f"Windows bildirimi gönderildi: {title}")
        except Exception as e:
            logging.error(f"Windows bildirimi hatası: {e}")
            if self.tray_icon:
                self.tray_icon.notify(message, title)

    def update_status_label(self, text: str) -> None:
        """Sol alt köşedeki durum bilgisini günceller (Thread safe)."""
        self.after(0, lambda: self.lbl_last_check.configure(text=text))

    def send_test_notification(self) -> None:
        """Test bildirimini ayrı bir thread'de başlatır."""
        if not self.save_settings():
            return
        
        methods = []
        if self.notify_email_var.get(): methods.append("email")
        if self.notify_windows_var.get(): methods.append("windows")
            
        settings = {
                "student_id": self.student_id_var.get(),
                "obis_password": self.obis_password_var.get(),
                "notification_methods": methods,
                "semester": self.semester_var.get(),
                "sender_email": self.sender_email_var.get(),
                "gmail_app_password": self.gmail_password_var.get(),
                "check_interval": 15,
                "browser": "chromium",
                "status_callback": None,
                "notification_callback": self.show_windows_notification
        }
        
        def run_test():
            try:
                self.btn_test_mail.configure(state="disabled", text="Gönderiliyor...")
                temp_notifier = OBISNotifier(settings) # type: ignore
                temp_notifier.send_test_notification()
                messagebox.showinfo("Başarılı", "Test bildirimi gönderildi/tetiklendi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Test bildirimi hatası:\n{e}")
            finally:
                self.after(0, lambda: self.btn_test_mail.configure(state="normal", text="Test Bildirimi Gönder"))

        threading.Thread(target=run_test, daemon=True).start()

    def init_tray_icon(self) -> None:
        """Sistem tepsisi (Tray) ikonunu başlatır."""

        if self.icon_image:
            image = self.icon_image
        else:
            # Varsayılan mavi kare
            image = Image.new('RGB', (64, 64), color = (73, 109, 137))
            d = ImageDraw.Draw(image)
            d.rectangle([16,16,48,48], fill="white")
        
        # Menü: Göster ve Çıkış
        menu = (pystray.MenuItem('Göster', self.show_window, default=True), pystray.MenuItem('Çıkış', self.quit_app))
        
        self.tray_icon = pystray.Icon("ObisNotifier", image, "OBIS Notifier", menu)
        
        # .Tray ikonunu ayrı bir thread'de çalıştır
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_closing(self) -> None:
        """Pencere kapatıldığında çağrılır."""
        if self.minimize_var.get():
            self.withdraw() # Pencereyi gizle
        else:
            self.quit_app()

    def show_window(self, icon: Any = None, item: Any = None) -> None:
        """Gizlenen pencereyi tekrar gösterir."""
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
    try:
        myappid = 'OBIS.Notifier'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        pass
        
    app = App()
    app.mainloop()
