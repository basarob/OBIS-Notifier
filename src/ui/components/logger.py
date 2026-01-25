"""
BU DOSYA: Loglama işlemlerini arayüzde göstermek için gerekli altyapıyı sağlar.
.Thread-safe olması için Queue (Kuyruk) yapısı kullanır.
"""

import logging
import queue
import customtkinter as ctk

# Logları biriktireceğimiz kuyruk
log_queue: queue.Queue = queue.Queue()

class QueueHandler(logging.Handler):
    """
    Log kayıtlarını bir kuyruğa (Queue) gönderen özel logging handler.
    Bu sayede farklı threat'lerden gelen loglar güvenle ana thread'e taşınır.
    """
    def emit(self, record: logging.LogRecord) -> None:
        log_queue.put(self.format(record))

def setup_logging_to_queue() -> None:
    """Global logging yapılandırmasına QueueHandler ekler."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    queue_handler = QueueHandler()
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
    queue_handler.setFormatter(formatter)
    logger.addHandler(queue_handler)

def update_log_display(textbox: ctk.CTkTextbox, root: ctk.CTk) -> None:
    """
    Kuyruktaki logları okur ve UI üzerindeki Textbox'a yazar.
    Recursive olarak kendini çağırır (after metodu ile).
    
    Args:
        .textbox: Logların yazılacağı arayüz elemanı
        root: Ana pencere (after metodunu çağırmak için)
    """
    try:
        while True:
            # Kuyruktan veri al (Non-blocking)
            record = log_queue.get_nowait()
            textbox.configure(state="normal")
            textbox.insert("end", record + "\n")
            textbox.see("end") # En alta kaydır
            textbox.configure(state="disabled")
    except queue.Empty:
        pass
    
    # 100ms sonra tekrar kontrol et
    root.after(100, lambda: update_log_display(textbox, root))
