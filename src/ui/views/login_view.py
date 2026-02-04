"""
BU DOSYA: Kullanıcının OBIS bilgilerini girerek sisteme 
giriş yaptığı ekran.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from ..components.card import OBISCard
from ..components.input import OBISInput
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens, OBISStyles
from ..utils.animations import OBISAnimations
import qtawesome as qta

from services.browser import BrowserService
import logging

class LoginWorker(QThread):
    """
    Arka planda BrowserService ile giriş dener.
    """
    result_signal = pyqtSignal(bool, str) # success, message

    def __init__(self, user, pwd):
        super().__init__()
        self.user = user
        self.pwd = pwd

    def run(self):
        try:
            # .Tarayıcıyı headless (görünmez) başlat
            browser = BrowserService(headless=True)
            browser.start_browser()
            
            # Login dene
            is_success = browser.login(self.user, self.pwd)
            
            browser.close_browser()
            
            if is_success:
                self.result_signal.emit(True, "Giriş Başarılı! Yönlendiriliyorsunuz...")
            else:
                self.result_signal.emit(False, "Giriş Başarısız! Lütfen bilgilerinizi kontrol ediniz.")
                
        except Exception as e:
            self.result_signal.emit(False, f"Sistem hatası: {str(e)}")

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
        
        # Ana Layout (Merkezleme için)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setSpacing(20) # Elemanlar arası boşluk
        
        self._setup_ui()
        
    def showEvent(self, event):
        """Sayfa her görüntülendiğinde çalışır."""
        super().showEvent(event)
        
        # Animasyonlar (Sadece ilk açılışta veya her girişte çalışacak şekilde ayarlandı)
        # Kart Giriş Animasyonu
        OBISAnimations.entrance_anim(self.card, delay=100)
        
    def _setup_ui(self):
        """Arayüz elemanlarını oluştur."""
        
        #! Logo daha sonradan değişecek
        # 1. Üst Bölüm (Logo ve Başlıklar)
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(5)
        
        # Logo Arkaplanı
        logo_bg = QLabel()
        logo_bg.setFixedSize(52, 52)
        logo_bg.setStyleSheet(f"""
            background-color: {OBISColors.PRIMARY};
            border-radius: {OBISDimens.RADIUS_MEDIUM}px;
        """)
        logo_bg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo İkonu
        logo_icon = qta.icon("fa5s.graduation-cap", color="white")
        logo_bg.setPixmap(logo_icon.pixmap(QSize(24, 24))) # Icon da küçüldü
        
        # Başlıklar
        title = QLabel("OBIS NOTIFIER")
        title.setFont(OBISFonts.H1)
        title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; margin-top: 10px;") # Margin azaltıldı
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("ADÜ Akademik Asistan")
        subtitle.setFont(OBISFonts.BODY)
        subtitle.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Header'a ekle (Ortalayarak)
        header_layout.addWidget(logo_bg, 0, Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        self.main_layout.addStretch() # Üst boşluk (Simetri için)
        self.main_layout.addLayout(header_layout)
        
        # 2. Login Kartı
        self.card = OBISCard(has_shadow=True)
        self.card.setFixedSize(400, 310) # Kart Boyutu
        
        # Kart stili
        self.card.setStyleSheet(OBISStyles.MAIN_CARD)
        
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
        self.inp_pass.returnPressed.connect(self._on_login_clicked) # Enter tuşu ile giriş

        # Şifre Göster/Gizle Butonu
        self.btn_toggle_pass = self.inp_pass.add_action_button("fa5s.eye", self._toggle_password_visibility)
        
        # Login Butonu
        self.btn_login = OBISButton("Giriş Yap  ", "primary", icon=qta.icon("fa5s.sign-in-alt", color="white"))
        self.btn_login.setLayoutDirection(Qt.LayoutDirection.RightToLeft) # İkonu sağa al
        self.btn_login.clicked.connect(self._on_login_clicked)
        
        form_layout.addWidget(lbl_std)
        form_layout.addWidget(self.inp_std)
        form_layout.addWidget(lbl_pass)
        form_layout.addWidget(self.inp_pass)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.btn_login)
        form_layout.addStretch()
        
        self.card.add_widget(card_content)
        self.main_layout.addWidget(self.card)

        # 3. Footer
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(2) # Metinleri yaklaştır
        footer_lbl = QLabel("Obis Notifier v3.0")
        footer_lbl.setFont(OBISFonts.SMALL)
        footer_lbl.setStyleSheet(f"color: {OBISColors.TEXT_GHOST};")
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        author_lbl = QLabel("BAŞAR ORHANBULUCU")
        author_lbl.setFont(OBISFonts.get_font(9, "bold"))
        author_lbl.setStyleSheet(f"color: {OBISColors.TEXT_GHOST}; letter-spacing: 1px;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_layout.addWidget(footer_lbl)
        footer_layout.addWidget(author_lbl)
        
        self.main_layout.addLayout(footer_layout)
        self.main_layout.addStretch() # En alta boşluk

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

    def check_auto_login(self, user, pwd):
        """
        Otomatik giriş kontrolünü başlatır.
        UI etkileşimini kapatır ve kullanıcıya bilgi verir.
        """
        self.inp_std.setText(user)
        self.inp_pass.setText(pwd)
        self._set_loading(True)
        self.btn_login.setText("Oturum Doğrulanıyor... ")
        
        self.worker = LoginWorker(user, pwd)
        self.worker.result_signal.connect(self._on_auto_login_finished)
        self.worker.start()

    def _on_login_clicked(self):
        """Giriş butonuna basılınca (Validasyonlu)"""
        user = self.inp_std.text().strip()
        pwd = self.inp_pass.text().strip()
        
        has_error = False
        
        if not user:
            self.inp_std.set_error(True)
            OBISAnimations.shake(self.inp_std) # Titreşim Efekti
            has_error = True
            
        if not pwd:
            self.inp_pass.set_error(True)
            if not has_error: # Eğer üstteki sallanıyorsa bunu biraz gecikmeli veya aynı anda salla
                OBISAnimations.shake(self.inp_pass)
            else:
                 # İkisi de boşsa ikincisini de salla
                 OBISAnimations.shake(self.inp_pass)
            has_error = True
            
        if has_error:
            return

        # Yükleniyor moduna geç
        self._set_loading(True)
        
        # Worker başlat
        self.worker = LoginWorker(user, pwd)
        self.worker.result_signal.connect(self._on_login_finished)
        self.worker.start()
        
    def _on_auto_login_finished(self, success: bool, message: str):
        """Oto login işlemi tamamlandığında."""
        self._set_loading(False)
        self.btn_login.setText("Giriş Yap  ")
        
        if success:
            logging.info("Oto-login başarılı.")
            self.login_success.emit(self.inp_std.text(), self.inp_pass.text())
        else:
            logging.warning(f"Oto-login başarısız: {message}")
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