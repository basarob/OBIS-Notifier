"""
BU DOSYA: Uygulama yapılandırma ayarlarının yönetildiği kontrolör (Controller) ekran.
- Arayüz bileşenlerini `settings_cards.py` içinden çağırır.
- Load, Save ve sistem güvenliği (System Running Check) işlemlerini yönetir.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os
import logging
import re
import qtawesome as qta

# UI Modülleri
from .settings_cards import SettingsAutomationCard, SettingsNotificationCard, SettingsAdvancedCard, create_label, create_icon_box
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
from ..utils.animations import OBISAnimations

# Servis ve Utils
from ui.utils.worker import TestMailWorker
from utils.system import get_user_data_dir
from utils.date_utils import get_current_semester

SETTINGS_FILE = os.path.join(get_user_data_dir(), "settings.json")


class SettingsView(QWidget):
    snackbar_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_system_running = False
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)
        self.scroll.setWidget(self.content_widget)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)

        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        self.main_container = QFrame()
        self.main_container.setObjectName("MainSettingsContainer")
        self.main_container.setStyleSheet(f"""
            QFrame#MainSettingsContainer {{
                background-color: {OBISColors.SURFACE};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                border: 1px solid rgba(0, 0, 0, 0.04);
            }}
        """)
        
        m_layout = QVBoxLayout(self.main_container)
        m_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        m_layout.setSpacing(0)
        
        # 1. Header
        header_widget = QWidget()
        h_layout = QHBoxLayout(header_widget)
        h_layout.setContentsMargins(0, 0, 0, 0) 
        t_layout = QVBoxLayout()
        t_layout.setSpacing(2)
        t_layout.addWidget(create_label("Uygulama Ayarları", OBISFonts.get_font(16, "bold"), OBISColors.TEXT_PRIMARY))
        t_layout.addWidget(create_label("Sistemin işleyişini ve bildirim tercihlerini özelleştirin.", OBISFonts.get_font(10, "normal"), OBISColors.TEXT_SECONDARY))
        icon_lbl = create_icon_box("fa5s.cog", OBISColors.TEXT_SECONDARY, border_color=OBISColors.BORDER)
        h_layout.addLayout(t_layout)
        h_layout.addStretch()
        h_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        
        m_layout.addWidget(header_widget)
        m_layout.addSpacing(24) 
        
        # 2. Body (Cards)
        self.card_automation = SettingsAutomationCard()
        self.card_notification = SettingsNotificationCard()
        self.card_advanced = SettingsAdvancedCard()

        self.card_notification.test_mail_requested.connect(self._on_test_mail_requested)

        m_layout.addWidget(self.card_automation)
        m_layout.addWidget(self.card_notification)
        m_layout.addWidget(self.card_advanced)
        m_layout.addStretch()
        
        # 3. Footer (Save Button)
        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(0, 16, 0, 0)
        self.btn_save = OBISButton("Ayarları Kaydet", "success", icon=qta.icon("fa5s.save", color=OBISColors.TEXT_WHITE))
        self.btn_save.setFixedWidth(200)
        self.btn_save.clicked.connect(self.save_settings)
        f_layout.addStretch()
        f_layout.addWidget(self.btn_save)
        
        m_layout.addWidget(footer)
        self.main_layout.addWidget(self.main_container)

    # ================= TEST MAIL İŞLEMLERİ =================

    def _on_test_mail_requested(self, email: str, pwd: str):
        has_error = False
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.card_notification.inp_gmail.set_error(True)
            OBISAnimations.shake(self.card_notification.inp_gmail)
            has_error = True
            
        if not pwd:
            self.card_notification.inp_app_pass.set_error(True)
            if not has_error:
                OBISAnimations.shake(self.card_notification.inp_app_pass)
            has_error = True
            
        if has_error:
            self.snackbar_signal.emit("Lütfen geçerli bir e-posta adresi ve şifre giriniz.", "error")
            return
            
        self.card_notification.btn_test_mail.setEnabled(False)
        self.card_notification.btn_test_mail.setText("Gönderiliyor...")
        
        self.test_worker = TestMailWorker(email, pwd)
        self.test_worker.result_signal.connect(self._on_test_mail_finished)
        self.test_worker.start()

    def _on_test_mail_finished(self, success, message):
        self.card_notification.btn_test_mail.setEnabled(True)
        self.card_notification.btn_test_mail.setText("Bildirimi Test Et")
        self.snackbar_signal.emit(message, "success" if success else "error")

    # ================= VERİ YÜKLEME / KAYDETME =================

    def load_settings(self):
        """Ayarları dosyadan yükler. Dosya yoksa varsayılan değerlerle oluşturur."""
        
        # Dosya yoksa varsayılan ayarlarla oluştur
        if not os.path.exists(SETTINGS_FILE):
            default_settings = {
                "check_interval": 20,
                "auto_semester": True,
                "semester": get_current_semester(),
                "notification_methods": [],
                "sender_email": "",
                "gmail_app_password": "",
                "browser": "chromium",
                "minimize_to_tray": False
            }
            try:
                os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(default_settings, f, indent=4)
                logging.info("Varsayılan settings.json oluşturuldu.")
            except Exception as e:
                logging.error(f"Varsayılan ayar dosyası oluşturulamadı: {e}")
        
        settings = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception as e:
                logging.error(f"Ayarlar yüklenemedi: {e}")

        # Automation
        interval = settings.get("check_interval", 20)
        is_auto_semester = settings.get("auto_semester", True)
        semester = settings.get("semester", get_current_semester())
        self.card_automation.set_data(interval, is_auto_semester, semester)

        # Notification
        methods = settings.get("notification_methods", [])
        self.card_notification.set_data(
            "email" in methods,
            settings.get("sender_email", ""),
            settings.get("gmail_app_password", "")
        )

        # Advanced (stop_on_failures artık çekirdekte kalıcı, UI'da gösterilmiyor)
        self.card_advanced.set_data(
            settings.get("browser", "chromium"),
            settings.get("minimize_to_tray", False)
        )

    def save_settings(self):
        if self._is_system_running:
            self.snackbar_signal.emit("Sistem çalışırken ayarlar değiştirilemez. Önce sistemi durdurun.", "warning")
            return

        notif_data = self.card_notification.get_data()
        
        if notif_data["email_enabled"]:
            email = notif_data["email_address"]
            pwd = notif_data["email_pwd"]
            if not email or "@" not in email:
                self.snackbar_signal.emit("Geçerli bir E-posta adresi giriniz.", "error")
                return
            if not pwd:
                self.snackbar_signal.emit("Gmail uygulama şifresi zorunludur.", "error")
                return

        try:
            current_settings = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    current_settings = json.load(f)
            
            auto_data = self.card_automation.get_data()
            adv_data = self.card_advanced.get_data()
            
            methods = ["email"] if notif_data["email_enabled"] else []
            
            current_settings.update({
                "check_interval": auto_data["check_interval"],
                "auto_semester": auto_data["auto_semester"],
                "semester": auto_data["semester"],
                "notification_methods": methods,
                "sender_email": notif_data["email_address"],
                "gmail_app_password": notif_data["email_pwd"],
                "browser": adv_data["browser"],
                "minimize_to_tray": adv_data["minimize_to_tray"]
            })
            
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(current_settings, f, indent=4)
                
            logging.info(f"Ayarlar kaydedildi. (Kontrol: {auto_data['check_interval']} dk, Dönem: {auto_data['semester']}, Tarayıcı: {adv_data['browser']})")
            self.snackbar_signal.emit("Ayarlar başarıyla kaydedildi.", "success")
            
        except Exception as e:
            logging.error(f"Ayarlar kaydedilemedi: {e}")
            self.snackbar_signal.emit(f"Kaydetme hatası: {str(e)}", "error")

    def set_system_status(self, is_running: bool):
        self._is_system_running = is_running
        self.card_automation.set_running_state(is_running)
        self.card_notification.set_running_state(is_running)
        self.card_advanced.set_running_state(is_running)
