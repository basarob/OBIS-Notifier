"""
BU DOSYA: Kullanıcı arayüzünde fare ile bir öğenin üzerine gelindiğinde
görünen açıklama baloncuğunu (ToolTip) yönetir.
"""

import customtkinter as ctk
from typing import Any, Optional

class ToolTip:
    """
    Widget'lar için basit ToolTip sınıfı.
    Fare widget üzerindeyken küçük bir pencere açar.
    """
    def __init__(self, widget: ctk.CTkBaseClass, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[ctk.CTkToplevel] = None

        # Event binding (Olay bağlama)
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: Any = None) -> None:
        """ToolTip penceresini hesaplanan konumda gösterir."""
        if self.tooltip_window or not self.text:
            return
        
        # Widget'ın ekran konumunu al
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # Pencereyi oluştur (Kenarlıksız - Overrideredirect)
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            self.tooltip_window, 
            text=self.text, 
            fg_color="gray20", 
            corner_radius=5, 
            text_color="white", 
            padx=10, 
            pady=5
        )
        label.pack()

    def hide_tooltip(self, event: Any = None) -> None:
        """ToolTip penceresini yok eder."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
