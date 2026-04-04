"""
BU DOSYA: İşletim sistemi ile ilgili yardımcı fonksiyonları barındırır.
Dosya yolları (path handling) ve AppData klasör yönetimi bu modüldedir.
"""

import os
import logging

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
        logging.info(f"Kullanıcı veri dizini oluşturuldu: {data_dir}")
    return data_dir

