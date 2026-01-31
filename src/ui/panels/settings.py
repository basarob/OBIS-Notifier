"""
BU DOSYA: Sol taraftaki ayarlar panelini ve tüm konfigürasyon widget'larını içerir.
Kullanıcı girişlerinin doğrulanması ve kaydedilmesi burada yapılır.
"""

import json
import logging
import os
import webbrowser
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, List, Optional

# Kendi modüllerimiz
from ..components.tooltip import ToolTip
from utils.system import set_auto_start, get_user_data_dir

SETTINGS_FILE = os.path.join(get_user_data_dir(), "settings.json")

class SettingsPanel(ctk.CTkScrollableFrame):
    """Ayarlar formu ve mantığını barındıran scroll edilebilir panel."""
    
    def __init__(self, parent: Any, send_test_notification_callback: Any):
        super().__init__(parent, label_text="Ayarlar")
        
        self.send_test_notification_callback = send_test_notification_callback
        
        # Değişkenler (Variables)
        self.student_id_var = ctk.StringVar()
        self.obis_password_var = ctk.StringVar()
        self.semester_var = ctk.StringVar()
        self.interval_var = ctk.StringVar(value="20")
        
        # Bildirim
        self.notify_email_var = ctk.BooleanVar(value=False)
        self.notify_windows_var = ctk.BooleanVar(value=False)
        
        # Email
        self.sender_email_var = ctk.StringVar()
        self.gmail_password_var = ctk.StringVar()
        
        # Gelişmiş
        self.browser_var = ctk.StringVar(value="chromium")
        self.minimize_var = ctk.BooleanVar()
        self.autostart_var = ctk.BooleanVar()
        self.stop_failure_var = ctk.BooleanVar(value=True)
        
        # UI State
        self.advanced_settings_visible = False
        self.show_obis_pass = False
        self.show_gmail_pass = False

        self._init_widgets()
        
        # Event Tracing
        self.notify_email_var.trace_add("write", self.update_email_fields_visibility)
        
    def _init_widgets(self) -> None:
        """Arayüz elemanlarını oluşturur."""
        self.grid_columnconfigure(1, weight=1)
        
        # --- Temel Ayarlar ---
        self._create_basic_fields()
        
        # --- Bildirim Seçimi ---
        self._create_notification_choice()
        
        # --- E-posta Ayarları (Dinamik) ---
        self._create_email_fields()
        
        # --- Gelişmiş Ayarlar ---
        self._create_advanced_fields()
        
        # --- Aksiyon Butonları ---
        self.btn_save = ctk.CTkButton(self, text="Ayarları Kaydet", command=self.save_settings, fg_color="green", height=40)
        self.btn_save.pack(fill="x", padx=20, pady=20)
        
        self.btn_test_mail = ctk.CTkButton(self, text="Test Bildirimi Gönder", command=self.send_test_notification_callback, fg_color="gray")
        self.btn_test_mail.pack(fill="x", padx=20, pady=(0, 20))

    def _create_basic_fields(self) -> None:
        """Temel ayarlar widget'larını oluşturur."""
        # Konteyner Frame
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=1)

        # 1. Öğrenci No
        ctk.CTkLabel(frame, text="Öğrenci No:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.entry_student_id = ctk.CTkEntry(frame, textvariable=self.student_id_var, placeholder_text="Örn: 201812345")
        self.entry_student_id.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        # 2. OBIS Şifre
        ctk.CTkLabel(frame, text="OBIS Şifre:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        pass_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pass_frame.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        pass_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_obis_pass = ctk.CTkEntry(pass_frame, textvariable=self.obis_password_var, show="*")
        self.entry_obis_pass.grid(row=0, column=0, sticky="ew")
        
        self.btn_toggle_obis_pass = ctk.CTkButton(pass_frame, text="👁", width=30, command=self.toggle_obis_pass_visibility)
        self.btn_toggle_obis_pass.grid(row=0, column=1, padx=(5,0))
        
        # 3. Yarıyıl
        ctk.CTkLabel(frame, text="Yarıyıl:").grid(row=2, column=0, padx=5, pady=10, sticky="w")
        self.combo_semester = ctk.CTkComboBox(frame, variable=self.semester_var, 
                                              state="readonly",
                                              values=["25/26 Bahar", "26/27 Güz", "26/27 Bahar", "27/28 Güz"])
        self.combo_semester.grid(row=2, column=1, padx=5, pady=10, sticky="ew")
        
        # 4. Süre
        ctk.CTkLabel(frame, text="Süre (dk):").grid(row=3, column=0, padx=5, pady=10, sticky="w")
        self.combo_interval = ctk.CTkComboBox(frame, variable=self.interval_var,
                                              state="readonly",
                                              values=["15", "20", "25", "30", "45", "60"])
        self.combo_interval.grid(row=3, column=1, padx=5, pady=10, sticky="ew")

    def _create_notification_choice(self) -> None:
        """Bildirim tercihi widget'larını oluşturur."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=10)
        
        ctk.CTkLabel(frame, text="Bildirim Tercihi:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        self.check_windows = ctk.CTkSwitch(frame, text="Windows", variable=self.notify_windows_var)
        self.check_windows.pack(side="left", padx=20)
        
        self.check_email = ctk.CTkSwitch(frame, text="E-posta", variable=self.notify_email_var)
        self.check_email.pack(side="left")

    def _create_email_fields(self) -> None:
        """E-posta ayarları (dinamik) widget'larını oluşturur."""
        self.email_settings_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        self.email_settings_frame.grid_columnconfigure(1, weight=1)
        # Pack edilmiyor, trace_add edecek

        ctk.CTkLabel(self.email_settings_frame, text="Gmail Adresi:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.entry_sender_email = ctk.CTkEntry(self.email_settings_frame, textvariable=self.sender_email_var)
        self.entry_sender_email.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.email_settings_frame, text="Uygulama Şifresi:").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        gmail_pass_frame = ctk.CTkFrame(self.email_settings_frame, fg_color="transparent")
        gmail_pass_frame.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        gmail_pass_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_gmail_pass = ctk.CTkEntry(gmail_pass_frame, textvariable=self.gmail_password_var, show="*")
        self.entry_gmail_pass.grid(row=0, column=0, sticky="ew")
        
        self.btn_toggle_gmail_pass = ctk.CTkButton(gmail_pass_frame, text="👁", width=30, command=self.toggle_gmail_pass_visibility)
        self.btn_toggle_gmail_pass.grid(row=0, column=1, padx=(5,5))
        
        ctk.CTkButton(gmail_pass_frame, text="Şifre Al", width=60, fg_color="#E0A800", text_color="black", hover_color="#C69500", 
                      command=lambda: webbrowser.open("https://myaccount.google.com/apppasswords")).grid(row=0, column=2)

        twofa_frame = ctk.CTkFrame(self.email_settings_frame, fg_color="transparent")
        twofa_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        ctk.CTkLabel(twofa_frame, text="⚠️ 2 Adımlı doğrulama açık olmalı!", text_color="orange", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        ctk.CTkButton(twofa_frame, text="Aktifleştir", width=70, fg_color="transparent", border_width=1, border_color="#E0A800", text_color="orange", hover_color="#333",
                      command=lambda: webbrowser.open("https://myaccount.google.com/signinoptions/two-step-verification")).pack(side="left", padx=5)

    def _create_advanced_fields(self) -> None:
        """ Gelişmiş ayarlar widget'larını oluşturur."""
        self.btn_toggle_advanced = ctk.CTkButton(self, text="▼ Gelişmiş Ayarlar", 
                                                 fg_color="transparent", border_width=1, 
                                                 text_color=("gray10", "gray90"), 
                                                 command=self.toggle_advanced_settings)
        self.btn_toggle_advanced.pack(fill="x", padx=5, pady=(20, 5))

        self.advanced_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.advanced_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.advanced_frame, text="Tarayıcı:").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.combo_browser = ctk.CTkComboBox(self.advanced_frame, variable=self.browser_var, state="readonly", values=["chromium", "firefox", "webkit"])
        self.combo_browser.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self._create_help_icon(self.advanced_frame, "OBIS'e bağlanmak için kullanılacak tarayıcı motoru.\nChromium önerilir.").grid(row=0, column=2, padx=5)

        self.check_minimize = ctk.CTkCheckBox(self.advanced_frame, text="Simge durumunda çalıştır", variable=self.minimize_var)
        self.check_minimize.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self._create_help_icon(self.advanced_frame, "Program kapatıldığında sistem tepsisine küçültür\nve arka planda çalışır.").grid(row=1, column=2, padx=5)

        self.check_autostart = ctk.CTkCheckBox(self.advanced_frame, text="Otomatik Başlat", variable=self.autostart_var)
        self.check_autostart.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self._create_help_icon(self.advanced_frame, "Windows açıldığında uygulama otomatik başlar.").grid(row=2, column=2, padx=5)

        self.check_stop_failure = ctk.CTkCheckBox(self.advanced_frame, text="3 Hatalı Girişte Durdur", variable=self.stop_failure_var)
        self.check_stop_failure.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self._create_help_icon(self.advanced_frame, "Hesabınızın kilitlenmemesi için\nüst üste hatalı girişlerde programı durdurur.").grid(row=3, column=2, padx=5)

    def _create_help_icon(self, parent: Any, text: str) -> ctk.CTkLabel:
        """Bilgi simgesi oluşturur."""
        lbl = ctk.CTkLabel(parent, text="?", width=20, height=20, corner_radius=10, fg_color="gray50", text_color="white")
        ToolTip(lbl, text)
        return lbl

    def toggle_advanced_settings(self) -> None:
        """ Gelişmiş ayarları göster/gizle """
        self.advanced_settings_visible = not self.advanced_settings_visible
        if self.advanced_settings_visible:
            self.advanced_frame.pack(fill="x", padx=5, pady=5, after=self.btn_toggle_advanced)
            self.btn_toggle_advanced.configure(text="▲ Gelişmiş Ayarlar")
        else:
            self.advanced_frame.pack_forget()
            self.btn_toggle_advanced.configure(text="▼ Gelişmiş Ayarlar")

    def update_email_fields_visibility(self, *args: Any) -> None:
        """ E-posta ayarlarını gizleme/kaydetme """
        if self.notify_email_var.get():
            self.email_settings_frame.pack(fill="x", padx=5, pady=10, before=self.btn_toggle_advanced)
        else:
            self.email_settings_frame.pack_forget()

    def load_settings(self) -> None:
        """Ayarları JSON dosyasından yükler."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.student_id_var.set(settings.get("student_id", ""))
                    self.obis_password_var.set(settings.get("obis_password", ""))
                    
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
            self.update_email_fields_visibility() # Manuel tetikle

    def save_settings(self) -> bool:
        """Ayarları doğrular ve kaydeder."""
        # 1. Validation
        if not self.student_id_var.get().isdigit():
            messagebox.showerror("Hata", "Öğrenci numarası sadece rakamlardan oluşmalıdır!")
            return False
        
        if not self.obis_password_var.get() or not self.semester_var.get():
             messagebox.showerror("Hata", "OBIS şifresi ve yarıyıl girilmelidir!")
             return False

        methods = []
        if self.notify_email_var.get(): methods.append("email")
        if self.notify_windows_var.get(): methods.append("windows")

        if not methods:
            messagebox.showerror("Hata", "En az bir bildirim yöntemi seçilmeli!")
            return False

        if "email" in methods:
            if not self.sender_email_var.get().endswith("@gmail.com"):
                messagebox.showerror("Hata", "Gmail adresi geçerli değil!")
                return False
            if not self.gmail_password_var.get():
                messagebox.showerror("Hata", "Email bildirimi için uygulama şifresi gerekli!")
                return False

        # 2. Kaydetme
        try:
            settings = self.get_settings_dict()
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            
            # Auto Start
            set_auto_start(self.autostart_var.get())
            
            logging.info("Ayarlar kaydedildi.")
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi.")
            return True
        except Exception as e:
            logging.error(f"Kayıt hatası: {e}")
            return False

    def get_settings_dict(self) -> Dict[str, Any]:
        """Tüm ayarların sözlük halini döner."""
        methods = []
        if self.notify_email_var.get(): methods.append("email")
        if self.notify_windows_var.get(): methods.append("windows")
        
        return {
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
            "stop_on_failures": self.stop_failure_var.get()
        }

    def set_input_state(self, state: str) -> None:
        """Giriş alanlarını (input) aktif/pasif yapar."""
        widgets = [
            self.entry_student_id, self.entry_obis_pass, 
            self.check_email, self.check_windows,
            self.entry_sender_email, self.entry_gmail_pass,
            self.check_minimize, self.check_autostart,
            self.check_stop_failure, self.btn_save, self.btn_test_mail
        ]
        
        for w in widgets:
            w.configure(state=state)
            
        combo_state = "readonly" if state == "normal" else "disabled"
        self.combo_semester.configure(state=combo_state)
        self.combo_interval.configure(state=combo_state)
        self.combo_browser.configure(state=combo_state)

    def toggle_obis_pass_visibility(self) -> None:
        """OBIS şifresini göster/gizle"""
        self.show_obis_pass = not self.show_obis_pass
        self.entry_obis_pass.configure(show="" if self.show_obis_pass else "*")
        self.btn_toggle_obis_pass.configure(text="🔒" if self.show_obis_pass else "👁")

    def toggle_gmail_pass_visibility(self) -> None:
        """Gmail şifresini göster/gizle"""
        self.show_gmail_pass = not self.show_gmail_pass
        self.entry_gmail_pass.configure(show="" if self.show_gmail_pass else "*")
        self.btn_toggle_gmail_pass.configure(text="🔒" if self.show_gmail_pass else "👁")
