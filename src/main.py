"""
BU DOSYA: Uygulamanın Başlangıç Noktasıdır (Entry Point).
Sadece UI uygulamasını (App) başlatır.
"""

import sys
sys.dont_write_bytecode = True  # __pycache__ klasörünü oluşturmaz

import os
if getattr(sys, 'frozen', False):
     os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

import ctypes   # Windows AppID için
from ui.app import App  # Arayüzü import

def main():
    # Windows Taskbar ikonunun düzgün görünmesi için AppID set et
    try:
        myappid = 'OBIS.Notifier.v2.2'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
        
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
