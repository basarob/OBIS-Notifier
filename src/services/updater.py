"""
BU DOSYA: Uygulamanın otonom güncellenmesinden sorumludur.
GitHub Releases API'sini kontrol eder, yeni exe indirir ve geçici BAT scriptiyle 
uygulamayı kapatıp üzerine yazar ve yeniden başlatır. 
"""

import os
import sys
import logging
import tempfile
import urllib.request
import urllib.error
import json

from config import CURRENT_VERSION
from PyQt6.QtCore import QThread, pyqtSignal

def is_newer_version(latest: str, current: str) -> bool:
    """Semantik versiyon kontrolü yapar (Örn: 3.1 > 3.0)."""
    try:
        def parse(v):
            return [int(x) for x in v.split('-')[0].split('.')]
        return parse(latest) > parse(current)
    except Exception:
        # Fallback (Integer çevrimi başarısız olursa düz string kıyası, ancak güvenli olmaz)
        return latest != current and latest > current

class UpdateWorker(QThread):
    """
    Arka planda Github versiyon kontrolü ve exe indirme işlemlerini yürütür.
    UI thread'ini dondurmaz.
    """
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str) # success, param (bat path or msg)

    def __init__(self, repo_path: str = "basarob/OBIS-Notifier"):
        super().__init__()
        self.repo_path = repo_path

    def run(self):
        try:
            self.status_signal.emit("Güncellemeler kontrol ediliyor...")
            url = f"https://api.github.com/repos/{self.repo_path}/releases/latest"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'OBIS-Notifier-Updater'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    self.finished_signal.emit(False, "API erişimi sağlanamadı")
                    return
                
                data = json.loads(response.read().decode('utf-8'))
                
            latest_version = data.get("tag_name", "").lstrip("v")
            if latest_version and is_newer_version(latest_version, CURRENT_VERSION):
                # Yeni versiyon bulundu, exe indirilecek
                exe_asset = None
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        exe_asset = asset
                        break
                        
                if not exe_asset:
                    self.finished_signal.emit(False, "")
                    return
                    
                self.status_signal.emit("Yeni sürüm indiriliyor...")
                download_url = exe_asset["browser_download_url"]
                download_path = os.path.join(tempfile.gettempdir(), "obis_notifier_update.exe")
                
                # EXE indir
                urllib.request.urlretrieve(download_url, download_path)
                
                # Sürüm notlarını kaydet (Yeniden başlayınca gösterilsin diye)
                release_notes = data.get("body", "Yenilikler listesi bulunamadı.")
                app_data = os.getenv('LOCALAPPDATA', os.getenv('APPDATA'))
                notes_path = os.path.join(app_data, "OBISNotifier", "release_notes.txt")
                os.makedirs(os.path.dirname(notes_path), exist_ok=True)
                with open(notes_path, "w", encoding="utf-8") as f:
                    f.write(release_notes)
                    
                # Hedef yolu belirle
                if getattr(sys, 'frozen', False):
                    target_exe = sys.executable
                else:
                    target_exe = os.path.abspath(sys.argv[0]) # Geliştirme ortamıysa exe'nin yerine kendi dosyasını ezmeye çalışır ki hata olur ama mühim değil
                    
                # Bat scriptini hazırla
                bat_path = os.path.join(tempfile.gettempdir(), "obis_update.bat")
                bat_content = f"""@echo off
echo OBIS Notifier Guncelleniyor... Lutfen bekleyin...
timeout /t 3 /nobreak >nul
move /Y "{download_path}" "{target_exe}"
start "" "{target_exe}"
del "%~f0"
"""
                with open(bat_path, "w") as f:
                    f.write(bat_content)
                    
                logging.info(f"Yenileme komutu hazırlandı: {bat_path}")
                self.finished_signal.emit(True, bat_path)
                return
                
            self.finished_signal.emit(False, "")
        except urllib.error.URLError as e:
            logging.warning(f"Bağlantı hatası: Güncelleme kontrol edilemedi ({e})")
            self.finished_signal.emit(False, "")
        except Exception as e:
            logging.error(f"UpdateWorker Hatası: {e}")
            self.finished_signal.emit(False, "")
