"""
BU DOSYA: Ana kontrol paneli. Sistem durumu, döngü sayısı 
ve anlık durum akışını (Timeline) içerir.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from ..components.card import OBISCard
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
import qtawesome as qta
import datetime

class DashboardView(QWidget):
    # Sidebar ile iletişim için sinyal
    system_status_changed = pyqtSignal(bool)
    # Bildirim yayınlamak için sinyal (Mesaj, Tip)
    snackbar_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Ana Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        
        # Ana Layout
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15) # Kartlar arası boşluk
        
        layout.addWidget(self.content_widget)
        
        self.is_system_running = False # Sistem durumu state'i
        
        # .Timer Ayarları
        self.CHECK_INTERVAL = int(15 * 60) 
        self.time_left = self.CHECK_INTERVAL
        
        self.last_manual_check_time = None # Son manuel kontrol zamanı
        
        # Spam Koruması (Toggle)
        self.toggle_timestamps = [] # Son işlem zamanları
        self.toggle_block_until = None # Engelleme bitiş zamanı
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.setInterval(1000) # 1 Saniye
        
        self._setup_ui()

    def _setup_ui(self):
        """Arayüz bileşenlerini oluşturur."""
        
        # --- 1. ÜST BÖLÜM (Sistem Kontrolü + Sayaç) ---
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)
        
        # A. Sistem Kontrol Kartı
        self.control_card = self._create_control_card()
        top_layout.addWidget(self.control_card, stretch=2)
        
        # B. Sayaç Kartı
        self.stats_card = self._create_stats_card()
        top_layout.addWidget(self.stats_card, stretch=1)
        
        self.main_layout.addWidget(top_section)
        
        # --- 2. ALT BÖLÜM (Anlık Durum) ---
        self.timeline_card = self._create_timeline_card()
        self.main_layout.addWidget(self.timeline_card, stretch=1) 

    def _create_control_card(self) -> OBISCard:
        """Sistem kontrol kartını oluşturur."""
        card = OBISCard()
        
        # 1. Header (Başlık + Badge)
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Üstten hizala
        
        # Başlık Grubu
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
        self.status_badge.setFixedHeight(24) # .Title ile aynı yükseklik
        self.status_badge.setFont(OBISFonts.get_font(10, "bold"))
        self._update_badge_style(False) # Başlangıçta kapalı
        
        badge_layout.addWidget(self.status_badge)
        
        h_layout.addWidget(title_group)
        h_layout.addStretch()
        h_layout.addWidget(badge_container)
        
        # 2. Butonlar Alanı
        btn_area = QWidget()
        b_layout = QHBoxLayout(btn_area)
        b_layout.setContentsMargins(0, 20, 0, 0) # Headerdan uzaklaş
        b_layout.setSpacing(15)
        
        # Ana Buton (Toggle)
        self.btn_toggle = OBISButton(" Sistemi Başlat", "primary", icon=qta.icon("fa5s.play", color="white"))
        self.btn_toggle.setFixedHeight(90) 
        self.btn_toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Enine genişle
        self.btn_toggle.setFont(OBISFonts.get_font(14, "bold"))
        self.btn_toggle.clicked.connect(self._toggle_system)
        
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
        # İçerik ortalı
        t_layout = QHBoxLayout(self.timer_widget)
        t_layout.setContentsMargins(10, 0, 10, 0)
        t_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Ortala
        
        # İkon
        t_icon = QLabel()
        t_icon.setPixmap(qta.icon("fa5s.clock", color=OBISColors.TEXT_SECONDARY).pixmap(QSize(14, 14)))
        t_icon.setStyleSheet("border: none; background: transparent;")
        
        # Label: "Sonraki Kontrol: --:--"
        self.lbl_timer_text = QLabel("Sonraki Kontrol: --:--")
        self.lbl_timer_text.setFont(OBISFonts.get_font(10, "medium"))
        self.lbl_timer_text.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; border: none; background: transparent;")
        
        t_layout.addWidget(t_icon)
        t_layout.addSpacing(5)
        t_layout.addWidget(self.lbl_timer_text)
        
        # Güncelleme Butonu
        self.btn_check = OBISButton("Şimdi Kontrol Et", "outline", icon=qta.icon("fa5s.sync-alt", color=OBISColors.TEXT_PRIMARY))
        self.btn_check.setFixedHeight(40)
        self.btn_check.clicked.connect(self._check_now)
        
        sc_layout.addWidget(self.timer_widget)
        sc_layout.addWidget(self.btn_check)
        
        # Sol ve Sağ bölümleri %50 - %50 yerleştir
        b_layout.addWidget(self.btn_toggle, 1)
        b_layout.addWidget(side_controls, 1)
        
        # Karta ekle
        card.add_widget(header)
        card.add_widget(btn_area)
        
        return card

    def _create_stats_card(self) -> OBISCard:
        """Döngü sayacı kartını oluşturur."""
        card = OBISCard()

        # Kart içeriğini ortala
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)
        
        # İkon ve Başlık
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
        
        # Büyük Sayı
        self.lbl_count = QLabel("15")
        self.lbl_count.setFont(OBISFonts.get_font(42, "bold"))
        self.lbl_count.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY};")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Alt Açıklama
        lbl_sub = QLabel("Günlük Kontrol Sayısı")
        lbl_sub.setFont(OBISFonts.BODY)
        lbl_sub.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(top_row)
        layout.addWidget(self.lbl_count)
        layout.addWidget(lbl_sub)
        
        card.add_widget(content)
        return card
        
    def _create_timeline_card(self) -> OBISCard:
        """Anlık durum akışı kartı."""
        card = OBISCard()
        # Kartın dikey olarak genişlemesini sağlamak için size policy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Header
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
        
        # Ayırıcı
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {OBISColors.BORDER}; background-color: {OBISColors.BORDER}; height: 1px;")
        
        # --- Scroll Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Scroll arkaplanını ve border'ını kaldır
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
        
        # Yukarı dayalı olması için stretch ekle (alttan iter)
        self.timeline_layout.addStretch()
        
        scroll_area.setWidget(self.timeline_container)
        
        # --- Mock Data ---
        
        self._add_timeline_item("Kontrol tamamlandı, herhangi bir değişiklik bulunamadı.", "info")
        self._add_timeline_item("Bildirim başarıyla gönderildi.", "success")
        self._add_timeline_item("Yeni bir ders notu eklendi: Veri Madenciliği!", "warn")
        
        # Hepsini karta monte et
        card.add_widget(header)
        card.add_widget(line)
        # Scroll Area'yı karta ekle ama genişleyebilsin
        card.layout.addWidget(scroll_area) 
        
        return card

    def _add_timeline_item(self, message: str, type: str = "info"):
        """Timeline'a yeni bir satır ekler."""
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Stil Belirleme
        if type == "success":
            bg = OBISColors.SUCCESS_BG
            fg = OBISColors.SUCCESS
            icon_name = "fa5s.bell"
        elif type == "warn": 
            bg = OBISColors.PURPLE_BG
            fg = OBISColors.PURPLE
            icon_name = "fa5s.book-open"
        elif type == "error":
            bg = OBISColors.DANGER_BG
            fg = OBISColors.DANGER
            icon_name = "fa5s.exclamation-circle"
        else: # Info
            bg = OBISColors.HOVER_BLUE
            fg = OBISColors.INFO
            icon_name = "fa5s.info-circle"
            
        item.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border-radius: {OBISDimens.RADIUS_SMALL}px;
            }}
        """)
        
        # İkon
        icon = QLabel()
        icon.setPixmap(qta.icon(icon_name, color=fg).pixmap(QSize(20, 20)))
        icon.setStyleSheet("background: transparent; border: none;")
        
        # Mesaj
        lbl_msg = QLabel(message)
        lbl_msg.setFont(OBISFonts.get_font(10, "medium"))
        lbl_msg.setStyleSheet(f"color: {fg}; background: transparent; border: none;")
        lbl_msg.setWordWrap(True)
        
        # Saat
        time_str = datetime.datetime.now().strftime("%H:%M")
        lbl_time = QLabel(time_str)
        lbl_time.setFont(OBISFonts.SMALL)
        lbl_time.setStyleSheet(f"color: {fg}; opacity: 0.7; background: transparent; border: none;")
        
        layout.addWidget(icon)
        layout.addWidget(lbl_msg, stretch=1)
        layout.addWidget(lbl_time)
        
        # Layout'un en başına ekle (Stretch en sonda kalmalı)
        # .Timeline layout'unda kaç widget var?
        self.timeline_layout.insertWidget(0, item)

    def _update_badge_style(self, is_active: bool):
        """Badge rengini ve metnini günceller."""
        if is_active:
            text = " • Aktif "
            bg = OBISColors.SUCCESS_BG
            fg = OBISColors.SUCCESS
        else:
            text = " • Kapalı "
            bg = OBISColors.INPUT_BG # Gri
            fg = OBISColors.TEXT_SECONDARY
            
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border-radius: {OBISDimens.RADIUS_MEDIUM}px;
            padding: 4px 10px;
        """)

    def _toggle_system(self):
        """Sistemi başlat/durdur."""
        
        # --- SPAM KORUMASI ---
        
        # 1. Kilit Kontrolü
        if self.toggle_block_until:
             if datetime.datetime.now() < self.toggle_block_until:
                 remaining = (self.toggle_block_until - datetime.datetime.now()).seconds
                 self.snackbar_signal.emit(f"Çok fazla deneme yaptınız. {remaining} sn bekleyin.", "warning")
                 return
             else:
                 self.toggle_block_until = None # Kilit süresi doldu

        # 2. Timestamp Ekle
        now = datetime.datetime.now()
        self.toggle_timestamps.append(now)

        # 3. 30 Saniyeden Eskileri Temizle
        cutoff = now - datetime.timedelta(seconds=30)
        self.toggle_timestamps = [t for t in self.toggle_timestamps if t > cutoff]

        # 4. Burst Kontrolü (4 İşlem)
        if len(self.toggle_timestamps) > 4:
            self.toggle_block_until = now + datetime.timedelta(seconds=30)
            self.snackbar_signal.emit("Çok hızlı işlem yapıyorsunuz. Sistem 30 saniye kilitlendi.", "error")
            return

        # 5. Kısa Süreli Buton Kilidi (1 sn) - Çift tıklamayı önler
        self.btn_toggle.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.btn_toggle.setEnabled(True))
        
        # --- İŞLEM DEVAMI ---
        
        self.is_system_running = not self.is_system_running
        
        # 1. UI Güncelle
        self._update_badge_style(self.is_system_running)
        
        if self.is_system_running:
            # Durdur moduna geç
            self.btn_toggle.setText(" Sistemi Durdur")
            self.btn_toggle.set_type("danger") # Kırmızı
            self.btn_toggle.setIcon(qta.icon("fa5s.stop-circle", color="white"))
            
            # .Timer'ı başlat
            self.time_left = self.CHECK_INTERVAL
            self._update_timer_label()
            self.timer.start()
        else:
            # Başlat moduna geç
            self.btn_toggle.setText(" Sistemi Başlat")
            self.btn_toggle.set_type("primary") # Mavi/Mor
            self.btn_toggle.setIcon(qta.icon("fa5s.play", color="white"))
            
            # .Timer'ı durdur ve sıfırla
            self._reset_timer()
            
        # 2. Sinyal Gönder (Sidebar güncellensin)
        self.system_status_changed.emit(self.is_system_running)

    def _on_timer_tick(self):
        """Her saniye çalışır."""
        self.time_left -= 1
        
        if self.time_left <= 0:
            # Süre bitti, başa dön (Simülasyon)
            # Gerçekte burada kontrol fonksiyonu çağrılacak.
            self.time_left = self.CHECK_INTERVAL
            self._add_timeline_item("Otomatik kontrol tetiklendi.", "info")
            
        self._update_timer_label()

    def _update_timer_label(self):
        """Zamanı MM:SS formatına çevirip yazar."""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_str = f"{minutes:02}:{seconds:02}"
        
        self.lbl_timer_text.setText(f"Sonraki Kontrol: {time_str}")

    def _reset_timer(self):
        """Zamanlayıcıyı durdurur ve sıfırlar."""
        self.timer.stop()
        self.lbl_timer_text.setText("Sonraki Kontrol: --:--")
        self.lbl_timer_text.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY}; border: none; background: transparent;")

    def _check_now(self):
        """Şimdi kontrol et butonu mantığı."""
        # 1. Sistem Kontrolü
        if not self.is_system_running:
            self.snackbar_signal.emit("Önce sistemi başlatmalısınız.", "error")
            return

        # 2. Süre Kontrolü (10 dakikadan az kaldıysa)
        # 10 dakika = 600 saniye
        if self.time_left < 600:
             self.snackbar_signal.emit("Otomatik kontrole 10 dakikadan az kaldı, manuel kontrol gerekmez.", "warning")
             return

        # 3. Spam/Cooldown Kontrolü (10 dakika)
        if self.last_manual_check_time:
            elapsed = (datetime.datetime.now() - self.last_manual_check_time).total_seconds()
            if elapsed < 600:
                self.snackbar_signal.emit("Çok sık kontrol yapamazsınız. Lütfen bekleyin.", "warning")
                return

        # --- BAŞARILI ---
        self._add_timeline_item("Manuel kontrol başlatıldı.", "info")
        self.snackbar_signal.emit("Kontrol başlatıldı.", "success")
        
        self.last_manual_check_time = datetime.datetime.now()
        
        # .Timer'ı sıfırla (Başa sar)
        self.time_left = self.CHECK_INTERVAL
        self._update_timer_label()
        # .Timer zaten çalışıyor olmalı ama garantileyelim
        if not self.timer.isActive():
            self.timer.start()