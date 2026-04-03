# 🤖 OBIS Notifier - Yapay Zeka Geliştirici Bağlam Raporu (AI Context Report)

> **Amaç:** Bu doküman, OBIS Notifier projesini analiz edecek veya geliştirecek olan yapay zeka ajanlarına (AI Agents) projenin mimarisini, veri akışını ve genişletilebilirlik noktalarını eksiksiz aktarmak için hazırlanmıştır.

---

## 1. Proje Kimliği

- **Proje Adı:** OBIS Notifier (v3.0 - PyQt6 Migration)
- **Tanım:** ADÜ Öğrenci Bilgi Sistemi (OBIS) üzerindeki notları periyodik olarak tarayan, değişiklikleri tespit eden ve kullanıcıya masaüstü/e-posta yoluyla bildiren lokal otomasyon aracı.
- **Mevcut Durum:** V3 (PyQt6) arayüz mimarisi ve not kontrol entegrasyonu tamamlanmıştır. Uygulama test ve stabilizasyon aşamasındadır.
- **Dağıtım Türü:** Tekil Windows Uygulaması (`EXE`).

## 2. Teknoloji Yığını (Tech Stack)

| Katman       | Teknoloji / Kütüphane | Kullanım Amacı                                           |
| :----------- | :-------------------- | :------------------------------------------------------- |
| **Dil**      | Python 3.11+          | Ana geliştirme dili. (Type-hinting zorunlu)              |
| **UI**       | **PyQt6**             | Modern, Native-feel arayüz framework'ü.                  |
| **Scraping** | Playwright (Sync API) | Güvenilir ve headless tarayıcı otomasyonu.               |
| **Security** | Keyring               | Şifrelerin güvenli işletim sistemi kasasında saklanması. |
| **Schedule** | QTimer                | UI tarafında asenkron periyodik görev zamanlayıcı.         |
| **Icons**    | **Qtawesome**         | FontAwesome ikonlarını native PyQt ikonlarına çevirir.   |
| **Build**    | PyInstaller           | Uygulamayı tek dosya EXE haline getirmek.                |

## 3. Mimari Genel Bakış (PyQt6 Architecture)

Proje **Modüler Monolitik Component (Bileşen)** yapısındadır. UI "orchestrator (yönlendirici)" görünüm sınıfları (Views) ile tasarımsal bileşen sınıfları (Cards) tamamen ayrılmıştır.

```mermaid
graph TD
    User((Kullanıcı)) --> Views[UI Controllers/Views]
    Views --> Component[UI Cards (Arayüz Bileşenleri)]
    Views --> MainWindow[Main Window Orchestrator]
    Views --> Worker[QThread Workerlar]
    Worker --> Core[Çekirdek Katmanı (src/core)]

    subgraph Component Layer
    Component --> Styles[Style & Themes]
    end

    subgraph Core Logic
    Core -->|Yönetir| BrowserService[Tarayıcı Servisi]
    Core -->|Yönetir| SessionManager[Oturum & Keyring Yöneticisi]
    Core -->|Yönetir| NotificationService[Bildirim Servisi]
    end
```

### 📂 Dosya Yapısı (Mevcut Yapı)

| Dizin / Dosya                | Sorumluluk (Responsibility)                                                          |
| :--------------------------- | :----------------------------------------------------------------------------------- |
| `src/main.py`                | **Entry Point.** PyQt6 uygulamasını (`QApplication`) başlatır.                       |
| `src/ui/main_window.py`      | **Orchestrator.** `QStackedWidget` ile sayfalar arası geçişi yönetir.                |
| `src/ui/views/*.py`          | **Sayfalar (Denetçiler).** `dashboard.py`, `settings.py` sadece mantık ve iş akışı yönetir. |
| `src/ui/views/*_cards.py`    | **Sayfa Bileşenleri.** UI Çizimlerini, Layout'ları kapsülleyen Component Sınıfları.    |
| `src/ui/utils/worker.py`     | **Asenkron Köprü.** Backend (`OBISNotifier`) ile UI'ı bağlayan `QThread` sınıfları. |
| `src/ui/styles/`             | **Tema.** Renk paletleri (`OBISColors`), fontlar ve stil tanımları.                  |
| `src/services/session.py`    | **Güvenlik.** Keyring ile şifre saklama ve otomatik giriş mantığı.                   |
| `src/services/pdf_parser.py` | **Veri İşleme.** İndirilen Mezuniyet PDF'inden Regex ile öğrenci verilerini çıkarır. |

## 4. Mevcut İlerleme Durumu (Progress Status)

### ✅ Tamamlananlar (Completed)

- **Frontend & Backend Ayrımı:** Arayüz (`PyQt6`) ve İş mantığı (`Playwright/OBISNotifier`) `CheckWorker (QThread)` sayesinde birbirini bloke etmez hale getirildi. 
- **Modern Login & Oturum Yönetimi:** Güvenli Keyring desteği, 3 başarısız deneme limiti, auto-login ve cache temizlik tabanlı temiz çıkış (Logout) sistemi tamamlandı.
- **Dashboard Component Refactoring:** 800+ satırlık obez dashboard dosyası sadece bir denetleyiciye (Controller) dönüştürüldü. Çizim mantığı `ControlCard`, `StatsCard` ve `TimelineCard` sınıflarına bölündü.
- **Settings Component Refactoring:** Aynı şekilde 700+ satırlık ayarlar, `AutomationCard`, `NotificationCard`, `AdvancedCard` modüllerine ayrılarak temizlendi. Hardcode renk/pozisyon tanımları silindi ve projede tam anlamıyla **Theme Engine (`OBISColors`)** kullanılmaya başlandı.
- **Tasarım Elementleri & Event Engellemeleri:** Ayarlar sayfasındaki CheckBox/ComboBox yapılarının Scroll sırasında yanlışlıkla değişmesi (WheelEvent engellemesi) gibi UX bugları çözüldü. Buton stili değişimindeki boya kalıntıları (Rendering Bug) `unpolish/polish` mantığıyla kalıcı olarak yok edildi.
- **Timeline & Log Akışı:** Uygulama içinde manuel ve otomatik yapılan işlemler zaman damgasıyla Timeline bileşenini ve Logs ekranını anlık olarak güncelliyor. 
- **Email Sistemi (Tamamen Entegre):** Yeni bir ders notu yakalandığında veya test talebi tetiklendiğinde `NotificationService` vasıtasıyla güzel gözüken HTML tabanlı mail şablonlarıyla kullanıcılara not fırlatılabiliyor. 

### 🚧 Bekleyenler / Eksiklikler (Shortcomings & Future Works)

Projede şu anda "hata" bulunmamakta ancak sistemin ölçeklenebilirliği (Scalability) ve uzun ömürlülüğü açısından henüz **eksik** olan noktalar mevcuttur:

- [ ] **Canlı Ortam Doğrulaması:** Uygulamanın en stresli işlevlerinden biri "Mevcut notlar üzerinde gerçekten değişiklik/yeni not girildiğinde" programın diff (fark) alıp maile yansıtmasıdır. Bu bir öğrenci için henüz canlı veride **test edilmemiştir**.
- [ ] **JSON Ölçeklenebilirliği:** Veriler (`grades_data.json`, `profile.json`, `settings.json`) JSON olarak saklanmaktadır. Eğer öğrencinin çok fazla not geçmişi veya ders durumu olursa zamanla parsing ağırlığı oluşturabilir. Gelecekte SQLite'a geçiş gerekebilir.
- [ ] **Log Ekranı Şişmesi:** `LogsView` ekranında on binlerce satır log yazılırsa arayüz performans kaybı yaşayabilir (QTableWidget render sıkıntısı). Satır bazlı *Pagination (Sayfalama)* veya eski satırları düşüren *Garbage Collector* yazılması düşünülebilir.
- [ ] **Rate-Limiting Exceed Koruması:** Eğitmen aynı ders notunu üst üste 1 saat içerisinde 5 kere düzeltirse, sistem aynı e-postayı 5 kere atar. Zeki bildirim filtreleme (Smart grouping / Digest) mekanizması yapısı ileride eksikliği hissedilecek bir noktadır.
- [ ] **Gelişmiş Error-Handling:** OBİS sunucuları yoğunluktan patladığında (502 Bad Gateway), sistem bazen sahte bir hata dönebilir. Backoff algoritmalarına (Logaritmik geri deneme) geçiş yapılmalıdır.

## 5. Kritik Kurallar (Rules & Guidelines)

1.  **Thread Güvenliği:**
    - Uzun süren işlemler ASLA UI thread'ini bloklamamalıdır (bkz: `src/ui/utils/worker.py`).
2.  **Stil ve Tema Zorunluluğu:**
    - Sınıfların içinden el yordamıyla `#FF5733` vs tetiklemek kesinlikle **YASAK**.
    - Tüm renkler, fontlar `src/ui/styles/theme.py` üzerinden çağrılacaktır (`OBISColors.xyz`).
3.  **God Object Kaçınması:**
    - Görünümler (Views) eğer 300-400 satırı aşıyorsa o ekran için hemen bir `_cards.py` veya `_components.py` dizini yaratıp UI dizgi mantığını oraya taşıyın. View sadece sinyal alıp veren bir koordinatör (Controller) olmalıdır.
4.  **Güvenlik İzleri:**
    - `student_id` ve `obis_password` gibi hassas veriler ASLA diske yazılmaz, `SessionManager` ile Keyring sisteminde (Windows'ta Credential Vault) tutulur, `Settings.json` içinden ayıklanır.

---
_Bu yapılandırma dokümanı, Model-View-Controller benzeri Component-bazlı Refactoring ve Backend Entegrasyonu (Sürüm 3.0) sonrası güncellenmiştir._
