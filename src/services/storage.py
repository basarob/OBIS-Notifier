"""
BU DOSYA: Not verilerinin JSON formatında dosyaya kaydedilmesi ve okunmasından sorumludur.
Data Persistence (Veri Kalıcılığı) katmanıdır.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class GradeStorageService:
    """Notları dosyaya (JSON) kaydeder ve okur."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_previous_grades(self) -> Optional[Dict[str, Any]]:
        """
        Daha önce kaydedilmiş notları dosyadan okur.
        Dosya yoksa veya bozuksa None döner ve hatayı loglar.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Önceki notlar yüklenemedi: {str(e)}")
                return None
        return None
    
    def save_grades(self, grades: List[Dict[str, str]]) -> bool:
        """
        Mevcut notları timestamp (zaman damgası) ile dosyaya kaydeder.
        
        Args:
            grades: Kaydedilecek not listesi
        """
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "grades": grades
            }
            # ensure_ascii=False -> Türkçe karakterlerin bozulmamasını sağlar
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info("Notlar başarıyla dosyaya kaydedildi.")
            return True
        except Exception as e:
            logging.error(f"Notlar kaydedilemedi: {str(e)}")
            return False
