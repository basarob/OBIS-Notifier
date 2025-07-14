@echo off
title OBIS Notifier Kurulumu

cls
echo ===========================================
echo           OBIS Notifier Kurulumu          
echo ===========================================
echo.

echo [1/5] Python kontrol ediliyor...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Python yüklü değil veya PATH'e ekli değil!
    echo Lütfen https://www.python.org/downloads/ adresinden Python'u indirip kurun.
    echo.
    pause
    exit /b
) ELSE (
    echo Python bulundu ve sürümü uygun.
)
echo.

echo [2/5] pip güncelleniyor...
python -m pip install --upgrade pip
IF %ERRORLEVEL% EQU 0 (
    echo pip başarıyla güncellendi.
) ELSE (
    echo pip güncellemesi sırasında hata oluştu, devam ediyor...
)
echo.

echo [3/5] Gerekli paketler yükleniyor...
python -m pip install -r requirements.txt
IF %ERRORLEVEL% EQU 0 (
    echo Paketler başarıyla yüklendi.
) ELSE (
    echo Paket yükleme sırasında hata oluştu, lütfen internet bağlantınızı kontrol edin.
)
echo.

echo [4/5] Playwright browserlar indiriliyor...
python -m playwright install
IF %ERRORLEVEL% EQU 0 (
    echo Playwright browserlar başarıyla indirildi.
) ELSE (
    echo Playwright browser indirirken hata oluştu.
)
echo.

echo [5/5] Kurulum tamamlandı!
echo ==============================================================================
echo Lütfen config.py dosyasını Not Defteri ile açıp bilgilerinizi düzenleyin.
echo Ardından OBISNotifier.exe dosyasını çalıştırarak uygulamayı başlatabilirsiniz.
echo ==============================================================================
echo.

pause
exit