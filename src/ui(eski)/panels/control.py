"""
BU DOSYA: Sağ taraftaki kontrol panelini (Başlat/Durdur, Loglar) içerir.
"""

import customtkinter as ctk
from typing import Callable, Any
from ..components.logger import update_log_display

class ControlPanel(ctk.CTkFrame):
    """Log görüntüleme ve sistemi başlatma/durdurma işlevlerini barındıran panel."""
    def __init__(self, parent: Any, start_stop_callback: Callable, check_updates_callback: Callable, version_text: str):
        super().__init__(parent, corner_radius=0)
        
        self.start_stop_callback = start_stop_callback
        self.check_updates_callback = check_updates_callback
        self.version_text = version_text
        
        self._init_widgets()

    def _init_widgets(self) -> None:
        """Widget'ları yerleştirir."""
        # Grid ayarları
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Başlat/Durdur Butonu
        self.btn_start_stop = ctk.CTkButton(
            self, 
            text="Sistemi Başlat", 
            command=self.start_stop_callback, 
            height=50, 
            font=("Arial", 18, "bold")
        )
        self.btn_start_stop.pack(padx=20, pady=20, fill="x")

        # 2. Log Başlığı
        ctk.CTkLabel(self, text="Sistem Logları:").pack(padx=20, anchor="w")

        # 3. Log Alanı (Textbox)
        self.log_text = ctk.CTkTextbox(self)
        self.log_text.pack(padx=20, pady=10, fill="both", expand=True)
        self.log_text.configure(state="disabled")

        # 4. Alt Bilgi (Son Kontrol)
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(padx=20, pady=(0, 5), fill="x", side="bottom")

        self.lbl_last_check = ctk.CTkLabel(self.info_frame, text="Son Kontrol: -", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_last_check.pack(side="right")

        # 5. Footer (Versiyon ve Güncelleme)
        self._create_footer()

    def _create_footer(self) -> None:
        """Footer'ı oluşturur."""
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=5)
        
        footer_container = ctk.CTkFrame(footer_frame, fg_color="transparent")
        footer_container.pack(side="top", anchor="center")

        # Versiyon
        self.footer_label = ctk.CTkLabel(footer_container, text=self.version_text, text_color="gray60", font=("Arial", 10))
        self.footer_label.pack(side="left", padx=(0, 5))
        
        # Güncelleme Butonu
        self.btn_check_updates = ctk.CTkButton(
            footer_container, 
            text="Güncellemeleri Kontrol Et", 
            width=120, 
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color="transparent", 
            border_width=1,
            text_color=("gray60", "gray40"),
            hover_color=("gray90", "gray20"),
            command=self.check_updates_callback
        )
        self.btn_check_updates.pack(side="left", padx=(5, 0))

    def update_button_state(self, is_running: bool) -> None:
        """Buton metnini ve rengini duruma gör günceller."""
        if is_running:
            self.btn_start_stop.configure(text="Sistemi Durdur", fg_color="red")
        else:
            self.btn_start_stop.configure(text="Sistemi Başlat", fg_color=["#3B8ED0", "#1F6AA5"])

    def set_update_btn_loading(self, loading: bool) -> None:
        """Güncelleme butonunun durumunu değiştirir."""
        if loading:
            self.btn_check_updates.configure(state="disabled", text="Kontrol ediliyor...")
        else:
            self.btn_check_updates.configure(state="normal", text="Güncellemeleri Kontrol Et")

    def update_last_check_label(self, text: str) -> None:
        """Son kontrol zamanını günceller."""
        self.lbl_last_check.configure(text=text)

    def start_log_stream(self, root_app: ctk.CTk) -> None:
        """Log akışını başlatır."""
        update_log_display(self.log_text, root_app)
