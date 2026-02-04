---
description: Yeni Özellik Ekleme ve Kodlama Başlatıcı
---

## trigger: Kullanıcı yeni bir özellik (feature) istediğinde

**ACT AS:** Solutions Architect

**OBJECTIVE:**
Yeni bir özellik kodlamadan önce, bu özelliğin mevcut mimariye, temaya ve bileşen setine %100 uyumlu olduğundan emin ol.

**PRE-CODING CHECKLIST (Kodlamadan Önce Uygula):**

1.  **Bağlam Yükleme:**
    - Bu özellik hangi `View` içinde olacak? O dosyanın içeriğini oku.
    - Bu özellik hangi `Service`'leri kullanacak? İlgili servisleri oku.
    - Tasarım gerekiyorsa: `src/ui/styles/theme.py` dosyasını oku.

2.  **Bileşen Kontrolü:**
    - `src/ui/components/` altında bu iş için kullanılabilecek hazır bir widget var mı?
    - Varsa onu kullan, yoksa yeni bir component oluşturmayı teklif et (Inline kod yazma).

3.  **Planlama (Implementation Plan):**
    - Yapılacak değişiklikleri adım adım **TÜRKÇE** olarak listele.
    - Dosya isimlerini ve kullanılacak fonksiyonları belirt.

4.  **Yorum Satırları:**
    - Yeni bir dosya oluşturulacaksa dosya başına """BU DOSYA:...""" şeklinde dosya tanıtımını yap.
    - Eklenecek yorum satırlarını **TÜRKÇE** olarak oluştur.

**ÇIKTI FORMATI:**
Kod yazmaya başlamadan önce onayıma şu planı sun:

> 📋 **UYGULAMA PLANI**
>
> 1. [Dosya Adı] -> [Yapılacak Değişiklik]
> 2. Kullanılacak Hazır Bileşenler: [Component Adları]
> 3. Eklenecek Yeni Kodlar: [Kısaca Açıkla]
