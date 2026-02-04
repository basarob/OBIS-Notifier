# 🤖 OBIS Notifier - Yapay Zeka Geliştirici Bağlam Raporu (AI Context Report)

> **Amaç:** Bu doküman, OBIS Notifier projesini analiz edecek veya geliştirecek olan yapay zeka ajanlarına (AI Agents) projenin mimarisini, veri akışını ve genişletilebilirlik noktalarını eksiksiz aktarmak için hazırlanmıştır.

---

## 1. Proje Kimliği

- **Proje Adı:** OBIS Notifier (v3.0 - PyQt6 Migration)
- **Tanım:** ADÜ Öğrenci Bilgi Sistemi (OBIS) üzerindeki notları periyodik olarak tarayan, değişiklikleri tespit eden ve kullanıcıya masaüstü/e-posta yoluyla bildiren lokal otomasyon aracı.
- **Mevcut Durum:** CustomTkinter yapısından **PyQt6** yapısına geçiş aşamasındadır.
- **Dağıtım Türü:** Tekil Windows Uygulaması (`EXE`).

## 2. Teknoloji Yığını (Tech Stack)

| Katman       | Teknoloji / Kütüphane | Kullanım Amacı                                           |
| :----------- | :-------------------- | :------------------------------------------------------- |
| **Dil**      | Python 3.11+          | Ana geliştirme dili. (Type-hinting zorunlu)              |
| **UI**       | **PyQt6**             | Modern, Native-feel arayüz framework'ü.                  |
| **Scraping** | Playwright (Sync API) | Güvenilir ve headless tarayıcı otomasyonu.               |
| **Security** | Keyring               | Şifrelerin güvenli işletim sistemi kasasında saklanması. |
| **Schedule** | Schedule              | Periyodik görev zamanlayıcı.                             |
| **Icons**    | **Qtawesome**         | FontAwesome ikonlarını native PyQt ikonlarına çevirir.   |
| **Build**    | PyInstaller           | Uygulamayı tek dosya EXE haline getirmek.                |

## 3. Mimari Genel Bakış (PyQt6 Architecture)

Proje **Modüler Monolitik** yapıdadır ve UI katmanı tamamen ayrılmıştır.

```mermaid
graph TD
    User((Kullanıcı)) --> Views[UI Views (PyQt6)]
    Views --> MainWindow[Main Window Orchestrator]
    MainWindow --> Core[Çekirdek Katmanı (src/core)]

    subgraph UI Layer
    Views --> Components[Custom Components]
    Components --> Styles[Style & Themes]
    end

    subgraph Core Logic
    Core -->|Yönetir| BrowserService[Tarayıcı Servisi]
    Core -->|Yönetir| SessionManager[Oturum & Keyring Yöneticisi]
    Core -->|Yönetir| NotificationService[Bildirim Servisi]
    end
```

### 📂 Dosya Yapısı (Hedef Yapı)

| Dizin / Dosya             | Sorumluluk (Responsibility)                                                    |
| :------------------------ | :----------------------------------------------------------------------------- |
| `src/main.py`             | **Entry Point.** PyQt6 uygulamasını (`QApplication`) başlatır.                 |
| `src/ui/main_window.py`   | **Orchestrator.** `QStackedWidget` ile sayfalar arası geçişi yönetir.          |
| `src/ui/views/`           | **Sayfalar.** `login_view.py`, `dashboard.py` vb. her ekran ayrı bir dosyadır. |
| `src/ui/components/`      | **Bileşenler.** Sidebar, Topbar, Snackbar gibi tekrar kullanılabilir parçalar. |
| `src/ui/styles/`          | **Tema.** Renk paletleri, fontlar ve stil tanımları.                           |
| `src/services/session.py` | **Güvenlik.** Keyring ile şifre saklama ve otomatik giriş mantığı.             |
| `src/utils/logger_qt.py`  | **Logging.** Python loglarını `signal` ile arayüze taşıyan köprü.              |
| `src/core/notifier.py`    | **Backend.** (Eski yapıdan taşınıyor) Ana kontrol mekanizması.                 |

## 4. Mevcut İlerleme Durumu (Progress Status)

### ✅ Tamamlananlar (Completed)

- **Modern Login Ekranı:** PyQt6 ile yeniden yazıldı. Validasyonlar ve animasyonlar eklendi.
- **Browser & Login Entegrasyonu:** Mevcut `BrowserService` ile yeni UI arasındaki bağlantı sağlandı.
- **Güvenlik (Keyring):** Şifreler artık düz metin olarak değil, işletim sistemi anahtarlığında (`keyring` kütüphanesi) saklanıyor.
- **Auto-Login:** Uygulama açılışında kayıtlı oturum varsa otomatik giriş deneniyor.
- **Logout:** Profil üzerinden çıkış yapıldığında session temizleniyor.
- **Profil Sayfası:** `LoginView` ile birebir tasarımsal bütünlük sağlandı. Kullanıcı bilgileri kartı ve çıkış fonksiyonu tamamlandı.
- **Advanced Animations:** `OBISAnimations` sınıfı `QParallelAnimationGroup` (Paralel Animasyon) desteği ile güncellendi. "Nefes Alma (Breathing)" efektleri performant hale getirildi.
- **Sidebar (Refactored):**
  - Header (Logo), Navigasyon ve Footer (Sistem Durumu) olarak parçalandı.
  - **`StatusIndicator`**: Işıklı bildirim noktası için `QLabel` yerine özel `QWidget` (Custom Paint) yazılarak performans artırıldı.
  - Kod tekrarı önlendi ve stil tanımları temizlendi.
- **Topbar (Modernized):**
  - Sol (Başlık + Son Kontrol) ve Sağ (Bildirim + Profil) olarak ikiye ayrıldı.
  - Profil bileşeni `QFrame` yapısına çevrilerek layout sorunları giderildi.
  - Stil sızıntılarını önlemek için `#TopBar` ID selector kullanıldı.
  - **Veri Akışı:** Öğrenci numarası ve İsim parametreleri düzeltildi. (Numara doğru alana, İsim sabit "Ad Soyad" olarak ayarlandı).

  - "Son Kontrol" saatinin gerçek veriyle güncellenmesi.
  - Bildirim ikonu ve Badge (Okunmamış bildirim sayısı) entegrasyonu.

- **Logs (Log Kayıtları):**
  - Sanal terminal görünümü (Log Table).
  - Anlık akış (Live Stream) ve renklendirilmiş log seviyeleri.
  - Arama ve Temizleme fonksiyonları.

### 🚧 Bekleyenler / Yapılacaklar (In Progress / Todo)

- [ ] **Dashboard (Ana Sayfa):** Notların listelendiği tablo ve özet kartları.
- [ ] **Settings (Ayarlar):** Bildirim tercihleri, tarayıcı ayarları vb.
- [ ] **Profile (Profil):** "Bilgilerimi Güncelle" butonu işlevsiz durumda (Mock). Gelecekte backend entegrasyonu yapılacak.
- [ ] **Components:** Sidebar Footer kısmındaki sistem durumu indikatörünün (Yeşil/Kırmızı nokta) arka plandaki `Service` katmanına (Signal/Slot ile) bağlanması.
- [ ] **Data Fetching:** Kullanıcı adının (OBIS'ten çekilmesi) ve numaranın dinamikleşmesi. (Şu an isim "Ad Soyad" olarak sabit).
- [ ] **Topbar Dynamics:**
  - "Son Kontrol" saatinin gerçek veriyle güncellenmesi.
  - Bildirim ikonu ve Badge (Okunmamış bildirim sayısı) entegrasyonu.

## 5. Kritik Kurallar (Rules & Guidelines)

1.  **UI Thread Güvenliği:**
    - Uzun süren işlemler (Web scraping, login) ASLA UI thread'ini bloklamamalıdır.
    - `QThread` veya `QRunnable` kullanılmalıdır. İşlem bitince `pyqtSignal` ile UI güncellenmelidir.

2.  **Stil ve Tema:**
    - Hardcoded renkler YASAK. Tüm renkler `src/ui/styles/theme.py` içindeki `OBISColors` sınıfından gelmelidir.
    - Fontlar `OBISFonts` sınıfından çağrılmalıdır.
    - **Isolation:** `setStyleSheet` kullanırken ID Selector (`#ObjectName`) kullanarak stil sızıntılarını (Cascading issues) engelle.

3.  **Hata Yönetimi:**
    - Hata durumlarında kullanıcıya `OBISSnackbar` veya `QMessageBox` ile geri bildirim verilmeli, ancak uygulama çökmemelidir.
    - Tüm kritik hatalar `logging` modülü ile kaydedilmelidir.

4.  **Legacy Code (Eski Kod):**
    - `src/ui(eski)/` klasörü referans amaçlı tutulmaktadır. Buradan kod kopyalarken PyQt6 standartlarına (Signal/Slot yapısı) çevirerek al.
    - CustomTkinter kütüphanesi projeden tamamen kaldırılacaktır (Cleanup aşamasında).

---

_Bu rapor en son 05.02.2026 tarihinde güncellenmiştir._
