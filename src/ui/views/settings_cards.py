"""
BU DOSYA: SettingsView (Ayarlar) ekranındaki kart bileşenlerini barındırır.
Sadece arayüz oluşturma ve iç veri tutma işlemleri yapılır.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from ..components.card import OBISCard
from ..components.input import OBISInput
from ..components.button import OBISButton
from ..components.switch import OBISSwitch
from ..components.combobox import OBISCombobox
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
from utils.date_utils import generate_semester_list, get_current_semester
import qtawesome as qta
import webbrowser

def create_label(text, font, color=None, word_wrap=False) -> QLabel:
    """Kartlar için standart etiket oluşturucu yardımcı fonksiyon."""
    lbl = QLabel(text)
    lbl.setFont(font)
    if color:
        lbl.setStyleSheet(f"color: {color}; border: none; background: transparent;")
    lbl.setWordWrap(word_wrap)
    return lbl

def create_icon_box(icon_name, icon_color, bg_color="transparent", size=18, box_size=36, border_color=None) -> QLabel:
    lbl = QLabel()
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedSize(box_size, box_size)
    b_css = f"border: 1px solid {border_color};" if border_color else "border: none;"
    lbl.setStyleSheet(f"background-color: {bg_color}; {b_css} border-radius: {OBISDimens.RADIUS_SMALL}px;")
    lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(QSize(size, size)))
    return lbl

def add_section_header(layout, text, icon_name):
    hc_layout = QVBoxLayout()
    hc_layout.setContentsMargins(0, 0, 0, 0)
    hc_layout.setSpacing(12)
    h_layout = QHBoxLayout()
    h_layout.setContentsMargins(0, 0, 0, 0)
    h_layout.setSpacing(8)
    lbl_icon = QLabel()
    lbl_icon.setPixmap(qta.icon(icon_name, color=OBISColors.PRIMARY).pixmap(QSize(22, 22)))
    label = create_label(text, OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY)
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


class SettingsAutomationCard(OBISCard):
    def __init__(self, parent=None):
        super().__init__(parent, has_shadow=False)
        self._setup_ui()

    def _setup_ui(self):
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        c_layout.setSpacing(16)
        add_section_header(c_layout, "OTOMASYON AYARLARI", "fa5s.cog")

        # Kontrol Süresi
        time_box = QFrame()
        time_box.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1px solid {OBISColors.BORDER}; border-radius: {OBISDimens.RADIUS_MEDIUM}px; }}")
        tb_layout = QHBoxLayout(time_box)
        tb_layout.setContentsMargins(16, 16, 16, 16)
        
        lbl_layout = QVBoxLayout()
        lbl_layout.setSpacing(4)
        lbl_layout.addWidget(create_label("Kontrol Süresi", OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY))
        lbl_layout.addWidget(create_label("Sistemin notları ne sıklıkla kontrol edeceğini belirler.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_SECONDARY, False))
        lbl_layout.addStretch()
        
        self.combo_interval = OBISCombobox(items=["15 Dakika", "20 Dakika", "30 Dakika", "60 Dakika"], height=42)
        self.combo_interval.set_left_icon("fa5s.clock", OBISColors.TEXT_SECONDARY)
        self.combo_interval.setFixedWidth(160)
        
        tb_layout.addLayout(lbl_layout)
        tb_layout.addStretch()
        tb_layout.addWidget(self.combo_interval, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Aktif Dönem
        semester_box = QFrame()
        semester_box.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1px solid {OBISColors.BORDER}; border-radius: {OBISDimens.RADIUS_MEDIUM}px; }}")
        sb_layout = QVBoxLayout(semester_box)
        sb_layout.setContentsMargins(16, 16, 16, 16)
        sb_layout.setSpacing(16)
        
        sb_top = QHBoxLayout()
        sb_top.setContentsMargins(0, 0, 0, 0)
        sb_texts = QVBoxLayout()
        sb_texts.setSpacing(2)
        sb_texts.addWidget(create_label("Aktif Dönemi Otomatik Belirle", OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY))
        sb_texts.addWidget(create_label("İçinde bulunulan dönemi sistem otomatik hesaplar.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_SECONDARY, False))
        sb_texts.addStretch()
        
        self.sw_auto_semester = OBISSwitch(width=44, height=24)
        self.sw_auto_semester.toggled.connect(self._toggle_semester_mode)
        
        sb_top.addLayout(sb_texts)
        sb_top.addStretch()
        sb_top.addWidget(self.sw_auto_semester, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_semester = OBISCombobox(items=[], height=42)
        self.combo_semester.set_left_icon("fa5s.calendar-alt", OBISColors.TEXT_SECONDARY)
        
        sb_layout.addLayout(sb_top)
        sb_layout.addWidget(self.combo_semester)
        
        c_layout.addWidget(time_box)
        c_layout.addWidget(semester_box)
        self.layout.addLayout(c_layout)

    def _toggle_semester_mode(self, checked):
        if checked:
            current = get_current_semester()
            self.combo_semester.clear()
            self.combo_semester.addItems([f"{current} (Otomatik)"])
            self.combo_semester.setCurrentIndex(0)
            self.combo_semester.setEnabled(False)
        else:
            self.combo_semester.setEnabled(True)
            self.combo_semester.clear()
            items = generate_semester_list()
            self.combo_semester.addItems(items)
            current = get_current_semester()
            if hasattr(self, "_temp_selected_semester") and self._temp_selected_semester in items:
                self.combo_semester.setCurrentText(self._temp_selected_semester)
            elif current in items:
                self.combo_semester.setCurrentText(current)

    def set_data(self, interval: int, is_auto: bool, target_semester: str):
        valid = ["15", "20", "30", "60"]
        val = str(interval) if str(interval) in valid else "20"
        self.combo_interval.setCurrentText(f"{val} Dakika")
        self._temp_selected_semester = target_semester
        self.sw_auto_semester.setChecked(is_auto)
        self._toggle_semester_mode(is_auto)

    def get_data(self):
        val = self.combo_interval.currentText().split()[0]
        return {
            "check_interval": int(val),
            "auto_semester": self.sw_auto_semester.isChecked(),
            "semester": get_current_semester() if self.sw_auto_semester.isChecked() else self.combo_semester.currentText()
        }

    def set_running_state(self, is_running: bool):
        self.combo_interval.setEnabled(not is_running)
        self.sw_auto_semester.setEnabled(not is_running)
        self.combo_semester.setEnabled(False if is_running else not self.sw_auto_semester.isChecked())


class SettingsNotificationCard(OBISCard):
    test_mail_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent, has_shadow=False)
        self._setup_ui()

    def _setup_ui(self):
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        c_layout.setSpacing(16)
        add_section_header(c_layout, "BİLDİRİM KANALLARI", "fa5s.bell")
        
        mail_box = QFrame()
        mail_box.setStyleSheet(f"QFrame {{ background-color: transparent; border: 1px solid rgba(0,0,0,0.05); border-radius: {OBISDimens.RADIUS_MEDIUM}px; }}")
        mb_layout = QVBoxLayout(mail_box)
        mb_layout.setContentsMargins(16, 16, 16, 16)
        mb_layout.setSpacing(16)
        
        mail_row = QHBoxLayout()
        mail_row.setContentsMargins(0, 0, 0, 0)
        
        icon_box = create_icon_box("fa5s.envelope", OBISColors.PURPLE, OBISColors.PURPLE_BG, 20, 40)
        m_texts = QVBoxLayout()
        m_texts.setSpacing(2)
        m_texts.addWidget(create_label("E-posta Bildirimleri", OBISFonts.get_font(10, "bold"), OBISColors.TEXT_PRIMARY))
        m_texts.addWidget(create_label("Not değişimi olduğunda e-posta al.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_SECONDARY, False))
        
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
        info_alert.setStyleSheet(f"QFrame {{ background-color: {OBISColors.HOVER_BLUE}; border: 1px solid {OBISColors.PRIMARY}; border-radius: {OBISDimens.RADIUS_SMALL}px; }}")
        ia_layout = QHBoxLayout(info_alert)
        ia_layout.setContentsMargins(12, 12, 12, 12)
        
        info_icon = QLabel()
        info_icon.setPixmap(qta.icon("fa5s.info-circle", color=OBISColors.INFO).pixmap(QSize(16, 16)))
        info_icon.setStyleSheet("border: none; background: transparent;")
        info_lbl = create_label(f"Gmail üzerinden bildirim göndermek için <b style='color:{OBISColors.PRIMARY}'>2 Adımlı Doğrulama</b> açık olmalı ve bir <b style='color:{OBISColors.PRIMARY}'>Uygulama Şifresi</b> tanımlanmalıdır.", OBISFonts.get_font(9, "normal"), OBISColors.TEXT_PRIMARY, True)
        
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
        
        input_grid.addWidget(create_label("GÖNDERİCİ GMAIL ADRESİ", OBISFonts.get_font(8, "bold"), OBISColors.TEXT_SECONDARY), 0, 0)
        input_grid.addWidget(self.inp_gmail, 1, 0)
        input_grid.addWidget(create_label("GMAIL UYGULAMA ŞİFRESİ", OBISFonts.get_font(8, "bold"), OBISColors.TEXT_SECONDARY), 0, 1)
        input_grid.addWidget(self.inp_app_pass, 1, 1)
        g_layout.addLayout(input_grid)
        
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(12)
        
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
        
        self.btn_test_mail = OBISButton("Bildirimi Test Et", "outline", icon=qta.icon("fa5s.paper-plane", color=OBISColors.TEXT_SECONDARY))
        self.btn_test_mail.setFixedHeight(32)
        self.btn_test_mail.setFont(OBISFonts.get_font(9, "medium"))
        self.btn_test_mail.setStyleSheet(f"QPushButton {{ color: {OBISColors.TEXT_SECONDARY}; border: 1px solid {OBISColors.BORDER}; border-radius: {OBISDimens.RADIUS_SMALL}px; background-color: {OBISColors.SURFACE}; padding: 0 16px; }} QPushButton:hover {{ background-color: {OBISColors.BACKGROUND}; }}")
        # Sinyali Emit Et
        self.btn_test_mail.clicked.connect(lambda: self.test_mail_requested.emit(self.inp_gmail.text().strip(), self.inp_app_pass.text().strip()))
        
        action_row.addWidget(self.btn_2fa)
        action_row.addWidget(btn_pass)
        action_row.addStretch()
        action_row.addWidget(self.btn_test_mail)
        g_layout.addLayout(action_row)
        
        mb_layout.addWidget(self.gmail_container)
        c_layout.addWidget(mail_box)
        self.layout.addLayout(c_layout)

    def _toggle_gmail_settings(self, checked):
        self.gmail_container.setVisible(checked)

    def set_data(self, is_enabled: bool, email: str, pwd: str):
        self.sw_mail.setChecked(is_enabled)
        self.inp_gmail.setText(email)
        self.inp_app_pass.setText(pwd)
        self._toggle_gmail_settings(is_enabled)

    def get_data(self):
        return {
            "email_enabled": self.sw_mail.isChecked(),
            "email_address": self.inp_gmail.text(),
            "email_pwd": self.inp_app_pass.text()
        }

    def set_running_state(self, is_running: bool):
        self.sw_mail.setEnabled(not is_running)
        self.inp_gmail.setEnabled(not is_running)
        self.inp_app_pass.setEnabled(not is_running)
        self.btn_test_mail.setEnabled(not is_running)
        self.btn_2fa.setEnabled(not is_running)


class SettingsAdvancedCard(OBISCard):
    def __init__(self, parent=None):
        super().__init__(parent, has_shadow=False)
        self._setup_ui()

    def _setup_ui(self):
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE, 
                                    OBISDimens.PADDING_LARGE, OBISDimens.PADDING_LARGE)
        c_layout.setSpacing(16)
        add_section_header(c_layout, "GELİŞMİŞ AYARLAR", "fa5s.sliders-h")
        
        adv_grid = QGridLayout()
        adv_grid.setContentsMargins(0, 0, 0, 0)
        adv_grid.setSpacing(32) 
        adv_grid.setColumnStretch(0, 1)
        adv_grid.setColumnStretch(1, 1)
        
        col_left = QVBoxLayout()
        col_left.setContentsMargins(0, 0, 0, 0)
        col_left.setSpacing(12)
        col_left.addWidget(create_label("TARAYICI MOTOR SEÇİMİ", OBISFonts.get_font(8, "bold"), OBISColors.TEXT_SECONDARY))
        
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
        col_left.addWidget(create_label("Not: Otomasyonun web sayfalarını render etmek için kullanacağı motoru belirler.", OBISFonts.get_font(8, "italic"), OBISColors.TEXT_SECONDARY, True))
        
        sep_l = QFrame()
        sep_l.setFrameShape(QFrame.Shape.HLine)
        sep_l.setStyleSheet(f"background-color: {OBISColors.BORDER}; height: 1px; border: none; margin: 16px 0;")
        col_left.addWidget(sep_l)
        
        warn_box = QFrame()
        warn_box.setStyleSheet(f"QFrame {{ background-color: {OBISColors.WARNING_BG}; border-radius: {OBISDimens.RADIUS_SMALL}px; }}")
        wb_layout = QVBoxLayout(warn_box)
        wb_layout.setContentsMargins(12, 12, 12, 12)
        wb_layout.addWidget(create_label("Gelişmiş ayarlar sistem stabilitesini etkileyebilir. Değiştirirken lütfen dikkatli olun.", OBISFonts.get_font(9, "normal"), OBISColors.WARNING, True))
        
        col_left.addWidget(warn_box)
        col_left.addStretch()
        
        col_right = QVBoxLayout()
        col_right.setContentsMargins(0, 0, 0, 0)
        col_right.setSpacing(16)
        
        self.sw_minimize = self._create_switch_row("Simge Durumunda Çalıştır", "Pencere kapatıldığında sistem tepsisinde çalışmaya devam eder.")
        
        col_right.addLayout(self.sw_minimize)
        col_right.addStretch()
        
        adv_grid.addLayout(col_left, 0, 0)
        adv_grid.addLayout(col_right, 0, 1)
        c_layout.addLayout(adv_grid)
        self.layout.addLayout(c_layout)

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
        is_chrom = (name == "chromium")
        self._update_browser_btn_style(self.btn_chrom, is_chrom)
        self._update_browser_btn_style(self.btn_ff, not is_chrom)

    def _update_browser_btn_style(self, btn, is_active, override_childs=None):
        rad_cmd = f"border-radius: {OBISDimens.RADIUS_MEDIUM}px;"
        bg_col = f"qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {OBISColors.HOVER_BLUE}, stop:1 {OBISColors.SURFACE})" if is_active else OBISColors.SURFACE
        border_col = OBISColors.PRIMARY if is_active else OBISColors.BORDER
        border_width = "2px" if is_active else "1px"
        hov_bg = OBISColors.HOVER_BLUE if is_active else OBISColors.BACKGROUND
        
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {bg_col}; border: {border_width} solid {border_col}; {rad_cmd} }}
            QPushButton:hover {{ background-color: {hov_bg}; border: {border_width} solid {OBISColors.PRIMARY if is_active else OBISColors.BORDER}; }}
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
        texts.addWidget(create_label(title, OBISFonts.BODY, OBISColors.TEXT_PRIMARY, True))
        texts.addWidget(create_label(desc, OBISFonts.SMALL, OBISColors.TEXT_SECONDARY, True))
        
        sw = OBISSwitch(width=36, height=20)
        sw.set_active_color(active_color or OBISColors.PRIMARY)
        
        row.addLayout(texts)
        row.addStretch()
        row.addWidget(sw)
        row.switch_widget = sw
        return row

    def set_data(self, browser: str, min_to_tray: bool):
        self._set_browser(browser if browser in ["chromium", "firefox"] else "chromium")
        self.sw_minimize.switch_widget.setChecked(min_to_tray)

    def get_data(self):
        return {
            "browser": getattr(self, "selected_browser", "chromium"),
            "minimize_to_tray": self.sw_minimize.switch_widget.isChecked()
        }

    def set_running_state(self, is_running: bool):
        self.btn_chrom.setEnabled(not is_running)
        self.btn_ff.setEnabled(not is_running)
        self.sw_minimize.switch_widget.setEnabled(not is_running)
