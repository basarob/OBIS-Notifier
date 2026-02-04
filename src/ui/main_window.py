"""
BU DOSYA: Uygulamanın ana çerçevesi.
Sidebar, Topbar ve Değişen İçerik Alanlarını birleştirir.
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt
from .styles.theme import OBISStyles
from .components.sidebar import OBISSidebar
from .components.topbar import OBISTopBar
from .components.snackbar import OBISSnackbar

# Views
from .views.login_view import LoginView
from .views.dashboard import DashboardView
from .views.settings import SettingsView
from .views.logs import LogsView
from .views.profile import ProfileView

from services.session import SessionManager
import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OBIS Notifier v3.0")
        self.setFixedSize(1152, 648)
        
        # Merkezi Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        
        # --- Sayfa Yöneticisi (Login vs App) ---
        self.main_stack = QStackedWidget()
        self.central_layout.addWidget(self.main_stack)
        
        # 1. Login Ekranı
        self.login_view = LoginView()
        self.login_view.login_success.connect(self._on_login_success)
        self.main_stack.addWidget(self.login_view)
        
        # 2. Ana Uygulama Alanı (Sidebar + İçerik)
        self.app_container = QWidget()
        self.app_layout = QHBoxLayout(self.app_container)
        self.app_layout.setContentsMargins(0, 0, 0, 0)
        self.app_layout.setSpacing(0)
        
        # Sol Menü (Sidebar)
        self.sidebar = OBISSidebar()
        self.sidebar.page_changed.connect(self._change_page)
        self.app_layout.addWidget(self.sidebar)
        
        # Sağ Taraf (Topbar + Content)
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        
        # .Topbar
        self.topbar = OBISTopBar()
        self.topbar.profile_clicked.connect(self._show_profile)
        self.right_layout.addWidget(self.topbar)
        
        # İçerik Alanı (Stacked)
        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(20, 20, 20, 20) # İçerik boşluğu
        self.content_stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.content_stack.setStyleSheet(OBISStyles.MAIN_BACKGROUND)
        
        # VIEWS
        self.dash_view = DashboardView()
        self.settings_view = SettingsView()
        self.logs_view = LogsView()
        
        self.content_stack.addWidget(self.dash_view)      # Index 0
        self.content_stack.addWidget(self.settings_view)  # Index 1
        self.content_stack.addWidget(self.logs_view)      # Index 2
        # Sinyal Bağlantıları
        self.logs_view.snackbar_signal.connect(self.show_snackbar)
        
        self.right_layout.addWidget(self.content_stack)
        
        self.app_layout.addWidget(self.right_container)
        self.main_stack.addWidget(self.app_container) # Index 1: Uygulama
        
        # 3. Profil Ekranı
        self.profile_view = ProfileView()
        # Buton Bağlantıları
        self.profile_view.back_requested.connect(self._on_profile_back)
        self.profile_view.logout_requested.connect(self._logout)
        
        self.main_stack.addWidget(self.profile_view) # Index 2: Profil
        
        logging.info("---------- OBISNotifier Başlatıldı ----------")
        
        # Başlangıç: Otomatik Giriş Kontrolü
        self._check_and_auto_login()

        # Global Snackbar (En üst katman)
        self.snackbar = OBISSnackbar(self)
        
        # Mevcut kullanıcı durumu
        self.current_user = None

    def show_snackbar(self, message: str, type: str = "info"):
        """Uygulama genelinde bildirim gösterir."""
        if self.snackbar:
            self.snackbar.show_message(message, type)

    def _check_and_auto_login(self):
        """Kayıtlı oturum varsa otomatik giriş dener."""
        
        # Varsayılan olarak Login ekranındayız
        self.main_stack.setCurrentIndex(0) 
        
        credentials = SessionManager.load_session()
        
        if credentials:
            user, pwd = credentials
            logging.info(f"Oto-login tetiklendi: {user}")
            # Login view üzerindeki auto-login metodunu tetikle
            self.login_view.check_auto_login(user, pwd)
        else:
            logging.info("Kayıtlı oturum bulunamadı.")

    def _on_login_success(self, user, pwd):
        """Giriş başarılı olunca ana ekrana geç."""
        logging.info(f"MainWindow: Giriş başarılı -> {user}")
        
        # Oturumu kaydet (Güncel şifre olabilir)
        if SessionManager.save_session(user, pwd):
             logging.info("Oturum güvenli şekilde güncellendi.")
        
        # Kullanıcı durumunu güncelle
        self.current_user = user
        
        # İsim şimdilik "Ad Soyad" olarak sabit, numara ise user'dan gelir.
        self.topbar.set_user_info("Ad Soyad", user)
        self.profile_view.set_user_data("Ad Soyad", user, "Henüz kontrol yapılmadı")
        
        self.main_stack.setCurrentIndex(1) # App göster
        self.content_stack.setCurrentIndex(0) # Dashboard'u aç
        self.topbar.set_title("Ana Menü")

    def _change_page(self, index: int):
        """Sidebar butonlarına basılınca."""
        self.content_stack.setCurrentIndex(index)
        
        titles = ["Ana Menü", "Ayarlar", "Loglar"]
        if 0 <= index < len(titles):
            self.topbar.set_title(titles[index])
            
    def _show_profile(self):
        """Profil sayfasına geç (Tam Ekran)."""
        self.main_stack.setCurrentWidget(self.profile_view)

    def _on_profile_back(self):
        """Profilden geri dön."""
        self.main_stack.setCurrentWidget(self.app_container)

    def _logout(self):
        """Çıkış Yap."""
        logging.info(f"Çıkış yapılıyor: {self.current_user}")
        SessionManager.clear_session()
        self.current_user = None
        self.main_stack.setCurrentIndex(0) # Login ekranına dön
        self.show_snackbar("Başarıyla çıkış yapıldı.", "success")