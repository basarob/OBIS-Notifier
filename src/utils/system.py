"""
BU DOSYA: İşletim sistemi ile ilgili yardımcı fonksiyonları barındırır.
Dosya yolları (path handling), otomatik başlatma ve
AppData klasör yönetimi bu modüldedir.
"""

import os
import sys
import logging
import subprocess

def get_user_data_dir() -> str:
    """
    Kullanıcı veri dizinini (AppData/Local/OBISNotifier) döndürür.
    Eğer klasör yoksa oluşturur.
    """
    # Windows'ta LOCALAPPDATA environment variable'ını okur
    app_data = os.getenv('LOCALAPPDATA')
    if not app_data:
        app_data = os.getenv('APPDATA') # Fallback (Yedek plan)
        
    data_dir = os.path.join(app_data, "OBISNotifier")
    
    # Klasör yoksa yarat (ensure directory exists)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def set_auto_start(enable: bool = True) -> bool:
    """
    Windows başlangıç klasörüne kısayol oluşturarak uygulamanın otomatik başlamasını sağlar.
    
    Args:
        enable: True ise kısayol oluşturur, False ise siler.
    """
    try:
        # Windows Startup klasörü yolu
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_folder, "OBIS Notifier.lnk")
        
        if enable:
            if os.path.exists(shortcut_path):
                return True # Zaten varsa işlem yapma

            target = sys.executable
            cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
            arguments = ""
            
            # Uygulamanın script mi yoksa compiled EXE mi olduğunu kontrol et (frozen attribute)
            if not getattr(sys, 'frozen', False):
                # Script ise python.exe script.py şeklinde çalıştır
                script_path = os.path.abspath(sys.argv[0])
                arguments = f'"{script_path}"'
            else:
                # EXE ise direkt çalıştır
                target = sys.executable
                cwd = os.path.dirname(target)
            
            # İkon yolunu belirle
            icon_path = ""
            if getattr(sys, 'frozen', False):
                 icon_path = target
            else:
                 icon_candidate = os.path.join(cwd, "images", "icon.ico")
                 if os.path.exists(icon_candidate):
                     icon_path = icon_candidate

            # PowerShell komutu ile kısayol (.lnk) oluşturma
            ps_command = (
                f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{shortcut_path}");'
                f'$s.TargetPath="{target}";'
                f'$s.Arguments=\'{arguments}\';'
                f'$s.WorkingDirectory="{cwd}";'
                f'if("{icon_path}" -ne ""){{$s.IconLocation="{icon_path}"}};'
                f'$s.Save()'
            )
            
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            logging.info(f"Otomatik başlatma kısayolu oluşturuldu: {shortcut_path}")
            
        else:
            # Devre dışı bırakılıyorsa kısayolu sil
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                logging.info("Otomatik başlatma kısayolu silindi.")
        
        return True
    except Exception as e:
        logging.error(f"Otomatik başlatma ayarı yapılamadı: {e}")
        return False
