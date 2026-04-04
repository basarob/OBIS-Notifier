"""
BU DOSYA: Uygulamanın ana çerçevesi.
Sidebar, Topbar ve Değişen İçerik Alanlarını birleştirir.
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QSystemTrayIcon, QMenu, QApplication, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
import os
import json
from datetime import datetime
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
from utils.system import get_user_data_dir
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
        self.profile_view = ProfileView()

        # Snackbar Sinyal Bağlantıları
        self.dash_view.snackbar_signal.connect(self.show_snackbar)
        self.settings_view.snackbar_signal.connect(self.show_snackbar)
        self.logs_view.snackbar_signal.connect(self.show_snackbar)
        self.profile_view.snackbar_signal.connect(self.show_snackbar)
        
        # Dashboard <-> Diğer View'lar Senkronizasyonu
        self.dash_view.system_status_changed.connect(self.sidebar.set_system_status)
        self.dash_view.system_status_changed.connect(self.settings_view.set_system_status)
        self.dash_view.system_status_changed.connect(self.profile_view.set_system_status)
        self.dash_view.last_check_updated.connect(self.topbar.set_last_check_time)
        
        self.content_stack.addWidget(self.dash_view)      # Index 0
        self.content_stack.addWidget(self.settings_view)  # Index 1
        self.content_stack.addWidget(self.logs_view)      # Index 2

        self.right_layout.addWidget(self.content_stack)
        self.app_layout.addWidget(self.right_container)
        self.main_stack.addWidget(self.app_container) # Index 1: Uygulama
        
        # Profil görünümü sinyal bağlantıları
        self.profile_view.profile_data_ready.connect(self._on_profile_data_ready)
        self.profile_view.back_requested.connect(self._on_profile_back)
        self.profile_view.logout_requested.connect(self._logout)
        
        self.main_stack.addWidget(self.profile_view) # Index 2: Profil
        
        # Açılış loglaması
        logging.info(f"---------- OBISNotifier Başlatıldı ({datetime.now().strftime('%d.%m.%Y %H:%M:%S')}) ----------")
        
        # Başlangıç: Otomatik Giriş Kontrolü
        self._check_and_auto_login()

        # Global Snackbar (En üst katman)
        self.snackbar = OBISSnackbar(self)
        
        # Mevcut kullanıcı durumu
        self.current_user = None
        
        self._setup_tray_icon()

    def showEvent(self, event):
        super().showEvent(event)
        
        notes_path = os.path.join(get_user_data_dir(), "release_notes.txt")
        if getattr(self, "_notes_checked", False) == False:
            self._notes_checked = True
            if os.path.exists(notes_path):
                try:
                    with open(notes_path, "r", encoding="utf-8") as f:
                        notes = f.read()
                    
                    msg = QMessageBox(self)
                    msg.setWindowTitle("OBIS Notifier Güncellendi!")
                    msg.setText("YENİ SÜRÜM NOTLARI")
                    msg.setInformativeText("Yeni sürüm başarıyla yüklendi. Neler değişti görmek için detayları inceleyebilirsiniz.")
                    msg.setDetailedText(notes)
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.exec()
                    
                    os.remove(notes_path)
                except Exception as e:
                    logging.error(f"Sürüm notları okunamadı: {e}")

    def _setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = os.path.join(os.path.dirname(__file__), "..", "images", "icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(QApplication.windowIcon())
            
        tray_menu = QMenu()
        
        show_action = QAction("Uygulamayı Göster", self)
        show_action.triggered.connect(self.show_window)
        
        quit_action = QAction("Çıkış", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
    def _tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.activateWindow()
        if self.isMinimized():
            self.showNormal()

    def quit_app(self):
        QApplication.quit()

    def closeEvent(self, event):
        settings_file = os.path.join(get_user_data_dir(), "settings.json")
        minimize_to_tray = False
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    minimize_to_tray = settings.get("minimize_to_tray", False)
            except Exception:
                pass
                
        if minimize_to_tray:
            event.ignore()
            self.hide()
            self.tray_icon.show()
            if not getattr(self, '_tray_message_shown', False):
                self.tray_icon.showMessage(
                    "OBIS Notifier",
                    "Uygulama arka planda çalışmaya devam ediyor.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
                self._tray_message_shown = True
        else:
            QApplication.quit()
            event.accept()

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
            logging.info(f"Auto-login tetiklendi: {user}")
            # Login view üzerindeki auto-login metodunu tetikle
            self.login_view.check_auto_login(user, pwd)
        else:
            logging.info("Kayıtlı oturum bulunamadı.")

    def _on_login_success(self, user, pwd):
        """Giriş başarılı olunca ana ekrana geç."""
        logging.info(f"Oturumu açıldı: {user}")
        
        # Oturumu kaydet (Güncel şifre olabilir)
        if SessionManager.save_session(user, pwd):
             logging.info("Oturum güvenli şekilde güncellendi.")
        
        # Kullanıcı durumunu güncelle
        self.current_user = user
        
        # Sadece varsayılan yükleniyor durumu ata (Sinyal geldiğinde asıl veri yazılacak)
        self.topbar.set_user_info("Yükleniyor...", user)

        # Profile view'a artık set_user_data yerine doğrudan yükleme emri veriyoruz:
        self.profile_view.load_initial_data(user)

        self.main_stack.setCurrentIndex(1) # App göster
        self.content_stack.setCurrentIndex(0) # Dashboard'u aç
        self.topbar.set_title("Ana Menü")

    def _on_profile_data_ready(self, data: dict):
        """ProfileView veriyi parse ettiğinde (ilk açılışta veya güncellendiğinde) burası çalışır."""

        # PDF'ten alınan veriyi topbar'a yazdır
        name = data.get("ogrenci_bilgileri", {}).get("ad_soyad", "Bilinmeyen Kullanıcı")
        
        # .Topbar'ı güncelle
        student_id = data.get("ogrenci_bilgileri", {}).get("numara", self.current_user)
        self.topbar.set_user_info(name, student_id)

        # Dashboard Timeline'a bildir
        self.dash_view.timeline_card.add_item(
            f"Profil bilgileri güncellendi. ({name})", "success"
        )

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
        """
        Çıkış Yap. Sistem çalışıyorsa güvenli şekilde durdurur,
        tüm oturum verilerini ve UI cache'lerini temizler.
        """
        logging.info(f"Çıkış yapılıyor: {self.current_user}")

        # 1. Dashboard: Sistem durdur + Timeline/Sayaç/Timer sıfırla
        self.dash_view.reset_state()

        # 2. Loglar: Tablo temizle
        self.logs_view.reset_state()

        # 3. Oturum verilerini sil (Keyring + session.json + profile.json)
        SessionManager.clear_session()

        # 4. Topbar sıfırla
        self.topbar.set_user_info("", "")
        self.topbar.set_title("Ana Menü")

        # 5. Sidebar'ı ilk durumuna getir (Dashboard seçili)
        self.sidebar.set_system_status(False)
        self.content_stack.setCurrentIndex(0)

        self.current_user = None
        self.main_stack.setCurrentIndex(0)  # Login ekranına dön
        self.show_snackbar("Başarıyla çıkış yapıldı.", "success")