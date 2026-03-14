"""
BU DOSYA: Tarih ve akademik dönem (semester) işlemlerini yöneten yardımcı modüldür.
"""

from datetime import datetime

def _get_semester_string(start_year: int, term: str) -> str:
    """
    Örn: start_year=2024, term="Güz" -> '24/25 Güz' döndürür.
    """
    yy1 = str(start_year)[-2:]
    yy2 = str(start_year + 1)[-2:]
    return f"{yy1}/{yy2} {term}"

def get_current_semester() -> str:
    """
    Mevcut tarihe göre aktif akademik dönemi hesaplar.
    Kırılım Notları (Edge Cases):
    15 Eylül - 14 Şubat -> GÜZ Dönemi (Örn: 2024 Eylül - 2025 Şubat -> 24/25 Güz)
    15 Şubat - 14 Eylül -> BAHAR Dönemi (Örn: 2025 Şubat - 2025 Eylül -> 24/25 Bahar)
    """
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day

    # Eylül'ün 15i ile yıl sonuna kadar GÜZ dönemi (bulunulan yıl başlar)
    if (month == 9 and day >= 15) or month > 9:
        return _get_semester_string(year, "Güz")
    
    # Ocak başı ile Şubat'ın 14üne kadar hala bir önceki yılın GÜZ dönemi
    elif month == 1 or (month == 2 and day < 15):
        return _get_semester_string(year - 1, "Güz")
    
    # Şubat'ın 15i ile Eylül'ün 14üne kadar bir önceki yılın devamı olan BAHAR dönemi
    else:
        # Bahar dönemi her zaman (year-1) girişlidir. 
        # Çünkü "Bahar" dönemi genelde Ocak/Şubat aylarında başlayan ve bir önceki yılın takvimini takip eden dönemdir.
        # Örnek: Mayıs 2025 -> 24/25 Bahar
        return _get_semester_string(year - 1, "Bahar")


def generate_semester_list() -> list[str]:
    """
    Dinamik olarak ComboBox içerisinde gösterilecek dönemleri oluşturur.
    Kapsam: İçinde bulunulan dönem, 1 önceki dönem ve 1 gelecek dönem.
    """
    current_sem = get_current_semester()
    parts = current_sem.split()
    
    # "24/25" -> start=24
    year_str = parts[0].split("/")[0]
    # Yüzyılı ekleyelim: '24' -> 2024
    base_year = 2000 + int(year_str)
    
    current_term = parts[1] # "Güz" veya "Bahar"
    
    semesters = []
    
    if current_term == "Güz":
        # Mevcut: 24/25 Güz
        # Önceki: 23/24 Bahar
        # Sonraki: 24/25 Bahar
        semesters.append(_get_semester_string(base_year - 1, "Bahar"))
        semesters.append(current_sem)
        semesters.append(_get_semester_string(base_year, "Bahar"))
    else:
        # Mevcut: 24/25 Bahar
        # Önceki: 24/25 Güz
        # Sonraki: 25/26 Güz
        semesters.append(_get_semester_string(base_year, "Güz"))
        semesters.append(current_sem)
        semesters.append(_get_semester_string(base_year + 1, "Güz"))
        
    return semesters
