"""
BU DOSYA: Uygulama yapılandırma ayarlarının yönetildiği ekran.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QMessageBox, QGridLayout, QPushButton
from PyQt6.QtCore import Qt, QSize
import json
import os
import logging
import webbrowser
import qtawesome as qta

# UI Components
from ..components.card import OBISCard
from ..components.input import OBISInput
from ..components.button import OBISButton
from ..components.switch import OBISSwitch
from ..components.combobox import OBISCombobox
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
from ..components.snackbar import OBISSnackbar
from utils.system import set_auto_start, get_user_data_dir
from utils.date_utils import generate_semester_list, get_current_semester

SETTINGS_FILE = os.path.join(get_user_data_dir(), "settings.json")

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_scroll_area()
        self._setup_ui()
        self.load_settings()

    def _init_scroll_area(self):
        """Scroll yapısını ve ana çerçeveyi kurar."""
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
        """)
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

    def _setup_ui(self):
        """Tasarım parçalarını birleştirir."""
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
        
        m_layout.addWidget(self._create_header())
        m_layout.addSpacing(24) 
        m_layout.addWidget(self._create_body())
        m_layout.addStretch()
        m_layout.addWidget(self._create_footer())
        
        self.main_layout.addWidget(self.main_container)

    # ================= YARDIMCI METOTLAR (UI BUILDERS) =================
    
    def _create_label(self, text, font, color=None, word_wrap=False) -> QLabel:
        """Standart QLabel oluşturur."""
        lbl = QLabel(text)
        lbl.setFont(font)
        if color:
            lbl.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        lbl.setWordWrap(word_wrap)
        return lbl

    def _create_icon_box(self, icon_name, icon_color, bg_color="transparent", size=18, box_size=36, border_color=None) -> QLabel:
        """Yuvarlatılmış kare ikon kutusu oluşturur."""
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFixedSize(box_size, box_size)
        
        b_css = f"border: 1px solid {border_color};" if border_color else "border: none;"
        lbl.setStyleSheet(f"background-color: {bg_color}; {b_css} border-radius: {OBISDimens.RADIUS_SMALL}px;")
        lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(QSize(size, size)))
        return lbl

    def _add_section_header(self, layout, text, icon_name):
        """Kartlar için standart başlık ve ayırıcı ekler."""
        hc_layout = QVBoxLayout()
        hc_layout.setContentsMargins(0, 0, 0, 0)
        hc_layout.setSpacing(12)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)
        
        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon(icon_name, color=OBISColors.PRIMARY).pixmap(QSize(22, 22)))
        
        label = self._create_label(text, OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY)
        label.setStyleSheet(label.styleSheet() + " letter-spacing: 1px;")
        
        h_layout.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        h_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignVCenter)
        h_layout.addStretch()
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(0, 0, 0, 0.03); height: 1px; border: none; margin: 0px;")
        
        hc_layout.addLayout(h_layout)
        hc_layout.addWidget(line)
        layout.addLayout(hc_layout)

    # ================= BÖLÜMLER =================

    def _create_header(self) -> QWidget:
        header_widget = QWidget()
        h_layout = QHBoxLayout(header_widget)
        h_layout.setContentsMargins(0, 0, 0, 0) 
        
        t_layout = QVBoxLayout()
        t_layout.setSpacing(2)
        t_layout.addWidget(self._create_label("Uygulama Ayarları", OBISFonts.get_font(16, "bold"), OBISColors.TEXT_PRIMARY))
        t_layout.addWidget(self._create_label("Sistemin işleyişini ve bildirim tercihlerini özelleştirin.", OBISFonts.get_font(10, "normal"), OBISColors.TEXT_SECONDARY))
        
        icon_lbl = self._create_icon_box("fa5s.cog", OBISColors.TEXT_SECONDARY, border_color=OBISColors.BORDER)
        
        h_layout.addLayout(t_layout)
        h_layout.addStretch()
        h_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        return header_widget

    def _create_body(self) -> QWidget:
        body_widget = QWidget()
        b_layout = QVBoxLayout(body_widget)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(16) 
        
        b_layout.addWidget(self._create_automation_card())
        b_layout.addWidget(self._create_notification_card())
        b_layout.addWidget(self._create_advanced_card())
        b_layout.addStretch()
        return body_widget

    def _create_footer(self) -> QWidget:
        footer = QWidget()
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(0, 16, 0, 0)
        
        self.btn_save = OBISButton("Ayarları Kaydet", "success", icon=qta.icon("fa5s.save", color=OBISColors.TEXT_WHITE))
        self.btn_save.setFixedWidth(200)
        self.btn_save.clicked.connect(self.save_settings)
        
        f_layout.addStretch()
        f_layout.addWidget(self.btn_save)
        
        return footer

    def _create_automation_card(self) -> OBISCard:
        card = OBISCard(has_shadow=False)
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        c_layout.setSpacing(16)
        
        self._add_section_header(c_layout, "OTOMASYON AYARLARI", "fa5s.cog")
        
        time_box = QFrame()
        time_box.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1px solid {OBISColors.BORDER}; border-radius: {OBISDimens.RADIUS_MEDIUM}px; }}")
        tb_layout = QHBoxLayout(time_box)
        tb_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_layout = QVBoxLayout()
        lbl_layout.setSpacing(4)
        lbl_layout.addWidget(self._create_label("Kontrol Süresi", OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY))
        lbl_layout.addWidget(self._create_label("Sistemin notları ne sıklıkla kontrol edeceğini belirler.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_SECONDARY, False))
        lbl_layout.addStretch()
        
        self.combo_interval = OBISCombobox(items=["15 Dakika", "20 Dakika", "30 Dakika", "60 Dakika"], height=42)
        self.combo_interval.set_left_icon("fa5s.clock", OBISColors.TEXT_SECONDARY)
        self.combo_interval.setFixedWidth(160)
        
        tb_layout.addLayout(lbl_layout)
        tb_layout.addStretch()
        tb_layout.addWidget(self.combo_interval, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # --- AKTİF DÖNEM (SEMESTER) ---
        semester_box = QFrame()
        semester_box.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1px solid {OBISColors.BORDER}; border-radius: {OBISDimens.RADIUS_MEDIUM}px; }}")
        sb_layout = QVBoxLayout(semester_box)
        sb_layout.setContentsMargins(16, 16, 16, 16)
        sb_layout.setSpacing(16)
        
        # Switch Row (Dönemi Otomatik Belirle)
        sb_top = QHBoxLayout()
        sb_top.setContentsMargins(0, 0, 0, 0)
        
        sb_texts = QVBoxLayout()
        sb_texts.setSpacing(2)
        sb_texts.addWidget(self._create_label("Aktif Dönemi Otomatik Belirle", OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY))
        sb_texts.addWidget(self._create_label("İçinde bulunulan dönemi sistem otomatik hesaplar.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_SECONDARY, False))
        sb_texts.addStretch()
        
        self.sw_auto_semester = OBISSwitch(width=44, height=24)
        self.sw_auto_semester.toggled.connect(self._toggle_semester_mode)
        
        sb_top.addLayout(sb_texts)
        sb_top.addStretch()
        sb_top.addWidget(self.sw_auto_semester, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # ComboBox Row (Manuel Seçim)
        self.combo_semester = OBISCombobox(items=[], height=42)
        self.combo_semester.set_left_icon("fa5s.calendar-alt", OBISColors.TEXT_SECONDARY)
        
        sb_layout.addLayout(sb_top)
        sb_layout.addWidget(self.combo_semester)
        
        c_layout.addWidget(time_box)
        c_layout.addWidget(semester_box)
        card.layout.addLayout(c_layout)
        return card

    def _create_notification_card(self) -> OBISCard:
        card = OBISCard(has_shadow=False)
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        c_layout.setSpacing(16)
        
        self._add_section_header(c_layout, "BİLDİRİM KANALLARI", "fa5s.bell")
        
        mail_box = QFrame()
        mail_box.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1px solid rgba(0,0,0,0.05); border-radius: {OBISDimens.RADIUS_MEDIUM}px; }}")
        mb_layout = QVBoxLayout(mail_box)
        mb_layout.setContentsMargins(16, 16, 16, 16)
        mb_layout.setSpacing(16)
        
        mail_row = QHBoxLayout()
        mail_row.setContentsMargins(0,0,0,0)
        
        icon_box = self._create_icon_box("fa5s.envelope", OBISColors.PURPLE, OBISColors.PURPLE_BG, 20, 40)
        
        m_texts = QVBoxLayout()
        m_texts.setSpacing(2)
        m_texts.addWidget(self._create_label("E-posta Bildirimleri", OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY))
        m_texts.addWidget(self._create_label("Not değişimi olduğunda e-posta al.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_SECONDARY, False))
        
        self.sw_mail = OBISSwitch(width=44, height=24)
        self.sw_mail.toggled.connect(self._toggle_gmail_settings)
        
        mail_row.addWidget(icon_box)
        mail_row.addSpacing(0)
        mail_row.addLayout(m_texts)
        mail_row.addStretch()
        mail_row.addWidget(self.sw_mail, alignment=Qt.AlignmentFlag.AlignVCenter)
        mb_layout.addLayout(mail_row)
        
        self.gmail_container = QWidget()
        self.gmail_container.setStyleSheet("background: transparent; border: none;")
        g_layout = QVBoxLayout(self.gmail_container)
        g_layout.setContentsMargins(0, 0, 0, 0)
        g_layout.setSpacing(16)
        
        info_alert = QFrame()
        info_alert.setStyleSheet(f"QFrame {{ background-color: {OBISColors.HOVER_BLUE}; border: 1px solid #dbeafe; border-radius: {OBISDimens.RADIUS_SMALL}px; }}")
        ia_layout = QHBoxLayout(info_alert)
        ia_layout.setContentsMargins(12, 12, 12, 12)
        
        info_icon = QLabel()
        info_icon.setPixmap(qta.icon("fa5s.info-circle", color=OBISColors.INFO).pixmap(QSize(16, 16)))
        info_icon.setStyleSheet("border: none; background: transparent;")
        
        info_lbl = self._create_label("Gmail üzerinden bildirim göndermek için <b style='color:#3B82F6'>2 Adımlı Doğrulama</b> açık olmalı ve bir <b style='color:#3B82F6'>Uygulama Şifresi</b> tanımlanmalıdır.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_PRIMARY, True)
        
        ia_layout.addWidget(info_icon, alignment=Qt.AlignmentFlag.AlignTop)
        ia_layout.addSpacing(10)
        ia_layout.addWidget(info_lbl, stretch=1)
        g_layout.addWidget(info_alert)
        
        input_grid = QGridLayout()
        input_grid.setSpacing(16)
        
        self.inp_gmail = OBISInput(placeholder="example@gmail.com", icon_name="fa5b.google")
        self.inp_gmail.setStyleSheet(self.inp_gmail.styleSheet().replace(OBISColors.INPUT_BG, OBISColors.SURFACE))
        self.inp_app_pass = OBISInput(placeholder="**** **** **** ****", icon_name="fa5s.key", is_password=True)
        self.inp_app_pass.setStyleSheet(self.inp_app_pass.styleSheet().replace(OBISColors.INPUT_BG, OBISColors.SURFACE))
        
        input_grid.addWidget(self._create_label("GÖNDERİCİ GMAIL ADRESİ", OBISFonts.get_font(8, "bold"), OBISColors.TEXT_SECONDARY), 0, 0)
        input_grid.addWidget(self.inp_gmail, 1, 0)
        input_grid.addWidget(self._create_label("GMAIL UYGULAMA ŞİFRESİ", OBISFonts.get_font(8, "bold"), OBISColors.TEXT_SECONDARY), 0, 1)
        input_grid.addWidget(self.inp_app_pass, 1, 1)
        g_layout.addLayout(input_grid)
        
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(12)
        action_row.addStretch()
        
        self.btn_2fa = OBISButton("2 Adımlı Doğrulamayı Aç", "outline", icon=qta.icon("fa5s.shield-alt", color=OBISColors.WARNING))
        self.btn_2fa.setFixedHeight(32)
        self.btn_2fa.setFont(OBISFonts.get_font(9, "medium"))
        self.btn_2fa.setStyleSheet(f"QPushButton {{ color: {OBISColors.WARNING}; border: 1px solid {OBISColors.WARNING}; border-radius: {OBISDimens.RADIUS_SMALL}px; background-color: transparent; padding: 0 16px; }} QPushButton:hover {{ background-color: {OBISColors.WARNING_BG}; }}")
        self.btn_2fa.clicked.connect(lambda: webbrowser.open("https://myaccount.google.com/signinoptions/two-step-verification"))
        
        btn_pass = OBISButton("Uygulama Şifresi Al", "outline", icon=qta.icon("fa5s.external-link-alt", color=OBISColors.PURPLE))
        btn_pass.setFixedHeight(32)
        btn_pass.setFont(OBISFonts.get_font(9, "medium"))
        btn_pass.setStyleSheet(f"QPushButton {{ color: {OBISColors.PURPLE}; border: 1px solid {OBISColors.PURPLE}; border-radius: {OBISDimens.RADIUS_SMALL}px; background-color: {OBISColors.SURFACE}; padding: 0 16px; }} QPushButton:hover {{ background-color: {OBISColors.PURPLE_BG}; }}")
        btn_pass.clicked.connect(lambda: webbrowser.open("https://myaccount.google.com/apppasswords"))
        
        action_row.addWidget(self.btn_2fa)
        action_row.addWidget(btn_pass)
        g_layout.addLayout(action_row)
        
        mb_layout.addWidget(self.gmail_container)
        c_layout.addWidget(mail_box)
        card.layout.addLayout(c_layout)
        return card

    def _create_advanced_card(self) -> OBISCard:
        card = OBISCard(has_shadow=False)
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        c_layout.setSpacing(16)
        
        self._add_section_header(c_layout, "GELİŞMİŞ AYARLAR", "fa5s.sliders-h")
        
        adv_grid = QGridLayout()
        adv_grid.setContentsMargins(0, 0, 0, 0)
        adv_grid.setSpacing(32) 
        adv_grid.setColumnStretch(0, 1)
        adv_grid.setColumnStretch(1, 1)
        
        # Sol Kolon
        col_left = QVBoxLayout()
        col_left.setContentsMargins(0,0,0,0)
        col_left.setSpacing(12)
        
        col_left.addWidget(self._create_label("TARAYICI MOTOR SEÇİMİ", OBISFonts.get_font(8, "bold"), OBISColors.TEXT_SECONDARY))
        
        br_row = QHBoxLayout()
        br_row.setContentsMargins(0, 0, 0, 0)
        br_row.setSpacing(12)
        
        self.btn_chrom = self._create_browser_btn("Chromium", "Hızlı & Kararlı", True)
        self.btn_ff = self._create_browser_btn("Firefox", "Hafif Bellek", False)
        
        self.btn_chrom.clicked.connect(lambda: self._set_browser("chromium"))
        self.btn_ff.clicked.connect(lambda: self._set_browser("firefox"))
        
        br_row.addWidget(self.btn_chrom)
        br_row.addWidget(self.btn_ff)
        col_left.addLayout(br_row)
        col_left.addWidget(self._create_label("Not: Otomasyonun web sayfalarını render etmek için kullanacağı motoru belirler.", OBISFonts.get_font(8, "italic"), OBISColors.TEXT_SECONDARY, True))
        
        sep_l = QFrame()
        sep_l.setFrameShape(QFrame.Shape.HLine)
        sep_l.setStyleSheet("background-color: rgba(0, 0, 0, 0.03); height: 1px; border: none; margin: 16px 0;")
        col_left.addWidget(sep_l)
        
        warn_box = QFrame()
        warn_box.setStyleSheet(f"QFrame {{ background-color: #fff7ed; border-radius: {OBISDimens.RADIUS_SMALL}px; }}")
        wb_layout = QVBoxLayout(warn_box)
        wb_layout.setContentsMargins(12, 12, 12, 12)
        wb_layout.addWidget(self._create_label("Gelişmiş ayarlar sistem stabilitesini etkileyebilir. Değiştirirken lütfen dikkatli olun.", OBISFonts.get_font(9, "normal"), "#C2410C", True))
        
        col_left.addWidget(warn_box)
        col_left.addStretch()
        
        # Sağ Kolon
        col_right = QVBoxLayout()
        col_right.setContentsMargins(0,0,0,0)
        col_right.setSpacing(16)
        
        self.sw_autostart = self._create_switch_row("Windows Başlangıcında Başlat", "Bilgisayar açıldığında uygulamayı otomatik başlatır.")
        self.sw_minimize = self._create_switch_row("Simge Durumunda Çalıştır", "Pencere kapatıldığında sistem tepsisinde çalışmaya devam eder.")
        self.sw_stop_fail = self._create_switch_row("3 Başarısız Girişte Durdur", "Giriş denemeleri 3 kez başarısız olursa sistemi durdurur.")
        
        col_right.addLayout(self.sw_minimize)
        col_right.addLayout(self.sw_autostart)
        col_right.addLayout(self.sw_stop_fail)
        col_right.addStretch()
        
        adv_grid.addLayout(col_left, 0, 0)
        adv_grid.addLayout(col_right, 0, 1)
        c_layout.addLayout(adv_grid)
        card.layout.addLayout(c_layout)
        return card

    # ================= BROWSER SEÇİCİ & SWITCH YARDIMCILARI =================

    def _create_browser_btn(self, title, desc, active):
        btn = QPushButton()
        btn.setFixedHeight(56)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(btn)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 8, 10, 8)
        
        t_lbl = QLabel(title)
        t_lbl.setFont(OBISFonts.get_font(10, "bold"))
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        d_lbl = QLabel(desc)
        d_lbl.setFont(OBISFonts.get_font(8, "normal"))
        d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(t_lbl)
        layout.addWidget(d_lbl)
        
        self._update_browser_btn_style(btn, active, override_childs=(t_lbl, d_lbl))
        return btn

    def _set_browser(self, name):
        self.selected_browser = name
        is_chrom = name == "chromium"
        self._update_browser_btn_style(self.btn_chrom, is_chrom)
        self._update_browser_btn_style(self.btn_ff, not is_chrom)

    def _update_browser_btn_style(self, btn, is_active, override_childs=None):
        rad_cmd = f"border-radius: {OBISDimens.RADIUS_MEDIUM}px;"
        
        bg_col = f"qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {OBISColors.HOVER_BLUE}, stop:1 {OBISColors.SURFACE})" if is_active else OBISColors.SURFACE
        border_col = OBISColors.PRIMARY if is_active else "rgba(0,0,0,0.08)"
        border_width = "2px" if is_active else "1px"
        hov_bg = OBISColors.HOVER_BLUE if is_active else OBISColors.BACKGROUND
        
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {bg_col}; border: {border_width} solid {border_col}; {rad_cmd} }}
            QPushButton:hover {{ background-color: {hov_bg}; border: {border_width} solid {OBISColors.PRIMARY if is_active else 'rgba(0,0,0,0.1)'}; }}
        """)
        
        title_col = OBISColors.PRIMARY if is_active else OBISColors.TEXT_PRIMARY
        desc_col = OBISColors.PRIMARY if is_active else OBISColors.TEXT_SECONDARY
        font_weight = "bold" if is_active else "normal"
        
        if override_childs:
            t_lbl, d_lbl = override_childs
        else:
            t_lbl, d_lbl = btn.findChildren(QLabel)[0:2]
            
        t_lbl.setStyleSheet(f"color: {title_col}; background: transparent; border: none; font-weight: {font_weight};")
        d_lbl.setStyleSheet(f"color: {desc_col}; background: transparent; border: none;")

    def _create_switch_row(self, title, desc, active_color=None):
        row = QHBoxLayout()
        texts = QVBoxLayout()
        texts.setSpacing(2)
        
        texts.addWidget(self._create_label(title, OBISFonts.BODY, OBISColors.TEXT_PRIMARY, True))
        texts.addWidget(self._create_label(desc, OBISFonts.SMALL, OBISColors.TEXT_SECONDARY, True))
        
        sw = OBISSwitch(width=36, height=20)
        sw.set_active_color(active_color or OBISColors.PRIMARY)
        
        row.addLayout(texts)
        row.addStretch()
        row.addWidget(sw)
        
        row.switch_widget = sw
        return row

    def _toggle_gmail_settings(self, checked):
        self.gmail_container.setVisible(checked)

    def _toggle_semester_mode(self, checked):
        """Otomatik dönem seçeneği değiştiğinde ComboBox'ı günceller."""
        if checked:
            # Otomatik Mod: Şuan ki dönemi göster, ve kitle
            current = get_current_semester()
            self.combo_semester.clear()
            self.combo_semester.addItems([f"{current} (Otomatik)"])
            self.combo_semester.setCurrentIndex(0)
            self.combo_semester.setEnabled(False)
        else:
            # Manuel Mod: Gelecek, Geçmiş Listesini Göster
            self.combo_semester.setEnabled(True)
            self.combo_semester.clear()
            items = generate_semester_list()
            self.combo_semester.addItems(items)
            
            # Eğer seçili bir değer varsa ona dön, yoksa currentı seç
            current = get_current_semester()
            if hasattr(self, "_temp_selected_semester") and self._temp_selected_semester in items:
                self.combo_semester.setCurrentText(self._temp_selected_semester)
            elif current in items:
               self.combo_semester.setCurrentText(current)

    # ================= VERİ YÜKLEME / KAYDETME =================
    
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                    interval = str(settings.get("check_interval", 20))
                    if interval not in ["15", "20", "30", "60"]: interval = "20"
                    self.combo_interval.setCurrentText(f"{interval} Dakika")
                    
                    methods = settings.get("notification_methods", ["email"])
                    self.sw_mail.setChecked("email" in methods)
                    self.inp_gmail.setText(settings.get("sender_email", ""))
                    self.inp_app_pass.setText(settings.get("gmail_app_password", ""))
                    self._toggle_gmail_settings("email" in methods)
                    
                    browser_name = settings.get("browser", "chromium")
                    if browser_name not in ["chromium", "firefox"]: browser_name = "chromium"
                    self._set_browser(browser_name)
                    
                    self.sw_minimize.switch_widget.setChecked(settings.get("minimize_to_tray", False))
                    self.sw_autostart.switch_widget.setChecked(settings.get("auto_start", False))
                    self.sw_stop_fail.switch_widget.setChecked(settings.get("stop_on_failures", True))
                    
                    # Aktif Dönem / Otomatik Belirleme
                    is_auto_semester = settings.get("auto_semester", True)
                    self._temp_selected_semester = settings.get("semester", get_current_semester())
                    
                    self.sw_auto_semester.setChecked(is_auto_semester)
                    # Sinyal zaten _toggle_semester_mode u tetikleyecek, 
                    # Eğet "true" tetiklendiyse problem yok. "false" tetiklendiğinde ve ilk yüklemede 
                    # items temizlenip tekrar ekleniyor bu nedenle manuel bir çağrıya da gerek kalmıyor.
                    
            except Exception as e:
                logging.error(f"Ayarlar yüklenemedi: {e}")
        else:
            self._toggle_gmail_settings(False)
            self.sw_auto_semester.setChecked(True) # Default Otomatik

    def save_settings(self):
        # Snackbar instance kontrolü
        if not hasattr(self, 'snackbar'):
            self.snackbar = OBISSnackbar(self.parent() or self)

        methods = []
        if self.sw_mail.isChecked(): methods.append("email")

        # E-posta açık ise zorunlu alan doğrulaması
        if "email" in methods:
            email = self.inp_gmail.text()
            pwd = self.inp_app_pass.text()
            if not email or "@" not in email:
                self.snackbar.show_message("Geçerli bir E-posta adresi giriniz.", OBISSnackbar.ERROR)
                return
            if not pwd:
                self.snackbar.show_message("Gmail uygulama şifresi zorunludur.", OBISSnackbar.ERROR)
                return

        try:
            current_settings = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    current_settings = json.load(f)
            
            # Seçili olan formattaki yazıyı sayı olarak böl
            save_interval = int(self.combo_interval.currentText().split()[0])
            
            # Semester
            is_auto_sem = self.sw_auto_semester.isChecked()
            # Otomatik değilse direkt combo içindeki düz metin, otomatikse varsayılan.
            saved_sem = get_current_semester() if is_auto_sem else self.combo_semester.currentText()
            
            # Güncellemesi gereken ayarlara ekliyoruz.
            current_settings.update({
                "check_interval": save_interval,
                "auto_semester": is_auto_sem,
                "semester": saved_sem,
                "notification_methods": methods,
                "sender_email": self.inp_gmail.text(),
                "gmail_app_password": self.inp_app_pass.text(),
                "browser": getattr(self, "selected_browser", "chromium"),
                "minimize_to_tray": self.sw_minimize.switch_widget.isChecked(),
                "auto_start": self.sw_autostart.switch_widget.isChecked(),
                "stop_on_failures": self.sw_stop_fail.switch_widget.isChecked()
            })
            
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(current_settings, f, indent=4)
                
            set_auto_start(self.sw_autostart.switch_widget.isChecked())
            
            # Başarı Bildirimi (Snackbar ile)
            self.snackbar.show_message("Ayarlar başarıyla kaydedildi.", OBISSnackbar.SUCCESS)
            
        except Exception as e:
            logging.error(f"Ayarlar kaydedilemedi: {e}")
            self.snackbar.show_message(f"Kaydetme hatası: {str(e)}", OBISSnackbar.ERROR)
