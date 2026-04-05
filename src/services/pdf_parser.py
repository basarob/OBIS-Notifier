import pdfplumber
import os
import logging
import re
from datetime import datetime

# Önceden derlenmiş regex pattern'ları (performans optimizasyonu)
_RE_STUDENT_INFO = re.compile(r"^(\d{9})\s+(.+?)\s+(\d)\s+(\d[.,]\d{2})\s+(.+)$")
_RE_AKTS = re.compile(r"^(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")
_RE_COURSE = re.compile(r"^([A-Za-zÇĞİÖŞÜçğıöşü]{2,5}\d{3})\s+(.+?)\s+(\d{2}/\d{2}\s+(?:Güz|Bahar|Hazırlık|Yaz))\s+([A-Z0-9]+)\s+(\d{1,2})$")
_RE_PROGRAM = re.compile(r"^(\d\.\s*Yarıyıl)\s+(.+?)\s+(\d{1,2})(?:\s+([A-Za-zÇĞİÖŞÜçğıöşü]{2,5}\d{3}.*))?$")
_RE_REMAINING = re.compile(r"^(.+?)\s+(\d{1,2})\s+(\d{2}/\d{2}\s+(?:Güz|Bahar|Hazırlık|Yaz))\s+([A-Z0-9]+)$")

class PDFParserService:
    """Öğrenci Mezuniyet Kontrol PDF'ini satır satır metin üzerinden okuyarak verileri ayrıştırır."""
    
    def extract_graduation_data(self, pdf_path: str) -> dict:
        result = {
            "son_guncelleme": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "ogrenci_bilgileri": {
                "numara": "", "ad_soyad": "", "sinif": "", "gano": "", "program": ""
            },
            "akts": {
                "basarilan": {"zorunlu": 0, "secmeli": 0, "bolum_disi": 0, "toplam": 0},
                "gereken": {"zorunlu": 0, "secmeli": 0, "bolum_disi": 0, "toplam": 0}
            },
            "basarilan_dersler": [],
            "ogretim_programi_dersleri": []
        }
        
        if not os.path.exists(pdf_path):
            logging.error("PDF dosyası bulunamadı!")
            return result

        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # layout=True görsel boşlukları korur, sütunların bitişmesini önler
                    page_text = page.extract_text(layout=True)
                    if page_text:
                        text += page_text + "\n"

            # Tüm metni satır satır inceliyoruz
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 1. ÖĞRENCİ BİLGİLERİ
                match_info = _RE_STUDENT_INFO.match(line)
                if match_info:
                    result["ogrenci_bilgileri"]["numara"] = match_info.group(1)
                    result["ogrenci_bilgileri"]["ad_soyad"] = match_info.group(2).strip()
                    result["ogrenci_bilgileri"]["sinif"] = match_info.group(3)
                    result["ogrenci_bilgileri"]["gano"] = match_info.group(4)
                    result["ogrenci_bilgileri"]["program"] = match_info.group(5).strip()
                    continue

                # 2. AKTS (8 adet yan yana sayıyı yakalar)
                match_akts = _RE_AKTS.match(line)
                if match_akts and result["akts"]["basarilan"]["toplam"] == 0:
                    result["akts"]["basarilan"] = {
                        "zorunlu": int(match_akts.group(1)),
                        "secmeli": int(match_akts.group(2)),
                        "bolum_disi": int(match_akts.group(3)),
                        "toplam": int(match_akts.group(4))
                    }
                    result["akts"]["gereken"] = {
                        "zorunlu": int(match_akts.group(5)),
                        "secmeli": int(match_akts.group(6)),
                        "bolum_disi": int(match_akts.group(7)),
                        "toplam": int(match_akts.group(8))
                    }
                    continue

                # 3. BAŞARILAN DERSLER
                match_ders = _RE_COURSE.match(line)
                if match_ders:
                    result["basarilan_dersler"].append({
                        "kod": match_ders.group(1),
                        "ders_adi": match_ders.group(2).strip(),
                        "donem": match_ders.group(3),
                        "harf_not": match_ders.group(4),
                        "akts": match_ders.group(5)
                    })
                    continue

                # 4. ÖĞRETİM PROGRAMI DERSLERİ
                match_prog = _RE_PROGRAM.match(line)
                if match_prog:
                    item = {
                        "program_yariyil": match_prog.group(1),
                        "program_ders": match_prog.group(2).strip(),
                        "program_akts": match_prog.group(3),
                        "basarilan_ders": "",
                        "basarilan_akts": "",
                        "basarilan_donem": "",
                        "basarilan_not": ""
                    }
                    
                    remaining = match_prog.group(4)
                    if remaining:
                        remaining = remaining.strip()
                        # Eğer sağ taraf doluysa onu da kendi içinde parçalıyoruz
                        match_rem = _RE_REMAINING.match(remaining)
                        if match_rem:
                            item["basarilan_ders"] = match_rem.group(1).strip()
                            item["basarilan_akts"] = match_rem.group(2)
                            item["basarilan_donem"] = match_rem.group(3)
                            item["basarilan_not"] = match_rem.group(4)
                        else:
                            # Nadiren harf notu boş olabilir, düz metin olarak kaydedelim
                            item["basarilan_ders"] = remaining
                    
                    result["ogretim_programi_dersleri"].append(item)
                    continue

            logging.info(f"PDF verileri başarıyla ayrıştırıldı.")
        except Exception as e:
            logging.error(f"PDF ayrıştırma hatası: {str(e)}")
            
        return result