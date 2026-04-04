# 🤖 OBIS Notifier - Yapay Zeka Geliştirici Bağlam Raporu (AI Context Report)

> **Amaç:** Bu doküman, OBIS Notifier projesini analiz edecek veya geliştirecek olan yapay zeka ajanlarına (AI Agents) projenin mimarisini, otomasyon adımlarını, veri akışını ve genişletilebilirlik noktalarını eksiksiz aktarmak için hazırlanmıştır.

---

## 1. Proje Kimliği

- **Proje Adı:** OBIS Notifier (v3.0 - PyQt6 Migration & Autonomous Engine)
- **Tanım:** ADÜ Öğrenci Bilgi Sistemi (OBIS) üzerindeki notları periyodik olarak tarayan, değişiklikleri tespit eden, Github üzerinden kendi kendini otonom güncelleyebilen ve kullanıcıya e-posta/sistem tepsisi (tray) yoluyla bildiren lokal otomasyon aracı.
- **Mevcut Durum:** V3 (PyQt6) arayüz mimarisi, Playwright not kontrolü, Top-level import bazlı performans optimizasyonları ve Otonom GitHub Updater entegrasyonu tamamlanmıştır. Uygulama yayına hazırdır.
- **Dağıtım Türü:** Tekil Windows Uygulaması (`EXE`) - PyInstaller.

## 2. Teknoloji Yığını (Tech Stack)

| Katman       | Teknoloji / Kütüphane | Kullanım Amacı                                                               |
| :----------- | :-------------------- | :--------------------------------------------------------------------------- |
| **Dil**      | Python 3.11+          | Ana geliştirme dili. (Type-hinting zorunlu)                                  |
| **UI**       | **PyQt6**             | Modern, Native-feel arayüz framework'ü (QSystemTrayIcon destekli).           |
| **Scraping** | Playwright (Sync API) | Güvenilir ve headless tarayıcı otomasyonu.                                   |
| **Security** | Keyring               | Şifrelerin güvenli işletim sistemi kasasında saklanması.                     |
| **Schedule** | QTimer                | UI tarafında asenkron periyodik görev zamanlayıcı.                           |
| **Icons**    | **Qtawesome**         | FontAwesome ikonlarını native PyQt ikonlarına çevirir.                       |
| **Build**    | PyInstaller           | Yalnızca "işlevsel" bağımlılıkları barındıran hafifletilmiş EXE derleyicisi. |
| **Parser**   | pdfplumber            | Üniversite profil verilerini PDF'den ayıklamak için.                         |

> **Not:** Windows 11 bildirimleri (win11toast) ve legacy arkaplan çalıştırıcıları projeden çıkartılarak sadeleştirilmiştir. Sistem sesleri için built-in `winsound` ve Updater için built-in `urllib` kullanılmaktadır.

## 3. Mimari Genel Bakış (PyQt6 Architecture)

Proje **Modüler Monolitik Component (Bileşen)** yapısındadır. Sistem başlangıcı (Startup), UI görünümleri (Views), Arkaplan İşçileri (Workers) ve Çekirdek (Core/Services) katmanlarına keskin bir şekilde ayrılmıştır.

```mermaid
graph TD
    User((Kullanıcı)) --> Startup[StartupManager (Update & System Check)]
    Startup --> Views[UI Controllers/Views]
    Views --> Component[UI Cards (Arayüz Bileşenleri)]
    Views --> MainWindow[Main Window Orchestrator & System Tray]
    Views --> Worker[QThread Workerlar (Login, Check, Update)]
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

| Dizin / Dosya             | Sorumluluk (Responsibility)                                                                                                                   |
| :------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/main.py`             | **Entry Point.** QApplication'ı başlatır, global dizinleri hazırlar ve logları kurar.                                                         |
| `src/ui/main_window.py`   | **Orchestrator.** `QStackedWidget` geçişini ve Sistem Tepsisi (Tray) davranışlarını yönetir.                                                  |
| `src/ui/utils/startup.py` | **Manager.** Uygulama başlarken ardışık Github sürüm doğrulamasını ve Playwright Chromium indirmelerini UI'ı tıkamadan halleder.              |
| `src/ui/utils/worker.py`  | **Asenkron Köprü.** Backend (`core/services`) bloklarını UI'a asenkron çağıran `Top-Level Import` yapısına sahip iş parçacıkları `(QThread)`. |
| `src/ui/views/*.py`       | **Sayfalar (Denetçiler).** `dashboard.py`, `settings.py`, `login_view.py` iş akışı yönetimi.                                                  |
| `src/ui/views/*_cards.py` | **Sayfa Bileşenleri.** Sadece çizim mantığını tutarak Obez sınıfları engelleyen Component'ler.                                                |
| `src/ui/styles/`          | **Tema.** Renk paletleri (`OBISColors`), fontlar ve native Qt elementleri tasarımları.                                                        |
| `src/services/updater.py` | **Otonom Motor.** GitHub sürümlerini semantik kıyaslayan (urllib) ve sistemi otonom yamalayan (.bat destekli) modül.                          |

## 4. Mevcut İlerleme Durumu (Progress Status)

### ✅ Tamamlananlar (Completed)

- **Top-Level Performans İyileştirmeleri:** Bütün lazy (inner) importlar dosya köküne taşınarak thread'ler üzerindeki load engeli kaldırılmıştır.
- **Güvenli Auto-Updater:** Uygulama GitHub Releases API'si ile versiyonunu kontrol eder (`updater.py`). Yeni .exe yayınlanmışsa 2 saniyelik bir `update_script.bat` ile sistemi kapatıp `.exe`'yi ezer ve kendini geri açar.
- **Fail-Fast Playwright Koruyucusu:** İlk açılıştaki Chromium/Playwright indirmesi sırasında internet kopması vs. nedeniyle kurulamama olursa sistem fail-fast prensibiyle 3 saniye içinde ilgili bozuk klasörleri temizleyip kendini kapatır (Temiz kurulum garantisi).
- **Temizlenmiş Bağımlılıklar (Clean Dependencies):** `win11toast`, `requests`, `packaging`, `pystray` gibi işlevselliğini yitiren legacy bileşenler `setup.bat`, `build.yml` ve kod yapısından sökülerek `requirements.txt` sadeleştirilmiştir. (CI/CD üzerinden redundant playwright indirmesi iptal edildi).
- **Hardened Error UI (Gerçek Zamanlı Durum Loglaması):** Özellikle backend'deki Mail Gönderim hataları (`❌ E-Mail gönderme hatası...`) veya Dönem/Parametre Bulamama Hataları artık doğrudan Dashboard Timeline bileşenine taşındı.
- **Safe Session Close:** Kullanıcı uygulamayı pencereden (`X`) veya Tray'den kapattığında Logout atılmaz (session silinmez). Yalnızca profil menüsündeki "Çıkış Yap" butonuna tıklandığında `profile.json` ve şifreler imha edilir.

### 🚧 Bekleyenler / Eksiklikler (Shortcomings & Future Works)

Projenin mimari açığı veya bilinen bir BUG'u bulunmamaktadır. Aşağıdakiler sadece vizyon amaçlı genişletilebilir adımlardır:

- [ ] **Data Limitleri (Pagination):** Canlı sistem logları (`LogsView`) tableWidget tabanlı işlendiği için günlerce çalışan bir senaryoda on binlerce satırı bulabilir. Belleğe oturan bu listeyi periyodik olarak uçuran bir Çöp Toplayıcı (Garbage Collector) yazılabilir.
- [ ] **Yapay Zeka veya Akıllı Filtre:** Eğitim görevlisinin tek bir dersteki harf notunu ardı ardına ("BB" "BA" "AA") 5 kez değiştirmesini izole edip spam mailleri engelleyecek rate-limit filtreleri tanımlanabilir. E-mail yerine Telegram entegrasyonu da opsiyonlar içine kolayca dahil olabilir.

## 5. Kritik Kurallar (Rules & Guidelines)

1. **Thread Güvenliği:**
   Eğer arayüzde (UI) bir tuşa basılınca Chromium tetiklenecekse ASLA ana fonksiyon üzerinden çalıştırılamaz. `src/ui/utils/worker.py` kullanmak ve süreci QThread sinyali(`status_signal.emit()`) ile taşımak mecburidir.
2. **Performans (Import Routing):**
   Lazy (inner) import'lara kesinlikle izin verilmemektedir. PyInstaller'ın import köklerini doğru okuyup EXE'den çıkartması ve çalışma anı (Runtime) performans kaybı yaşamamak adına tüm importlar dosya kökünde modülerce bulunmalıdır.
3. **Standart Kütüphane Hassasiyeti:**
   Olabildiğince az dış modül kullanılacaktır. (Ör: `urllib` dururken `requests` eklenmeyecek, sistem bildirimi için `winsound` tercih edilecek).
4. **Stil ve Tema Zorunluluğu:**
   Hardcoded renk tanımı (`#FF5733` vs.) kesinlikle **YASAKTIR**. Yeni UI eklenecekse tüm renkler `src/ui/styles/theme.py` içindeki modaya uygun olarak (`OBISColors.xyz`) çağrılır.
5. **Güvenlik (Keyring):**
   `obis_password` diske kaydedilmez. Otomatik doğrulama işlemleri Windows Credentials Management API (`keyring`) üzerinden işletilir.

---

_Bu doküman; Autonomous Updater, UI Startup Manager ve Pyinstaller Top-Level optimizasyonlarının inşa edildiği OBIS Notifier (Core Update) sürümünün ardından tam projeyi analiz ederek en güncel teknoloji verilerini yansıtacak şekilde revize edilmiştir._
