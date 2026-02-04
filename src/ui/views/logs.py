"""
BU DOSYA: Uygulama loglarının anlık görüntülendiği ekran.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor
from ..styles.theme import OBISFonts, OBISColors, OBISDimens, OBISStyles
from ..components.card import OBISCard
from ..components.button import OBISButton
from ..components.input import OBISInput
from utils.logger_qt import qt_logger
import qtawesome as qta

class LogsView(QWidget):
    # Sinyal: (Message, Type)
    snackbar_signal = pyqtSignal(str, str)
    
    # Hafıza optimizasyonu için maksimum satır sayısı
    MAX_LOG_COUNT = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(15)
        
        # --- Page Header ---
        page_header = QHBoxLayout()
        
        # Arama Kutusu
        self.search_input = OBISInput("Log kayıtlarında ara...", icon_name="fa5s.search", height=40, bg_color="#FFFFFF")
        self.search_input.setFixedWidth(400) 
        self.search_input.line_edit.textChanged.connect(self._filter_logs)
        
        # .Temizle Butonu
        self.btn_clear = OBISButton("Logları Temizle", "outline", icon=qta.icon("fa5s.trash", color=OBISColors.TEXT_SECONDARY))
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {OBISColors.BORDER};
                color: {OBISColors.TEXT_SECONDARY};
                background-color: {OBISColors.SURFACE};
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                padding: 0 16px;
                font-family: 'Inter';
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {OBISColors.BACKGROUND};
                border-color: {OBISColors.PRIMARY};
            }}
        """)
        self.btn_clear.clicked.connect(self._clear_logs)
        
        page_header.addWidget(self.search_input) 
        page_header.addStretch() 
        page_header.addWidget(self.btn_clear)
        
        self.layout.addLayout(page_header)
        
        # --- Terminal Layout Container ---
        # Card bileşeni sadece dış çerçeve (shadow) görevi görecek.
        self.card = OBISCard(has_shadow=True)
        self.card.layout.setContentsMargins(0, 0, 0, 0)
        self.card.layout.setSpacing(0)
        
        # Ana Konteyner (Yuvarlak köşeleri maskelemek için)
        main_container = QWidget()
        main_container.setObjectName("MainContainer")
        # Köşeleri yuvarlat ve taşmaları gizle
        main_container.setStyleSheet(f"""
            #MainContainer {{
                border-radius: {OBISDimens.RADIUS_MEDIUM}px;
                background-color: transparent;
            }}
        """)
        
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. ÜST BÖLÜM (Header & Column Names) - #181b21
        top_section = QFrame()
        top_section.setObjectName("TopSection")
        top_section.setStyleSheet(f"""
            #TopSection {{
                background-color: {OBISColors.TERMINAL_HEADER};
                border-bottom: 1px solid {OBISColors.TERMINAL_BORDER};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
            }}
        """)
        top_layout = QVBoxLayout(top_section)
        top_layout.setContentsMargins(20, 15, 20, 0)
        top_layout.setSpacing(10)
        
        # 1.1 Başlık Satırı (System Debugger + Live Stream)
        title_row = QHBoxLayout()
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.terminal", color=OBISColors.TERMINAL_ICON).pixmap(16, 16))
        
        t_title = QLabel("SYSTEM DEBUGGER")
        t_title.setFont(OBISFonts.get_font(9, "bold"))
        t_title.setStyleSheet(f"color: {OBISColors.TERMINAL_ICON}; letter-spacing: 1px;")
        
        live_dot = QLabel("● LIVE STREAM")
        live_dot.setFont(OBISFonts.get_font(9, "bold"))
        live_dot.setStyleSheet(f"color: {OBISColors.SUCCESS};")
        
        # .Trafik Işıkları
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(5)
        for c in [OBISColors.DANGER, OBISColors.WARNING, OBISColors.SUCCESS]: 
            dot = QLabel()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background-color: {c}; border-radius: 5px;")
            dots_layout.addWidget(dot)

        title_row.addWidget(icon_lbl)
        title_row.addSpacing(8)
        title_row.addWidget(t_title)
        title_row.addStretch()
        title_row.addWidget(live_dot)
        title_row.addSpacing(15)
        title_row.addLayout(dots_layout)
        
        top_layout.addLayout(title_row)
        
        # 1.2 Ayırıcı Çizgi
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"background-color: {OBISColors.TERMINAL_BORDER}; border: none; max-height: 1px;")
        top_layout.addWidget(line)

        # 1.3 Özel Sütun İsimleri (Custom Columns)
        cols_layout = QHBoxLayout()
        cols_layout.setContentsMargins(0, 5, 0, 10)
        cols_layout.setSpacing(0) # Sütunlar arası boşluğu sıfırla (Header ile Table hizası için)
        
        # Sütun Başlıklarını Hizalamak
        
        col_time = QLabel("TIMESTAMP")
        col_time.setFixedWidth(80) 
        col_time.setFont(OBISFonts.get_font(9, "bold"))
        col_time.setStyleSheet(f"color: {OBISColors.TERMINAL_TEXT_HEADER}; padding-left: 2px;")
        
        col_level = QLabel("LEVEL")
        col_level.setFixedWidth(100)
        col_level.setFont(OBISFonts.get_font(9, "bold"))
        col_level.setStyleSheet(f"color: {OBISColors.TERMINAL_TEXT_HEADER}; padding-left: 28px;")
        
        col_msg = QLabel("MESSAGE")
        col_msg.setFont(OBISFonts.get_font(9, "bold"))
        col_msg.setStyleSheet(f"color: {OBISColors.TERMINAL_TEXT_HEADER}; padding-left: 2px;")
        
        cols_layout.addWidget(col_time)
        cols_layout.addWidget(col_level)
        cols_layout.addWidget(col_msg, 1)
        
        top_layout.addLayout(cols_layout)
        main_layout.addWidget(top_section)
        
        # 2. ALT BÖLÜM (Table Content) - #0f1115
        bottom_section = QFrame()
        bottom_section.setObjectName("BottomSection")
        bottom_section.setStyleSheet(f"""
            #BottomSection {{
                background-color: {OBISColors.TERMINAL_BODY};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(20, 0, 20, 15)
        
        # .Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        # Headerları gizle çünkü yukarıda özel yaptık
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setCornerButtonEnabled(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # .Tablo Stili
        self.table.setStyleSheet(OBISStyles.LOG_TABLE)
        
        # Sütun Genişliklerini Header İle Eşle
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed) 
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) 
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 100)
        
        bottom_layout.addWidget(self.table)
        main_layout.addWidget(bottom_section)
        
        # Kart içine ekle
        self.card.add_widget(main_container)
        self.layout.addWidget(self.card)
        
        # Sinyal Bağlantısı
        qt_logger.log_signal.connect(self.add_log_record)

    @pyqtSlot(str, str, str)
    def add_log_record(self, timestamp, level, message):
        """Yeni bir log satırı ekler."""
        # Hafıza Yönetimi: Çok fazla log birikirse en eskileri sil
        if self.table.rowCount() >= self.MAX_LOG_COUNT:
             self.table.removeRow(0)

        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 1. Timestamp
        item_time = QTableWidgetItem(timestamp)
        item_time.setForeground(QColor(OBISColors.TERMINAL_TEXT_HEADER))
        self.table.setItem(row, 0, item_time)
        
        # 2. Level Badge (QLabel ile Custom Widget)
        # QTableWidgetItem sadece metin ve arka plan rengi destekler, radius desteklemez.
        # Bu yüzden hücreye bir Widget (Container -> Label) koyuyoruz.
        
        badge_container = QWidget()
        badge_container.setStyleSheet("background-color: transparent;") # Container şeffaf olmalı
        badge_layout = QHBoxLayout(badge_container)
        badge_layout.setContentsMargins(5, 2, 5, 2) # Hücre içi boşluk
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_badge = QLabel(level)
        lbl_badge.setFont(OBISFonts.get_font(8, "bold"))
        lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_badge.setFixedHeight(20) # Sabit yükseklik
        
        # Renkleri Belirle
        color_map = {
            "INFO": (OBISColors.LOG_INFO, "rgba(59, 130, 246, 0.15)"),
            "WARNING": (OBISColors.LOG_WARN, "rgba(245, 158, 11, 0.15)"),
            "ERROR": (OBISColors.LOG_ERROR, "rgba(239, 68, 68, 0.15)"),
            "CRITICAL": (OBISColors.LOG_ERROR, "rgba(239, 68, 68, 0.15)"),
            "SUCCESS": (OBISColors.LOG_SUCCESS, "rgba(16, 185, 129, 0.15)"),
            "SYSTEM": (OBISColors.LOG_SYSTEM, "rgba(139, 92, 246, 0.15)")
        }
        
        fg, bg = color_map.get(level, (OBISColors.TERMINAL_TEXT_BODY, "transparent"))
        
        lbl_badge.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background-color: {bg};
                border-radius: 4px; /* Yuvarlak Köşe */
                padding: 0 8px;
            }}
        """)
        
        badge_layout.addWidget(lbl_badge)
        self.table.setCellWidget(row, 1, badge_container)
        
        # 3. Message
        item_msg = QTableWidgetItem(message)
        item_msg.setForeground(QColor(OBISColors.TERMINAL_MESSAGE))
        self.table.setItem(row, 2, item_msg)
        
        self.table.scrollToBottom()

    def _filter_logs(self, text):
        rows = self.table.rowCount()
        for i in range(rows):
            match = False
            for j in range(3):
                item = self.table.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def _clear_logs(self):
        self.table.setRowCount(0)
        self.snackbar_signal.emit("Log kayıtları başarıyla temizlendi.", "success")