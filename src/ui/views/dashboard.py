"""
BU DOSYA: Ana kontrol paneli. Sistem durumu, döngü sayısı
ve başlat/durdur butonları.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from ..components.card import OBISCard
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
import qtawesome as qta

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scroll Area (İçerik taşarsa diye)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.content_widget = QWidget()
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)
        
        self.scroll.setWidget(self.content_widget)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
        
        self._setup_ui()

    def _setup_ui(self):
        # 1. Üst Kısım: Sistem Kontrolü Kartı ve Sayaç Kartı
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        # --- Sol: Sistem Kontrolü ---
        control_card = OBISCard()
        
        # Başlık ve Badge
        header_layout = QHBoxLayout()
        title = QLabel("Sistem Kontrolü")
        title.setFont(OBISFonts.H2)
        
        status_badge = QLabel(" • Aktif ")
        status_badge.setStyleSheet(f"""
            background-color: {OBISColors.SUCCESS_BG};
            color: {OBISColors.SUCCESS};
            border-radius: {OBISDimens.RADIUS_MEDIUM}px;
            padding: 4px 8px;
            font-weight: bold;
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_badge)
        
        desc = QLabel("Otomasyonu anlık olarak yönetin ve durumu izleyin.")
        desc.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        
        # Butonlar
        btns_layout = QHBoxLayout()
        
        # Büyük Kırmızı Başlat/Durdur Butonu
        self.btn_toggle = OBISButton("Sistemi Durdur", "danger", icon=qta.icon("fa5s.stop-circle", color="white"))
        self.btn_toggle.setFixedHeight(80) # Büyük buton
        self.btn_toggle.setMinimumWidth(200)
        
        # Sağdaki küçük butonlar
        right_btns = QVBoxLayout()
        self.btn_test = OBISButton("Bildirimi Test Et", "outline", icon=qta.icon("fa5s.paper-plane", color=OBISColors.TEXT_PRIMARY))
        self.btn_check = OBISButton("Güncellemeleri Kontrol Et", "outline", icon=qta.icon("fa5s.sync", color=OBISColors.TEXT_PRIMARY))
        
        right_btns.addWidget(self.btn_test)
        right_btns.addWidget(self.btn_check)
        
        btns_layout.addWidget(self.btn_toggle)
        btns_layout.addSpacing(15)
        btns_layout.addLayout(right_btns)
        
        # Kart montajı
        c_layout = QVBoxLayout()
        c_layout.addLayout(header_layout)
        c_layout.addWidget(desc)
        c_layout.addSpacing(20)
        c_layout.addLayout(btns_layout)
        
        c_container = QWidget()
        c_container.setLayout(c_layout)
        control_card.add_widget(c_container)
        
        # --- Sağ: Sayaç Kartı ---
        stats_card = OBISCard()
        stats_card.setFixedWidth(250)
        
        s_layout = QVBoxLayout()
        s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = qta.icon("fa5s.sync-alt", color=OBISColors.PRIMARY)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon.pixmap(QSize(24, 24)))
        
        cycle_lbl = QLabel("DÖNGÜ")
        cycle_lbl.setFont(OBISFonts.get_font(9, "bold"))
        cycle_lbl.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; letter-spacing: 1px;")
        
        count_lbl = QLabel("15")
        count_lbl.setFont(OBISFonts.get_font(36, "bold"))
        count_lbl.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY};")
        
        sub_lbl = QLabel("Günlük Kontrol Sayısı")
        sub_lbl.setFont(OBISFonts.SMALL)
        sub_lbl.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        
        s_layout.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignRight)
        s_layout.addWidget(cycle_lbl, 0, Qt.AlignmentFlag.AlignRight)
        s_layout.addWidget(count_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(sub_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        
        s_container = QWidget()
        s_container.setLayout(s_layout)
        stats_card.add_widget(s_container)
        
        top_row.addWidget(control_card)
        top_row.addWidget(stats_card)
        
        self.main_layout.addLayout(top_row)
        
        # 2. Alt Kısım: Gerçek Zamanlı Durum (Timeline)
        
        # Başlık ve Canlı Tag
        timeline_header = QHBoxLayout()
        
        t_title = QLabel("GERÇEK ZAMANLI DURUM")
        t_title.setFont(OBISFonts.get_font(10, "bold"))
        t_title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; letter-spacing: 1px;")
        t_icon = QLabel()
        t_icon.setPixmap(qta.icon("fa5s.chart-line", color=OBISColors.PRIMARY).pixmap(QSize(16, 16)))
        
        live_tag = QLabel("Canlı Akış")
        live_tag.setStyleSheet(f"background: {OBISColors.PRESSED_LIGHT}; color: {OBISColors.TEXT_SECONDARY}; padding: 4px 8px; border-radius: {OBISDimens.RADIUS_SMALL}px; font-size: {OBISDimens.TEXT_BODY}px;")
        
        timeline_header.addWidget(t_icon)
        timeline_header.addWidget(t_title)
        timeline_header.addStretch()
        timeline_header.addWidget(live_tag)
        
        timeline_card = OBISCard()
        
        # timeline content placeholder
        t_content = QVBoxLayout()
        # Mock item
        mock_msg = QLabel("ℹ️ Kontrol tamamlandı, herhangi bir değişiklik bulunamadı.  14:47")
        mock_msg.setStyleSheet(f"background: {OBISColors.HOVER_BLUE}; color: {OBISColors.PRIMARY}; padding: 10px; border-radius: {OBISDimens.RADIUS_SMALL}px;")
        
        mock_success = QLabel("🔔 Bildirim başarıyla gönderildi.  14:32")
        mock_success.setStyleSheet(f"background: {OBISColors.SUCCESS_BG}; color: {OBISColors.SUCCESS}; padding: 10px; border-radius: {OBISDimens.RADIUS_SMALL}px;")
        
        t_content.addWidget(mock_msg)
        t_content.addSpacing(10)
        t_content.addWidget(mock_success)
        t_content.addStretch()
        
        t_container = QWidget()
        t_container.setLayout(t_content)
        
        # Header'ı da karta ekleyelim ama ayrı
        h_container = QWidget()
        h_container.setLayout(timeline_header)
        
        timeline_card.add_widget(h_container)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {OBISColors.BORDER};")
        timeline_card.add_widget(line)
        
        timeline_card.add_widget(t_container)
        
        self.main_layout.addWidget(timeline_card)
        
        self.main_layout.addStretch()