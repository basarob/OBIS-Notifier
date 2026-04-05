"""
BU DOSYA: E-posta bildirimleri için kullanılacak HTML şablonlarını içerir.
Stiller, OBISColors ve tema kurallarıyla uyumlu olacak şekilde hazırlanmıştır.
"""

from datetime import datetime
from ui.styles.theme import OBISColors

class OBISEmailTemplates:
    
    @staticmethod
    def get_grade_change_template(ders_adi: str, yeni_bilgiler: dict) -> str:
        """Ders güncellendiğinde gönderilecek HTML şablon."""
        zaman = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        return f"""
        <html>
        <body style="margin: 0; padding: 0; background-color: {OBISColors.BACKGROUND}; font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="padding: 30px 15px;">
                <div style="max-width: 600px; margin: auto; background-color: {OBISColors.SURFACE}; border-radius: 12px; border: 1px solid {OBISColors.BORDER}; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    
                    <div style="background-color: {OBISColors.SUCCESS}; color: {OBISColors.TEXT_WHITE}; padding: 20px; text-align: center;">
                        <h2 style="margin: 0; font-size: 20px; font-weight: bold;">🔄 Ders Güncellendi 🔄</h2>
                    </div>
                    
                    <div style="padding: 24px;">
                        <div style="font-size: 16px; color: {OBISColors.TEXT_PRIMARY}; margin-bottom: 20px; text-align: center; font-weight: 600;">
                            {ders_adi}
                        </div>
                        
                        <div style="border: 1px solid {OBISColors.BORDER}; border-radius: 8px; overflow: hidden;">
                            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                                <tr style="background-color: {OBISColors.INPUT_BG}; border-bottom: 1px solid {OBISColors.BORDER};">
                                    <td style="padding: 14px 16px; font-weight: 600; width: 35%; color: {OBISColors.TEXT_SECONDARY};">Sınavlar</td>
                                    <td style="padding: 14px 16px; color: {OBISColors.TEXT_PRIMARY};">{yeni_bilgiler.get('Sınavlar', '-')}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid {OBISColors.BORDER};">
                                    <td style="padding: 14px 16px; font-weight: 600; color: {OBISColors.TEXT_SECONDARY};">Harf Notu</td>
                                    <td style="padding: 14px 16px; color: {OBISColors.PRIMARY}; font-weight: bold; font-size: 16px;">{yeni_bilgiler.get('Harf Notu', '-')}</td>
                                </tr>
                                <tr style="background-color: {OBISColors.INPUT_BG};">
                                    <td style="padding: 14px 16px; font-weight: 600; color: {OBISColors.TEXT_SECONDARY};">Sonuç</td>
                                    <td style="padding: 14px 16px; color: {OBISColors.TEXT_PRIMARY};">{yeni_bilgiler.get('Sonuç', '-')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="text-align: right; font-size: 12px; color: {OBISColors.TEXT_GHOST}; margin-top: 20px;">
                            ⏰ {zaman}
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_test_notification_template() -> str:
        """Test bildirimi için HTML şablon."""
        zaman = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        return f"""
        <html>
        <body style="margin: 0; padding: 0; background-color: {OBISColors.BACKGROUND}; font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="padding: 30px 15px;">
                <div style="max-width: 600px; margin: auto; background-color: {OBISColors.SURFACE}; border-radius: 12px; border: 1px solid {OBISColors.BORDER}; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="background-color: {OBISColors.INFO}; color: {OBISColors.TEXT_WHITE}; padding: 20px; text-align: center;">
                        <h2 style="margin: 0; font-size: 20px; font-weight: bold;">Sistem Testi</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div style="font-size: 16px; color: {OBISColors.TEXT_PRIMARY}; margin-bottom: 20px;">
                            Merhaba,<br><br>
                            Bu bir test bildirimidir. Ayarlarınız doğru yapılandırılmış görünüyor ve bildirim sistemi sorunsuz çalışıyor.
                        </div>
                        <div style="text-align: right; font-size: 12px; color: {OBISColors.TEXT_GHOST}; margin-top: 20px;">
                            ⏰ {zaman}
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def get_failure_notification_template() -> str:
        """Başarısız giriş bildirimi için HTML şablon."""
        zaman = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        return f"""
        <html>
        <body style="margin: 0; padding: 0; background-color: {OBISColors.BACKGROUND}; font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="padding: 30px 15px;">
                <div style="max-width: 600px; margin: auto; background-color: {OBISColors.SURFACE}; border-radius: 12px; border: 1px solid {OBISColors.BORDER}; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <div style="background-color: {OBISColors.DANGER}; color: {OBISColors.TEXT_WHITE}; padding: 20px; text-align: center;">
                        <h2 style="margin: 0; font-size: 20px; font-weight: bold;">⚠️ Sistem Durduruldu ⚠️</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div style="font-size: 16px; color: {OBISColors.TEXT_PRIMARY}; margin-bottom: 20px;">
                            Merhaba,<br><br>
                            OBIS Not not kontrolü esnasında <b>ardışık 3 kez</b> hata meydana geldi.<br>
                            Güvenlik nedeniyle veya şifre değişikliği/sistem hatası kaynaklı izleme durduruldu.<br><br>
                            Lütfen uygulama üzerinden bilgilerinizi kontrol edip sistemi tekrar başlatın.
                        </div>
                        <div style="text-align: right; font-size: 12px; color: {OBISColors.TEXT_GHOST}; margin-top: 20px;">
                            ⏰ {zaman}
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
