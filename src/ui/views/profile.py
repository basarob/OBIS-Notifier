"""
BU DOSYA: Kullanıcı profil bilgilerini gösterir, bilgilerini güncelleme ve 
çıkış (logout) işlemini yönetir.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
import qtawesome as qta
import datetime
import os
import logging
from ..components.card import OBISCard
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens, OBISStyles
from ..utils.animations import OBISAnimations
from services.storage import ProfileStorageService
from services.pdf_parser import PDFParserService
from utils.system import get_user_data_dir

PROFILE_FILE = os.path.join(get_user_data_dir(), 'profile.json')

class ProfileUpdateWorker(QThread):
    """PDF indirme ve ayrıştırma işlemlerini arayüzü dondurmadan arka planda yapar."""
    result_signal = pyqtSignal(bool, str, dict) 

    def __init__(self, parser_service, storage_service, user: str, pwd: str):
        super().__init__()
        self.parser_service = parser_service
        self.storage_service = storage_service
        self.user = user
        self.pwd = pwd

    def run(self):
        try:
            logging.info("Profil güncelleme işlemi başlatıldı.")
            
            from services.browser import BrowserService
            browser = BrowserService(headless=True)
            browser.start_browser()
            
            is_success = browser.login(self.user, self.pwd)
            if not is_success:
                browser.close_browser()
                self.result_signal.emit(False, "Giriş başarısız. Oturum bilgilerinizi kontrol edip tekrar deneyin.", {})
                return
                
            pdf_path = browser.download_graduation_pdf()
            
            if pdf_path and os.path.exists(pdf_path):
                logging.info(f"PDF başarıyla indi: {pdf_path}")

                # 1. PDF'i Ayrıştır (Tüm veriler çekilir)
                parsed_data = self.parser_service.extract_graduation_data(pdf_path)
                
                # 2. JSON'a Kaydet (Gelecekte lazım olur diye hepsi kaydedilir)
                self.storage_service.save_profile_data(parsed_data)
                
                # 3. PDF'i temizle
                try:
                    os.remove(pdf_path)
                    logging.info("Geçici PDF silindi.")
                except OSError as e:
                    logging.warning(f"Geçici PDF silinemedi: {e}")
                
                browser.close_browser()
                logging.info("Profil bilgileri başarıyla güncellendi!")
                self.result_signal.emit(True, "Profil bilgileri başarıyla güncellendi!", parsed_data)
            else:
                browser.close_browser()
                self.result_signal.emit(False, "PDF dosyası indirilemedi.", {})
                
        except Exception as e:
            logging.error(f"Profil Worker hatası: {str(e)}")
            self.result_signal.emit(False, f"Güncelleme sırasında hata oluştu: {str(e)}", {})

class ProfileView(QWidget):
    logout_requested = pyqtSignal() # Çıkış isteği
    back_requested = pyqtSignal()   # Geri dön isteği
    snackbar_signal = pyqtSignal(str, str) # Bildirim yayınlamak için (Mesaj, Tip)
    profile_data_ready = pyqtSignal(dict) # Profil verisi yüklendiğinde MainWindow'a haber ver

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Spam koruması
        self.update_block_until = None
        self._is_system_running = False  # Sistem durumu bayrağı
        
        # Arkaplan
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(OBISStyles.MAIN_BACKGROUND)

        # Ana Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Servisler
        self.profile_storage = ProfileStorageService(PROFILE_FILE)
        self.pdf_parser = PDFParserService()
        
        self._setup_ui()
        
    def showEvent(self, event):
        """Sayfa her görüntülendiğinde çalışır."""
        super().showEvent(event)
        
        # Animasyonları tetikle
        OBISAnimations.slide_in(self.btn_back, direction="right", offset=50, duration=600, delay=100)
        OBISAnimations.fade_in(self.btn_back, duration=500, delay=100)
        OBISAnimations.entrance_anim(self.card, delay=200)

    def _setup_ui(self):
        """Arayüz elemanlarını oluşturur."""
        
        container_widget = QWidget()
        container_widget.setFixedWidth(460)
        container_widget.setStyleSheet("background: transparent;")
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setSpacing(2) 
        container_layout.setContentsMargins(30, 10, 30, 40)
        
        # 1. Geri Dön Butonu
        self.btn_back = OBISButton(" Geri Dön", "ghost", icon=qta.icon("fa5s.arrow-left", color=OBISColors.PRIMARY))
        self.btn_back.setStyleSheet(OBISStyles.BACK_BUTTON)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_requested.emit)
        self.btn_back.setFixedWidth(120) 

        # 2. Profil Kartı
        self.card = OBISCard(has_shadow=True)
        self.card.setFixedSize(400, 450)
        
        self.card.setStyleSheet(f"""
            OBISCard {{
                background-color: {OBISColors.SURFACE};
                border-radius: {OBISDimens.RADIUS_X_LARGE}px; 
                border: 0px; 
            }}
        """)
        
        self._setup_card_content()
        
        container_layout.addWidget(self.btn_back, 0, Qt.AlignmentFlag.AlignLeft)
        container_layout.addWidget(self.card)
        self.main_layout.addWidget(container_widget)

    def _setup_card_content(self):
        """Kartın iç yapısını oluşturur."""
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(25, 20, 25, 20)
        
        avatar = self._create_avatar_section()
        self._create_info_section()
        self._create_actions_section()
        
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(50)
        layout.addWidget(self.lbl_name)
        layout.addSpacing(5)
        layout.addWidget(self.lbl_id)
        layout.addSpacing(30)
        layout.addWidget(self.lbl_updated)
        layout.addSpacing(10)
        layout.addWidget(self.btn_update)
        layout.addSpacing(30)
        layout.addWidget(self.line_sep, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.btn_logout)
        
        self.card.add_widget(container)

    def _create_avatar_section(self) -> QLabel:
        """Avatar container oluşturur."""
        avatar_container = QLabel()
        avatar_container.setFixedSize(120, 120)
        avatar_container.setStyleSheet(f"""
            background-color: {OBISColors.AVATAR_BG}; 
            border-radius: {OBISDimens.RADIUS_FULL}px;
            border: 4px solid {OBISColors.SURFACE};
        """)
        
        icon_lbl = QLabel(avatar_container)
        icon_lbl.setPixmap(qta.icon("fa5s.user-graduate", color="white").pixmap(QSize(50, 50)))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setGeometry(0, 0, 120, 120)
        
        return avatar_container

    def _create_info_section(self):
        """İsim, numara ve tarih labellarını oluşturur."""
        self.lbl_name = QLabel("Yükleniyor...")
        self.lbl_name.setFont(OBISFonts.get_font(18, "bold"))
        self.lbl_name.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; margin-top: 20px;")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_id = QLabel("Numara: -")
        self.lbl_id.setFont(OBISFonts.BODY)
        self.lbl_id.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}")
        self.lbl_id.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_updated = QLabel("SON GÜNCELLEME: -")
        self.lbl_updated.setFont(OBISFonts.get_font(8, "bold"))
        self.lbl_updated.setStyleSheet(f"color: {OBISColors.TEXT_GHOST}; letter-spacing: 0.5px;") 
        self.lbl_updated.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def _create_actions_section(self):
        """Aksiyon butonlarını oluşturur."""
        # 1. Bilgilerimi Güncelle
        self.btn_update = OBISButton(" Bilgilerimi Güncelle", "primary", icon=qta.icon("fa5s.sync-alt", color="white"))
        self.btn_update.setFixedHeight(50) 
        self.btn_update.setFont(OBISFonts.get_font(11, "bold"))
        self.btn_update.clicked.connect(self._on_update_button_clicked)
        
        self.line_sep = QFrame()
        self.line_sep.setFrameShape(QFrame.Shape.HLine)
        self.line_sep.setStyleSheet(f"color: {OBISColors.LINE}; max-height: 5px;")
        self.line_sep.setFixedWidth(150)
        
        # 2. Çıkış Yap
        self.btn_logout = OBISButton(" Çıkış Yap", "ghost", icon=qta.icon("fa5s.sign-out-alt", color=OBISColors.DANGER))
        self.btn_logout.setStyleSheet(OBISStyles.LOGOUT_BUTTON)
        self.btn_logout.clicked.connect(self._on_logout_clicked)

    def load_initial_data(self, current_user_id: str):
        """
        Giriş başarılı olduktan sonra MainWindow tarafından çağrılır.
        Lokal dosyayı okur, varsa arayüzü doldurur. Yoksa default değer atar.
        """
        profile_data = self.profile_storage.load_profile_data()
        
        if profile_data:
            # Json varsa UI'a yaz ve MainWindow'a veriyi gönder
            self.update_ui_with_data(profile_data)
            self.profile_data_ready.emit(profile_data)
        else:
            # Json okunamadıysa veya silindiyse varsayılan görünüm bırakılır
            logging.warning("ProfileView: JSON bulunamadı, varsayılan görünüm yükleniyor.")
            self.lbl_name.setText("Bilinmeyen Kullanıcı")
            self.lbl_id.setText(f"Öğrenci Numarası: {current_user_id}")
            self.lbl_updated.setText("SON GÜNCELLEME: Bulunamadı")

    def _on_update_button_clicked(self):
        """Kullanıcı 'Bilgilerimi Güncelle' butonuna açıkça bastığında çalışır."""
        # Sistem çalışıyorsa engelle ve uyar
        if self._is_system_running:
            self.snackbar_signal.emit("Sistem çalışırken profil güncellenemez. Önce sistemi durdurun.", "warning")
            return

        if self.update_block_until and datetime.datetime.now() < self.update_block_until:
            kalan_saniye = int((self.update_block_until - datetime.datetime.now()).total_seconds())
            dakika = kalan_saniye // 60
            saniye = kalan_saniye % 60
            self.snackbar_signal.emit(f"Lütfen tekrar güncellemek için {dakika} dk {saniye} sn bekleyin.", "warning")
            return

        # 1. Güncelleme Butonunu Blokla
        self.btn_update.setEnabled(False)
        self.btn_update.setText(" Bilgiler Güncelleniyor...")
        self.btn_update.setIcon(qta.icon("fa5s.sync", color="white", animation=qta.Spin(self.btn_update)))
        
        # 2. Geri Dön Butonunu Blokla
        self.btn_back.setEnabled(False)
        self.btn_back.setCursor(Qt.CursorShape.ArrowCursor)

        # 3. Çıkış Yap Butonunu Blokla
        self.btn_logout.setEnabled(False)
        self.btn_logout.setCursor(Qt.CursorShape.ArrowCursor)

        from services.session import SessionManager
        credentials = SessionManager.load_session()
        if not credentials:
            self.snackbar_signal.emit("Oturum bilgileri bulunamadı, lütfen tekrar giriş yapın.", "error")
            self._reset_update_button()
            return
            
        user, pwd = credentials
        
        self.worker = ProfileUpdateWorker(self.pdf_parser, self.profile_storage, user, pwd)
        self.worker.result_signal.connect(self._on_update_completed)
        self.worker.start()

    def _on_update_completed(self, success: bool, message: str, data: dict):
        """Worker işlemi bitirdiğinde (başarılı/başarısız) tetiklenir."""
        if success:
            self.update_block_until = datetime.datetime.now() + datetime.timedelta(minutes=10)
            
            # Arayüzü yeni verilerle doldur ve MainWindow'a bildir
            self.update_ui_with_data(data)
            self.profile_data_ready.emit(data)
            self.snackbar_signal.emit(message, "success")
        else:
            self.snackbar_signal.emit(message, "error")

        self._reset_update_button()

    def _reset_update_button(self):
        """Butonları normal tıklanabilir haline geri döndürür."""
        # 1. Güncelle Butonunu Aç
        self.btn_update.setEnabled(True)
        self.btn_update.setText(" Bilgilerimi Güncelle")
        self.btn_update.setIcon(qta.icon("fa5s.sync-alt", color="white"))
        
        # 2. Geri Dön Butonunu Aç
        self.btn_back.setEnabled(True)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)

        # 3. Çıkış Yap Butonunu Aç
        self.btn_logout.setEnabled(True)
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)

    def update_ui_with_data(self, data: dict):
        """Gelen JSON verisi ile ekrandaki etiketleri günceller."""
        ogrenci = data.get("ogrenci_bilgileri", {})

        ad_soyad = ogrenci.get("ad_soyad", "Bilinmeyen Kullanıcı")
        numara = ogrenci.get("numara", "")
        last_updated = data.get("son_guncelleme", "-")

        self.lbl_name.setText(ad_soyad)
        if numara:
            self.lbl_id.setText(f"Öğrenci Numarası: {numara}")
        self.lbl_updated.setText(f"SON GÜNCELLEME: {last_updated}")

    def _on_logout_clicked(self):
        """Çıkış yapılırken sayfanın iç durumunu (cooldown vb.) sıfırlar ve ana pencereye sinyal gönderir."""
        # 1. 10 dakikalık blokajı sıfırla
        self.update_block_until = None 
        
        # 2. Asıl çıkış işlemini yapması için MainWindow'a haber ver
        self.logout_requested.emit()

    def set_system_status(self, is_running: bool):
        """
        Sistem çalışma durumunu kaydeder.
        Güncelle butonu tıklanabilir kalır ama snackbar ile uyarır.
        Çıkış butonu her zaman aktif kalır (güvenli kapanma sağlanır).
        """
        self._is_system_running = is_running
