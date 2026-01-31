# 🎓 OBIS Notifier

<img src="src/images/banner_placeholder.png" width="100%">

<p align="center">
  <a href="#türkçe">Türkçe</a> •
  <a href="#english">English</a>
</p>

---

<h2 id="türkçe">🇹🇷 Türkçe</h2>

### 🚀 Proje Hakkında

**OBIS Notifier**, ADÜ Öğrencileri için geliştirilmiş, **OBIS (Öğrenci Bilgi Sistemi)** üzerindeki not değişikliklerini anlık olarak takip eden ve email ile bildiren akıllı bir masaüstü uygulamasıdır.

Sürekli siteye girip "Acaba notum açıklandı mı?" diye F5 yapmaktan yorulduysanız, bu uygulama tam size göre!

### ✨ Özellikler

- **🔄 Otomatik Takip:** Belirlediğiniz aralıklarla (örneğin her 20 dakikada bir) notlarınızı kontrol eder.
- **📩 Çoklu Bildirim:** Yeni bir not açıklandığında **E-posta** veya **Windows Bildirimi** (veya ikisi birden) alabilirsiniz.
- **⬆️ Otomatik Güncelleme:** Uygulama açılışında yeni sürüm kontrolü yapar ve sizi uyarır.
- **🖼️ Modern Arayüz:** Kullanıcı dostu, şık ve anlaşılır arayüz.
- **🤖 Akıllı Kurulum:** Tek bir `EXE` dosyasıyla çalışır. Gerekli tarayıcı bileşenlerini otomatik kurar.
- **🛡️ Güvenli:** Şifreniz sadece kendi bilgisayarınızda tutulur, dışarı aktarılmaz.
- **🧹 Temiz Çalışma Alanı:** Ayarlar ve loglar `%AppData%` klasöründe saklanır, masaüstünüzü kirletmez.

### ⚙️ Kullanılan Teknolojiler

Bu proje, modern ve güçlü kütüphaneler kullanılarak geliştirilmiştir:

- **[Python 3.11](https://www.python.org/):** Ana programlama dili.
- **[Playwright](https://playwright.dev/):** Hızlı ve güvenilir web otomasyonu (Scraping) için.
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** Modern ve şık arayüz tasarımı için.
- **[GitHub Actions](https://github.com/features/actions):** Otomatik derleme (CI/CD) süreçleri için.

### 📂 Proje Yapısı

```
OBIS-Notifier/
├── .github/          # GitHub Actions (Otomatik Build)
├── src/              # Kaynak Kodlar (Source)
│   ├── core/         # Çekirdek Mantık (Notifier Facade)
│   ├── services/     # Servisler (Browser, Grades, Notification)
│   ├── ui/           # Arayüz (GUI) Kodları
│   ├── utils/        # Yardımcı Araçlar
│   ├── config.py     # Konfigürasyon
│   └── main.py       # Başlangıç Noktası (Entry Point)
├── .gitattributes/   # Git ayarları
├── .gitignore/       # Git ignore dosyaları
├── LICENSE           # Lisans dosyası
├── README.md         # Okunabilir proje tanıtımı
├── requirements.txt  # Gerekli kütüphaneler
└── setup.bat         # Yerel kurulum ve EXE oluşturma aracı
```

### 📦 Kurulum ve Kullanım

1. **İndirin:** [Releases](https://github.com/basarob/OBIS-Notifier/releases) sayfasından en güncel `OBISNotifier.exe` dosyasını indirin.
2. **Çalıştırın:** İndirdiğiniz dosyayı çift tıklayarak açın. (Gerekirse yönetici olarak çalıştırın).
3. **Ayarlayın:**
   - **Öğrenci No:** Okul numaranız (Sistem `@stu.adu.edu.tr` otomatik ekler).
   - **OBIS Şifre:** Okul şifreniz.
   - **Bildirim Tercihi:** E-posta, Windows veya ikisini seçin.
   - **Gmail:** (E-posta seçiliyse) Bildirimlerin geleceği Gmail adresiniz.
   - **Uygulama Şifresi:** Gmail güvenlik ayarlarından alacağınız [Uygulama Şifresi](https://myaccount.google.com/apppasswords).
4. **Başlatın:** "Sistemi Başlat" butonuna basın ve arkanıza yaslanın!

> [!WARNING]
> **Windows Uyarısı Hakkında:** Uygulama dijital imzaya sahip olmadığı için ilk çalıştırmada **Windows SmartScreen** uyarısı ("Windows kişisel bilgisayarınızı korudu") alabilirsiniz. Bu beklenen bir durumdur.
>
> Devam etmek için: **Ek Bilgi (More Info) -> Yine de Çalıştır (Run Anyway)** butonuna tıklayınız.

### 📸 Ekran Görüntüleri

|                       Ana Ekran                        |                          E-posta Bildirim                           |                          Windows Bildirim                          |
| :----------------------------------------------------: | :-----------------------------------------------------------------: | :----------------------------------------------------------------: |
| <img src="src/images/screenshot_main.png" width="250"> | <img src="src/images/screenshot_mail_notification.png" width="250"> | <img src="src/images/screenshot_win_notification.png" width="250"> |

---

<h2 id="english">🇬🇧 English</h2>

### 🚀 About The Project

**OBIS Notifier** is a smart desktop automation tool designed for university students to track their grades on the **OBIS (Student Information System)** in real-time.

Stop refreshing the page every 5 minutes! Let OBIS Notifier handle the stress for you.

### ✨ Features

- **🔄 Auto-Check:** Monitors your grades at set intervals (e.g., every 20 mins).
- **📩 Multi-Notify:** Get alerts via **Email**, **Windows Notification**, or both when a grade is announced.
- **⬆️ Auto-Updater:** Automatically checks for new versions on startup and notifies you.
- **🖼️ Modern UI:** Sleek and user-friendly interface powered by CustomTkinter.
- **🤖 Smart Setup:** Runs as a single portable `EXE`. Automatically installs necessary browser components.
- **🛡️ Secure:** Your credentials are stored locally and never shared.
- **🧹 Clean Workspace:** Settings and logs are stored in `%AppData%`, keeping your desktop clean.

### ⚙️ Tech Stack

- **[Python 3.11](https://www.python.org/)**
- **[Playwright](https://playwright.dev/):** For reliable web scraping.
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** For modern UI components.
- **[GitHub Actions](https://github.com/features/actions):** For automated builds.

### 📂 Project Structure

```
OBIS-Notifier/
├── .github/          # GitHub Actions (Auto Build)
├── src/              # Source Code
│   ├── core/         # Core Logic (Notifier Facade)
│   ├── services/     # Services (Browser, Grades, Notification)
│   ├── ui/           # User Interface (GUI) Code
│   ├── utils/        # Utility Functions
│   ├── config.py     # Configuration
│   └── main.py       # Entry Point
├── .gitattributes/   # Git attributes
├── .gitignore/       # Git ignore files
├── LICENSE           # License file
├── README.md         # Project description
├── requirements.txt  # Dependencies
└── setup.bat         # Local setup script
```

### 📦 Installation & Usage

1. **Download:** Get the latest `OBISNotifier.exe` from the [Releases](https://github.com/basarob/OBIS-Notifier/releases) page.
2. **Run:** Double-click the downloaded file.
3. **Configure:**
   - **Student ID:** Your university ID (`@stu.adu.edu.tr` is added automatically).
   - **OBIS Password:** Your system password.
   - **Notify Preference:** Choose Email, Windows, or both.
   - **Gmail:** (If Email selected) The address to receive alerts.
   - **App Password:** Your Google [App Password](https://myaccount.google.com/apppasswords).
4. **Start:** Click "Start System" and relax!

> [!WARNING]
> **About Windows Warning:** Since the application is not digitally signed, you may see a **Windows SmartScreen** warning ("Windows protected your PC") on the first run. This is expected behavior.
>
> To proceed: Click **More Info -> Run Anyway**.

### 📸 Screenshots

|                      Main Screen                       |                         Email Notification                          |                        Windows Notification                        |
| :----------------------------------------------------: | :-----------------------------------------------------------------: | :----------------------------------------------------------------: |
| <img src="src/images/screenshot_main.png" width="250"> | <img src="src/images/screenshot_mail_notification.png" width="250"> | <img src="src/images/screenshot_win_notification.png" width="250"> |

---

### 🛠️ Development (Geliştirici)

#### Requirements

- Python 3.11+
- Playwright

#### Setup

```bash
git clone https://github.com/basarob/OBIS-Notifier.git
cd OBIS-Notifier
pip install -r requirements.txt
playwright install
python src/main_gui.py
```

#### Build EXE

```bash
setup.bat
```

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
