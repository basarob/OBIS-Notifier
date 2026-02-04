"""
BU DOSYA: Uygulama yapılandırma ayarlarının yönetildiği ekran.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QCheckBox, QComboBox
from PyQt6.QtCore import Qt, QSize
from ..components.card import OBISCard
from ..components.input import OBISInput
from ..components.button import OBISButton
from ..styles.theme import OBISColors, OBISFonts, OBISDimens
import qtawesome as qta

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        # 1. Giriş Bilgileri Kartı
        self._add_section_header("GİRİŞ BİLGİLERİ", "fa5s.lock")
        
        login_card = OBISCard()
        l_layout = QVBoxLayout()
        l_layout.setSpacing(15)
        
        # Row 1
        row1 = QHBoxLayout()
        
        # Öğrenci No
        grp_std = QVBoxLayout()
        lbl_std = QLabel("ÖĞRENCİ NUMARASI")
        lbl_std.setFont(OBISFonts.get_font(8, "bold"))
        lbl_std.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        self.inp_std = OBISInput(placeholder="201809999", icon_name="fa5s.user")
        grp_std.addWidget(lbl_std)
        grp_std.addWidget(self.inp_std)
        
        # Şifre
        grp_pwd = QVBoxLayout()
        lbl_pwd = QLabel("OBIS ŞİFRESİ")
        lbl_pwd.setFont(OBISFonts.get_font(8, "bold"))
        lbl_pwd.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        self.inp_pwd = OBISInput(placeholder="........", icon_name="fa5s.key", is_password=True)
        grp_pwd.addWidget(lbl_pwd)
        grp_pwd.addWidget(self.inp_pwd)
        
        row1.addLayout(grp_std)
        row1.addLayout(grp_pwd)
        
        l_layout.addLayout(row1)
        
        note = QLabel("Üniversite otomasyon sistemine giriş için kullanılır. Şifreniz yerel cihazınızda güvenle saklanır.")
        note.setFont(OBISFonts.SMALL)
        note.setStyleSheet(f"color: {OBISColors.TEXT_GHOST};")
        l_layout.addWidget(note)
        
        container = QWidget()
        container.setLayout(l_layout)
        login_card.add_widget(container)
        self.main_layout.addWidget(login_card)

        # 2. Otomasyon Ayarları
        self._add_section_header("OTOMASYON AYARLARI", "fa5s.cog")
        
        auto_card = OBISCard()
        a_layout = QVBoxLayout()
        a_layout.setSpacing(15)
        
        row2 = QHBoxLayout()
        
        # Dönem
        grp_term = QVBoxLayout()
        lbl_term = QLabel("KONTROL EDİLECEK YARIYIL")
        lbl_term.setFont(OBISFonts.get_font(8, "bold"))
        lbl_term.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        
        self.combo_term = QComboBox()
        self.combo_term.addItems(["2023-2024 Bahar Dönemi", "2024-2025 Güz Dönemi"])
        self.combo_term.setFixedHeight(45)
        self.combo_term.setStyleSheet(f"""
            QComboBox {{
                background-color: {OBISColors.INPUT_BG};
                border-radius: {OBISDimens.RADIUS_SMALL}px;
                padding-left: 15px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        grp_term.addWidget(lbl_term)
        grp_term.addWidget(self.combo_term)
        
        # Süre
        grp_time = QVBoxLayout()
        lbl_time = QLabel("KONTROL SÜRESİ (DAKİKA)")
        lbl_time.setFont(OBISFonts.get_font(8, "bold"))
        lbl_time.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        self.inp_time = OBISInput(placeholder="15", icon_name="fa5s.clock")
        grp_time.addWidget(lbl_time)
        grp_time.addWidget(self.inp_time)
        
        row2.addLayout(grp_term)
        row2.addLayout(grp_time)
        
        a_layout.addLayout(row2)
        
        container_auto = QWidget()
        container_auto.setLayout(a_layout)
        auto_card.add_widget(container_auto)
        self.main_layout.addWidget(auto_card)

        # 3. Bildirim Ayarları
        self._add_section_header("BİLDİRİM KANALLARI", "fa5s.bell")
        
        notif_card = OBISCard()
        n_layout = QVBoxLayout()
        
        # E-posta Switch (Mock)
        mail_row = QHBoxLayout()
        
        icon_bg = QLabel()
        icon_bg.setFixedSize(40, 40)
        icon_bg.setStyleSheet(f"background-color: {OBISColors.HOVER_BLUE}; border-radius: {OBISDimens.RADIUS_LARGE}px;")
        icon_bg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m_icon = qta.icon("fa5s.envelope", color=OBISColors.PRIMARY)
        icon_bg.setPixmap(m_icon.pixmap(QSize(20, 20)))
        
        m_texts = QVBoxLayout()
        m_title = QLabel("E-posta Bildirimleri")
        m_title.setFont(OBISFonts.get_font(10, "bold"))
        m_desc = QLabel("Not değişimi olduğunda e-posta al.")
        m_desc.setFont(OBISFonts.SMALL)
        m_desc.setStyleSheet(f"color: {OBISColors.TEXT_SECONDARY};")
        m_texts.addWidget(m_title)
        m_texts.addWidget(m_desc)
        
        # Switch (Checkbox style)
        self.sw_mail = QCheckBox()
        self.sw_mail.setCursor(Qt.CursorShape.PointingHandCursor)
        # Custom switch CSS could be added here
        
        mail_row.addWidget(icon_bg)
        mail_row.addSpacing(10)
        mail_row.addLayout(m_texts)
        mail_row.addStretch()
        mail_row.addWidget(self.sw_mail)
        
        n_layout.addLayout(mail_row)
        
        # Gmail Ayarları (Görünür/Gizli yapılabilir)
        gmail_box = QFrame()
        gmail_box.setStyleSheet(f"background-color: {OBISColors.INPUT_BG}; border-radius: {OBISDimens.RADIUS_SMALL}px; border: 1px solid {OBISColors.BORDER}; margin-top: 10px;")
        gl = QVBoxLayout(gmail_box)
        
        info = QLabel("Gmail üzerinden bildirim göndermek için 2 Adımlı Doğrulama açık olmalı.")
        info.setFont(OBISFonts.get_font(9))
        info.setStyleSheet(f"color: {OBISColors.PRIMARY};")
        
        g_row = QHBoxLayout()
        self.inp_gmail = OBISInput(placeholder="ornek@gmail.com", icon_name="fa5b.google")
        self.inp_app_pass = OBISInput(placeholder="Uygulama Şifresi", icon_name="fa5s.key", is_password=True)
        g_row.addWidget(self.inp_gmail)
        g_row.addWidget(self.inp_app_pass)
        
        gl.addWidget(info)
        gl.addLayout(g_row)
        
        n_layout.addWidget(gmail_box)
        
        container_notif = QWidget()
        container_notif.setLayout(n_layout)
        notif_card.add_widget(container_notif)
        self.main_layout.addWidget(notif_card)
        
        # Save Button
        self.btn_save = OBISButton("Ayarları Kaydet", "primary", icon=qta.icon("fa5s.save", color="white"))
        self.main_layout.addWidget(self.btn_save)
        
        self.main_layout.addStretch()

    def _add_section_header(self, text, icon_name):
        layout = QHBoxLayout()
        icon = qta.icon(icon_name, color=OBISColors.PRIMARY)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(icon.pixmap(QSize(16, 16)))
        
        label = QLabel(text)
        label.setFont(OBISFonts.get_font(9, "bold"))
        label.setStyleSheet(f"color: {OBISColors.TEXT_PRIMARY}; letter-spacing: 1px;")
        
        layout.addWidget(lbl_icon)
        layout.addWidget(label)
        layout.addStretch()
        
        self.main_layout.addLayout(layout)