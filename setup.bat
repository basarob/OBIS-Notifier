@echo off
title OBIS Notifier Kurulum Sihirbazi

cls
echo ===========================================
echo        OBIS Notifier v2.1 Kurulumu          
echo ===========================================
echo.

echo [1/5] Python kontrol ediliyor...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Python yuklu degil veya PATH'e ekli degil!
    echo Lutfen https://www.python.org/downloads/ adresinden Python'u indirip kurun.
    echo Kurulum sirasinda "Add Python to PATH" secenegini isaretlemeyi unutmayin.
    echo.
    pause
    exit /b
) ELSE (
    echo Python bulundu.
)
echo.

echo [2/5] pip guncelleniyor...
python -m pip install --upgrade pip
echo.

echo [3/5] Gerekli paketler yukleniyor...
python -m pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo [HATA] Paket yukleme sirasinda hata olustu. Internet baglantinizi kontrol edin.
    pause
    exit /b
)
echo.

echo [4/5] Playwright tarayicilari indiriliyor...
python -m playwright install
IF %ERRORLEVEL% NEQ 0 (
    echo [HATA] Playwright tarayicilari indirilemedi.
    pause
    exit /b
)
echo.

echo [5/5] Uygulama (EXE) olusturuluyor...
echo Bu islem biraz zaman alabilir...
if not exist "dist" mkdir "dist"
pyinstaller --noconsole --onefile --name "OBISNotifier" --distpath "dist" --workpath "build" --icon="src/images/icon.ico" --add-data "src/images;images" --hidden-import "pystray" --hidden-import "PIL" --hidden-import "win11toast" --hidden-import "requests" --hidden-import "packaging" --paths="src" src/main_gui.py

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo                           KURULUM TAMAMLANDI!
    echo ==============================================================================
    echo 1. "dist" klasoru icindeki "OBISNotifier.exe" dosyasini kullanabilirsiniz.
    echo 2. Veya dogrudan "python src/main_gui.py" komutu ile kodu calistirabilirsiniz.
    echo ==============================================================================
) ELSE (
    echo [UYARI] EXE olusturulamadi, ancak kutuphaneler yuklendi.
    echo "python src/main_gui.py" yazarak uygulamayi calistirabilirsiniz.
)
echo.
pause
