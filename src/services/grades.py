"""
BU DOSYA: HTML içeriğini analiz ederek (parsing) notları ayıklar ve
eski notlarla karşılaştırarak değişiklikleri tespit eder.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from bs4 import BeautifulSoup
from ..config import OBISSelectors

class GradeService:
    """HTML Parsing ve Not Karşılaştırma işlemlerini yürütür."""

    def parse_grades(self, html_content: str) -> Optional[List[Dict[str, str]]]:
        """
        HTML içeriğinden not tablosunu bulup verileri çeker.
        BeautifulSoup kütüphanesi kullanılır.
        """
        logging.info("HTML ayrıştırılıyor...")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # .Tablo ID'sini config'den al
            table = soup.find("table", {"id": OBISSelectors.GRADES_TABLE_ID})

            if not table:
                logging.error("HTML içinde not tablosu bulunamadı!")
                return None
            
            tbody = table.find("tbody") # .type: ignore
            if not tbody:
                 return None

            rows = tbody.find_all("tr")
            if not rows:
                return None
            
            grades = []
            for row in rows:
                cells = row.find_all("td")
                # Beklenen hücre sayısı en az 5 olmalı
                if len(cells) > 4:
                    ders = cells[0].get_text(strip=True)
                    sinavlar = cells[1].get_text(strip=True)
                    harf_notu = cells[2].get_text(strip=True)
                    sonuc = cells[4].get_text(strip=True)
                    
                    grades.append({
                        "Ders Adı": ders,
                        "Sınavlar": sinavlar,
                        "Harf Notu": harf_notu,
                        "Sonuç": sonuc
                    })
        
            return grades
            
        except Exception as e:
            logging.error(f"Notlar ayrıştırılırken hata: {str(e)}")
            return None

    def compare_grades(self, 
                       old_data: Optional[Dict[str, Any]], 
                       new_grades: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], str]:
        """
        Eski ve yeni not listelerini karşılaştırarak farkları bulur.
        
        Returns:
            (Değişiklik Listesi, Durum Mesajı)
        """
        if not old_data or "grades" not in old_data:
            # İlk kez çalışıyorsa veya eski veri yoksa hepsi "yeni" sayılır
            changes = []
            for grade in new_grades:
                changes.append({
                "ders": grade["Ders Adı"],
                "eski": None,
                "yeni": grade
            })
            return changes, "İlk kontrol (Tüm veriler yeni)"
        
        old_grades_list = old_data["grades"]
        
        # Karşılaştırma kolaylığı için listeyi dict'e çeviriyoruz (Anahtar: Ders Adı)
        old_dict = {grade["Ders Adı"]: grade for grade in old_grades_list}
        new_dict = {grade["Ders Adı"]: grade for grade in new_grades}
        
        changes = []
        
        for ders_adi, new_grade in new_dict.items():
            if ders_adi in old_dict:
                old_grade = old_dict[ders_adi]
                # İçerik değişikliği kontrolü
                if (old_grade["Sınavlar"] != new_grade["Sınavlar"] or 
                    old_grade["Harf Notu"] != new_grade["Harf Notu"] or 
                    old_grade["Sonuç"] != new_grade["Sonuç"]):
                    
                    changes.append({
                        "ders": ders_adi,
                        "eski": old_grade,
                        "yeni": new_grade
                    })
            else:
                # Yeni bir ders eklenmişse
                changes.append({
                    "ders": ders_adi,
                    "eski": None,
                    "yeni": new_grade
                })
        
        return changes, "Değişiklik bulundu" if changes else "Değişiklik yok"
