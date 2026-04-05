"""
BU DOSYA: Kullanıcının OBIS bilgilerini girerek sisteme 
giriş yaptığı ekran.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QPixmap
import os
import sys
import logging
from config import CURRENT_VERSION
from ..components.card import OBISCard
from ..components.input import OBISInput
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens, OBISStyles
from ..utils.animations import OBISAnimations
import qtawesome as qta

from ui.utils.startup import StartupManager
from ui.utils.worker import LoginWorker

class LoginView(QWidget):
    """
    .Tam ekran ortalanmış Login Kartı.
    """
    # Sinyaller
    login_success = pyqtSignal(str, str) # username, password
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Arkaplan
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(OBISStyles.MAIN_BACKGROUND)
        
        # Snackbar
        self.snackbar = None
        
        # Sistem kontrolü durumu (Playwright hazır mı?)
        self._system_ready = False
        self._system_check_worker = None
        # Otomatik giriş beklemede mi? (Sistem bitmeden login başlatılmasın)
        self._pending_auto_login = None
        
        # Ana Layout (Merkezleme için)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setSpacing(20) # Elemanlar arası boşluk
        
        self._setup_ui()
        
    def showEvent(self, event):
        """Sayfa her görüntülendiğinde çalışır."""
        super().showEvent(event)
        
        # Kart Giriş Animasyonu
        OBISAnimations.entrance_anim(self.card, delay=100)
        
        # İlk açılışta güncellemeleri kontrol et
        if not getattr(self, "_update_checked", False):
            self._update_checked = True
            self._start_startup_checks()
        elif not self._system_ready and self.startup_manager is None:
            self._start_startup_checks()
        
    def _setup_ui(self):
        """Arayüz elemanlarını oluştur."""
        
        # 1. Üst Bölüm (Logo ve Başlıklar)
        header_layout = self._create_header()
        
        # 2. Login Kartı
        self.card = self._create_login_card()
        
        # 3. Footer
        footer_layout = self._create_footer()
        
        # Ana Layout Yerleşimi
        self.main_layout.addStretch() # Üst boşluk
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(self.card)
        self.main_layout.addLayout(footer_layout)
        self.main_layout.addStretch() # Alt boşluk

    def _create_header(self) -> QVBoxLayout:
        """Logo ve başlıkların olduğu bölümü oluşturur."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)
        
        # Logo Arkaplanı
        logo_bg = QLabel()
        logo_bg.setFixedSize(80, 80)
        logo_bg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo İkonu
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
        icon_path = os.path.join(base_path, "images", "icon.png")
        pixmap = QPixmap(icon_path)
        pixmap = pixmap.scaled(QSize(80, 80), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_bg.setPixmap(pixmap)
        
        # Başlıklar
        title = QLabel("OBIS NOTIFIER")
        title.setFont(OBISFonts.H1)
        title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; margin-top: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("ADÜ Akademik Asistan")
        subtitle.setFont(OBISFonts.BODY)
        subtitle.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(logo_bg, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return layout

    def _create_login_card(self) -> OBISCard:
        """Giriş formunun olduğu kartı oluşturur."""
        card = OBISCard(has_shadow=True)
        card.setFixedSize(400, 310)
        card.setStyleSheet(OBISStyles.MAIN_CARD)
        
        # Kart İçeriği
        card_content = QWidget()
        card_content.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(card_content)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(30, 25, 30, 25)
        
        # Öğrenci No Input
        lbl_std = QLabel("ÖĞRENCİ NUMARASI")
        lbl_std.setFont(OBISFonts.get_font(8, "medium"))
        lbl_std.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; letter-spacing: 2px;")
        self.inp_std = OBISInput(placeholder="201805121", icon_name="fa5s.user")
        
        # Şifre Input
        lbl_pass = QLabel("OBIS ŞİFRESİ")
        lbl_pass.setFont(OBISFonts.get_font(8, "medium"))
        lbl_pass.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; letter-spacing: 2px;")
        self.inp_pass = OBISInput(placeholder="********", icon_name="fa5s.lock", is_password=True)
        self.inp_pass.returnPressed.connect(self._on_login_clicked)
        
        # Şifre Göster/Gizle Butonu
        self.btn_toggle_pass = self.inp_pass.add_action_button("fa5s.eye", self._toggle_password_visibility)
        
        # Login Butonu
        self.btn_login = OBISButton("Giriş Yap  ", "primary", icon=qta.icon("fa5s.sign-in-alt", color="white"))
        self.btn_login.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.btn_login.clicked.connect(self._on_login_clicked)
        
        form_layout.addWidget(lbl_std)
        form_layout.addWidget(self.inp_std)
        form_layout.addWidget(lbl_pass)
        form_layout.addWidget(self.inp_pass)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.btn_login)
        form_layout.addStretch()
        
        card.add_widget(card_content)
        return card

    def _create_footer(self) -> QVBoxLayout:
        """Sayfa altındaki sürüm bilgisini oluşturur."""
        layout = QVBoxLayout()
        layout.setSpacing(2)
        
        footer_lbl = QLabel(f"Obis Notifier {CURRENT_VERSION}")
        footer_lbl.setFont(OBISFonts.SMALL)
        footer_lbl.setStyleSheet(f"color: {OBISColors.TEXT_GHOST};")
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        author_lbl = QLabel("BAŞAR ORHANBULUCU")
        author_lbl.setFont(OBISFonts.get_font(9, "bold"))
        author_lbl.setStyleSheet(f"color: {OBISColors.TEXT_GHOST}; letter-spacing: 1px;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(footer_lbl)
        layout.addWidget(author_lbl)
        
        return layout

    def _toggle_password_visibility(self):
        """Şifre görünürlüğünü değiştirir."""
        if self.inp_pass.line_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.inp_pass.set_password_mode(False)
            self.btn_toggle_pass.update_icon("fa5s.eye-slash")
        else:
            self.inp_pass.set_password_mode(True)
            self.btn_toggle_pass.update_icon("fa5s.eye")

    def _set_loading(self, is_loading: bool):
        """Yükleniyor durumunu yönetir."""
        self.inp_std.setEnabled(not is_loading)
        self.inp_pass.setEnabled(not is_loading)
        self.btn_login.setEnabled(not is_loading)

        if hasattr(self, 'btn_toggle_pass'):
            self.btn_toggle_pass.setEnabled(not is_loading)
        
        if is_loading:
            self.btn_login.setText("Giriş Yapılıyor... ")
            spin_icon = qta.icon('fa5s.spinner', color='white', animation=qta.Spin(self.btn_login))
            self.btn_login.setIcon(spin_icon)
        else:
            self.btn_login.setText("Giriş Yap ")
            self.btn_login.setIcon(qta.icon("fa5s.sign-in-alt", color="white"))
            self.btn_login.setLayoutDirection(Qt.LayoutDirection.RightToLeft) # İkonu sağa al

    # --- Güncelleme & Playwright Sistem Kontrolü ---

    def _start_startup_checks(self):
        """Arka planda Updater ve SystemCheck'i yöneten manager'ı başlatır."""
        self.btn_login.setEnabled(False)
        spin_icon = qta.icon('fa5s.spinner', color='white', animation=qta.Spin(self.btn_login))
        self.btn_login.setIcon(spin_icon)
        
        self.startup_manager = StartupManager()
        self.startup_manager.status_changed.connect(self._on_startup_status)
        self.startup_manager.finished.connect(self._on_startup_finished)
        self.startup_manager.start_checks()

    def _on_startup_status(self, message: str):
        self.btn_login.setText(f"{message} ")

    def _on_startup_finished(self, success: bool):
        self.startup_manager = None
        self._system_ready = success

        if success:
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Giriş Yap  ")
            self.btn_login.setIcon(qta.icon("fa5s.sign-in-alt", color="white"))
            self.btn_login.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            
            if self._pending_auto_login:
                user, pwd = self._pending_auto_login
                self._pending_auto_login = None
                self._start_auto_login(user, pwd)
        else:
            self.btn_login.setEnabled(False)
            self.btn_login.setText("Kurulum Başarısız ")
            self.btn_login.setIcon(qta.icon("fa5s.times-circle", color="white"))
            self.inp_std.setEnabled(False)
            self.inp_pass.setEnabled(False)
            
            if hasattr(self.window(), "show_snackbar"):
                self.window().show_snackbar(
                    "Tarayıcılar kurulamadı! Dosyalar temizlenip 3 saniye içinde kapatılacak.", "error"
                )
            
            QTimer.singleShot(3000, StartupManager.cleanup_and_exit)

    # --- Otomatik Giriş ---

    def check_auto_login(self, user, pwd):
        """
        Otomatik giriş kontrolünü başlatır.
        Sistem kontrolü henüz bitmemişse, giriş isteğini kuyruğa alır.
        """
        self.inp_std.setText(user)
        self.inp_pass.setText(pwd)
        
        if not self._system_ready:
            # Sistem henüz hazır değil, beklet
            self._pending_auto_login = (user, pwd)
            self.btn_login.setText("Sistem Hazırlanıyor... ")
            return
        
        self._start_auto_login(user, pwd)

    def _start_auto_login(self, user: str, pwd: str):
        """Sistem hazır olduktan sonra otomatik girişi fiilen başlatır."""
        self._set_loading(True)
        self.btn_login.setText("Oturum Doğrulanıyor... ")
        
        self.worker = LoginWorker(user, pwd)
        self.worker.result_signal.connect(self._on_auto_login_finished)
        self.worker.status_signal.connect(self._update_btn_text)
        self.worker.start()

    def _update_btn_text(self, text: str):
        """Worker'dan gelen ara durumları butona yazar."""
        self.btn_login.setText(f"{text} ")

    def _on_login_clicked(self):
        """Giriş butonuna basılınca (Validasyonlu)"""
        
        # Eğer buton kilitliyse (Sistem kurulumu veya Giriş yapma evresindeyse) işlem yapma
        if not self.btn_login.isEnabled():
            return
            
        if not self._system_ready:
            self._start_startup_checks()
            return
        
        user = self.inp_std.text().strip()
        pwd = self.inp_pass.text().strip()
        
        has_error = False
        
        if not user:
            self.inp_std.set_error(True)
            OBISAnimations.shake(self.inp_std) # Titreşim Efekti
            has_error = True
            
        if not pwd:
            self.inp_pass.set_error(True)
            if not has_error:
                OBISAnimations.shake(self.inp_pass)
            else:
                 OBISAnimations.shake(self.inp_pass)
            has_error = True
            
        if has_error:
            return

        # Yükleniyor moduna geç
        self._set_loading(True)
        
        # Worker başlat
        self.worker = LoginWorker(user, pwd)
        self.worker.result_signal.connect(self._on_login_finished)
        self.worker.status_signal.connect(self._update_btn_text)
        self.worker.start()
        
    def _on_auto_login_finished(self, success: bool, message: str):
        """Oto login işlemi tamamlandığında."""
        self._set_loading(False)
        self.btn_login.setText("Giriş Yap  ")
        
        if success:
            logging.info("Auto-login başarılı.")
            self.login_success.emit(self.inp_std.text(), self.inp_pass.text())
        else:
            logging.warning(f"Auto-login başarısız: {message}")
            if hasattr(self.window(), "show_snackbar"):
                self.window().show_snackbar("Oturum süresi dolmuş, lütfen tekrar giriş yapın.", "warning")
            else:
                QMessageBox.warning(self, "Oturum Hatası", message)

    def _on_login_finished(self, success: bool, message: str):
        """Worker bittiğinde çalışır."""
        self._set_loading(False)
        
        if success:
            self.login_success.emit(self.inp_std.text().strip(), self.inp_pass.text().strip())
        else:
            if hasattr(self.window(), "show_snackbar"):
                self.window().show_snackbar(message, "error")
            else:
                QMessageBox.warning(self, "Hata", message)