"""
BU DOSYA: Dashboard ekranını oluşturan UI bileşenlerinin (Cards) tanımlandığı yerdir.
Sadece arayüz çizimiyle ilgilenirler. Mantıksal işlevleri (controller)
Sinyaller (Signals) aracılığıyla ana DashboardView'a bildirirler.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel,QScrollArea, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from ..components.card import OBISCard
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
import qtawesome as qta
import datetime

class DashboardControlCard(OBISCard):
    """Sistemi Başlat, Şimdi Kontrol Et butonlarını ve süreyi gösteren ana kart."""
    toggle_requested = pyqtSignal()
    check_now_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # 1. Header (Başlık + Badge)
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_group = QWidget()
        t_layout = QVBoxLayout(title_group)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(3)

        title = QLabel("Sistem Kontrolü")
        title.setFont(OBISFonts.H2)
        title.setFixedHeight(24)
        title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY};")

        subtitle = QLabel("Notlarınızı otomatik olarak kontrol edin")
        subtitle.setFont(OBISFonts.BODY)
        subtitle.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")

        t_layout.addWidget(title)
        t_layout.addWidget(subtitle)

        # Durum Badge'i
        badge_container = QWidget()
        badge_layout = QVBoxLayout(badge_container)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.status_badge = QLabel(" • Kapalı ")
        self.status_badge.setFixedHeight(24)
        self.status_badge.setFont(OBISFonts.get_font(10, "bold"))
        self.update_badge_style(False)

        badge_layout.addWidget(self.status_badge)

        h_layout.addWidget(title_group)
        h_layout.addStretch()
        h_layout.addWidget(badge_container)

        # 2. Butonlar Alanı
        btn_area = QWidget()
        b_layout = QHBoxLayout(btn_area)
        b_layout.setContentsMargins(0, 20, 0, 0)
        b_layout.setSpacing(15)

        # Ana Buton (Toggle)
        self.btn_toggle = OBISButton(
            " Sistemi Başlat", "primary",
            icon=qta.icon("fa5s.play", color="white")
        )
        self.btn_toggle.setFixedHeight(90)
        self.btn_toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_toggle.setFont(OBISFonts.get_font(14, "bold"))
        self.btn_toggle.clicked.connect(self.toggle_requested.emit)

        # Yan Kontroller (Timer + Güncelleme)
        side_controls = QWidget()
        sc_layout = QVBoxLayout(side_controls)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(10)

        # --- Geri Sayım Widget ---
        self.timer_widget = QWidget()
        self.timer_widget.setFixedHeight(40)
        self.timer_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {OBISColors.HOVER_LIGHT};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                border: 1px solid {OBISColors.BORDER};
            }}
        """)
        timer_inner_layout = QHBoxLayout(self.timer_widget)
        timer_inner_layout.setContentsMargins(10, 0, 10, 0)
        timer_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        t_icon = QLabel()
        t_icon.setPixmap(qta.icon("fa5s.clock", color=OBISColors.TEXT_SECONDARY).pixmap(QSize(14, 14)))
        t_icon.setStyleSheet("border: none; background: transparent;")

        self.lbl_timer_text = QLabel("Sonraki Kontrol: --:--")
        self.lbl_timer_text.setFont(OBISFonts.get_font(10, "medium"))
        self.lbl_timer_text.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; border: none; background: transparent;")

        timer_inner_layout.addWidget(t_icon)
        timer_inner_layout.addSpacing(5)
        timer_inner_layout.addWidget(self.lbl_timer_text)

        # Şimdi Kontrol Et Butonu
        self.btn_check = OBISButton(
            "Şimdi Kontrol Et", "outline",
            icon=qta.icon("fa5s.sync-alt", color=OBISColors.TEXT_PRIMARY)
        )
        self.btn_check.setFixedHeight(40)
        self.btn_check.clicked.connect(self.check_now_requested.emit)

        sc_layout.addWidget(self.timer_widget)
        sc_layout.addWidget(self.btn_check)

        b_layout.addWidget(self.btn_toggle, 1)
        b_layout.addWidget(side_controls, 1)

        self.add_widget(header)
        self.add_widget(btn_area)

    def update_badge_style(self, is_active: bool):
        if is_active:
            text = " • Aktif "
            bg = OBISColors.SUCCESS_BG
            fg = OBISColors.SUCCESS
        else:
            text = " • Kapalı "
            bg = OBISColors.INPUT_BG
            fg = OBISColors.TEXT_SECONDARY

        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border-radius: {OBISDimens.RADIUS_MEDIUM}px;
            padding: 4px 10px;
        """)

    def update_timer_text(self, text: str, is_active: bool = True):
        self.lbl_timer_text.setText(text)
        if not is_active:
            self.lbl_timer_text.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; border: none; background: transparent;")
        else:
            self.lbl_timer_text.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; border: none; background: transparent;")


class DashboardStatsCard(OBISCard):
    """Sistemin toplam kaç döngü (check) yaptığını gösteren dev sayaç kartı."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        content = QWidget()
        stats_layout = QVBoxLayout(content)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.setSpacing(5)

        top_row = QWidget()
        tr_layout = QHBoxLayout(top_row)
        tr_layout.setContentsMargins(0, 0, 0, 0)
        tr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.sync", color=OBISColors.INFO).pixmap(QSize(16, 16)))

        lbl_cycle = QLabel("DÖNGÜ")
        lbl_cycle.setFont(OBISFonts.get_font(9, "bold"))
        lbl_cycle.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; letter-spacing: 1px;")

        tr_layout.addWidget(icon)
        tr_layout.addWidget(lbl_cycle)

        self.lbl_count = QLabel("0")
        self.lbl_count.setFont(OBISFonts.get_font(42, "bold"))
        self.lbl_count.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY};")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_sub = QLabel("Kontrol Sayısı")
        lbl_sub.setFont(OBISFonts.BODY)
        lbl_sub.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        stats_layout.addWidget(top_row)
        stats_layout.addWidget(self.lbl_count)
        stats_layout.addWidget(lbl_sub)

        self.add_widget(content)

    def set_count(self, count: int):
        """Sayacı yeni değerle günceller."""
        self.lbl_count.setText(str(count))


class DashboardTimelineCard(OBISCard):
    """Olayların asenkron olarak aktığı scroll edilebilen timeline bileşeni."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)

        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.chart-line", color=OBISColors.PRIMARY).pixmap(QSize(18, 18)))

        title = QLabel("GERÇEK ZAMANLI DURUM")
        title.setFont(OBISFonts.get_font(10, "bold"))
        title.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; letter-spacing: 1px;")

        live_badge = QLabel("Canlı Akış")
        live_badge.setStyleSheet(f"""
            background-color: {OBISColors.HOVER_LIGHT};
            color: {OBISColors.TEXT_SECONDARY};
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 10px;
        """)

        h_layout.addWidget(icon)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(live_badge)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {OBISColors.BORDER}; background-color: {OBISColors.BORDER}; height: 1px;")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ width: 6px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {OBISColors.PRESSED_LIGHT}; border-radius: 3px; }}
        """)

        self.timeline_container = QWidget()
        self.timeline_container.setStyleSheet("background: transparent;")
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setContentsMargins(0, 10, 5, 0)
        self.timeline_layout.setSpacing(10)
        self.timeline_layout.addStretch() # Yukarı dayamak için

        scroll_area.setWidget(self.timeline_container)

        self.add_widget(header)
        self.add_widget(line)
        self.layout.addWidget(scroll_area)

    def add_item(self, message: str, msg_type: str = "info"):
        """
        Timeline'a yeni bir satır ekler ve limit kontrolü yapar.
        Tipler: info, success, warn, error, system
        """
        item = QWidget()
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(15, 12, 15, 12)

        if msg_type == "success":
            bg, fg, icon_name = OBISColors.SUCCESS_BG, OBISColors.SUCCESS, "fa5s.bell"
        elif msg_type == "warn":
            bg, fg, icon_name = OBISColors.PURPLE_BG, OBISColors.PURPLE, "fa5s.book-open"
        elif msg_type == "error":
            bg, fg, icon_name = OBISColors.DANGER_BG, OBISColors.DANGER, "fa5s.exclamation-circle"
        elif msg_type == "system":
            bg, fg, icon_name = OBISColors.HOVER_LIGHT, OBISColors.TEXT_SECONDARY, "fa5s.cog"
        else:  # info
            bg, fg, icon_name = OBISColors.HOVER_BLUE, OBISColors.INFO, "fa5s.info-circle"

        item.setStyleSheet(f"QWidget {{ background-color: {bg}; border-radius: {OBISDimens.RADIUS_SMALL}px; }}")

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=fg).pixmap(QSize(20, 20)))
        icon_lbl.setStyleSheet("background: transparent; border: none;")

        lbl_msg = QLabel(message)
        lbl_msg.setFont(OBISFonts.get_font(10, "medium"))
        lbl_msg.setStyleSheet(f"color: {fg}; background: transparent; border: none;")
        lbl_msg.setWordWrap(True)

        time_str = datetime.datetime.now().strftime("%H:%M")
        lbl_time = QLabel(time_str)
        lbl_time.setFont(OBISFonts.SMALL)
        lbl_time.setStyleSheet(f"color: {fg}; opacity: 0.7; background: transparent; border: none;")

        item_layout.addWidget(icon_lbl)
        item_layout.addWidget(lbl_msg, stretch=1)
        item_layout.addWidget(lbl_time)

        # En yeni en üste
        self.timeline_layout.insertWidget(0, item)

        # Hafıza yönetimi: Max 50 item
        while self.timeline_layout.count() > 51:
            oldest_item = self.timeline_layout.takeAt(self.timeline_layout.count() - 2)
            if oldest_item and oldest_item.widget():
                oldest_item.widget().deleteLater()

    def clear(self):
        """Timeline üzerindeki tüm verileri temizler."""
        while self.timeline_layout.count() > 1:
            item = self.timeline_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
