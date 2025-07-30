obis_mail = 'ogrencino@stu.adu.edu.tr'
obis_sifre = 'sifreniz'
yariyil = '24/25 Bahar'

use_email = True
alici_email = 'mailiniz'

use_telegram = False
telegram_bot_token = 'bot_token'
telegram_chat_id = 'chat_id'

tarayici = 'chromium'
gorunurluk = True
sure = 30

gonderen_email = 'obisnotifier@gmail.com'
gonderen_password = 'egsh hdpo wrum cxte'


"""
Yapılandırma Bilgisi (TR)
----------------------------
- yariyil (Dönem) formatı: '../.. Güz' veya '../.. Bahar' şeklinde olmalıdır.

- use_email veya use_telegram formatı  tercihinize göre True/False olarak ayarlanmalıdır.

- tarayici seçimi: 'chromium' (Chrome), 'firefox' (Firefox), 'webkit' (Safari) olarak ayarlanabilir.

- Tarayıcının görünmesini istiyorsanız: gorunurluk = False (headless mod için True)

- Notların kaç dakikada bir kontrol edileceğini 'sure' ile ayarlayın. Örn: sure = 30 (Çok kısa olması önerilmez!)

- Varsayılan olarak ayarlanmış gönderici mailini kullanmak istemiyorsanız, 
gonderen_email ve gonderen_password alanlarını kendinize göre yapılandırın.

Configuration Info (EN)
----------------------------
- yariyil (Semester) format must be: '../.. Güz' or '../.. Bahar'

- tarayici (Browser) selection can be set to: 'chromium' (Chrome), 'firefox' (Firefox), or 'webkit' (Safari)

- The use_email or use_telegram format should be set to True/False according to your preference.

- If you want the browser to be visible: gorunurluk = False (True for headless mode)

- Set how often grades are checked (in minutes) using 'sure'. Example: sure = 30 (Too short is not recommended!)

- If you do not want to use the default sender email address, configure the sender_email and sender_password fields accordingly.
"""