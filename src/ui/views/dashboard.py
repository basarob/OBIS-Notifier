"""
BU DOSYA: Ana kontrol paneli (DashboardController).
- QTimer ile geri sayım ve otomatik kontrol tetikleme
- QThread (CheckWorker) ile arka planda not kontrolü
- Olayların UI Componentlerine dağıtılması
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QTimer, pyqtSlot
import datetime
import json
import os
import logging
import winsound
from .dashboard_cards import DashboardControlCard, DashboardStatsCard, DashboardTimelineCard

# Servisler
from services.session import SessionManager
from utils.system import get_user_data_dir
from ui.utils.worker import CheckWorker
import qtawesome as qta

# Core import
try:
    from core.notifier import OBISNotifier
except ImportError:
    OBISNotifier = None

SETTINGS_FILE = os.path.join(get_user_data_dir(), "settings.json")


class DashboardView(QWidget):
    system_status_changed = pyqtSignal(bool)
    snackbar_signal = pyqtSignal(str, str)
    last_check_updated = pyqtSignal(str)  # Son kontrol zamanı ("HH:MM (Başarılı)")

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)
        layout.addWidget(self.content_widget)

        # --- Sistem Durumu ---
        self.is_system_running: bool = False
        self.check_count: int = 0
        self.notifier: OBISNotifier | None = None
        self.check_worker: CheckWorker | None = None
        self.is_checking: bool = False

        # --- Timer & Spam Koruma ---
        self.CHECK_INTERVAL: int = 20 * 60
        self.time_left: int = self.CHECK_INTERVAL
        self.last_manual_check_time: datetime.datetime | None = None
        self.toggle_timestamps: list = []
        self.toggle_block_until: datetime.datetime | None = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.setInterval(1000)

        self._setup_ui()

    def _setup_ui(self):
        # Üst Bölüm (Control & Stats)
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(20)

        self.control_card = DashboardControlCard()
        self.control_card.toggle_requested.connect(self._toggle_system)
        self.control_card.check_now_requested.connect(self._check_now)

        self.stats_card = DashboardStatsCard()

        top_layout.addWidget(self.control_card, stretch=2)
        top_layout.addWidget(self.stats_card, stretch=1)

        self.main_layout.addWidget(top_section)

        # Alt Bölüm (Timeline)
        self.timeline_card = DashboardTimelineCard()
        self.main_layout.addWidget(self.timeline_card, stretch=1)

    # ================= BADGE VE TIMER İLETİŞİMİ =================

    def _update_timer_label(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.control_card.update_timer_text(f"Sonraki Kontrol: {minutes:02}:{seconds:02}", is_active=True)

    def _reset_timer(self):
        self.timer.stop()
        self.control_card.update_timer_text("Sonraki Kontrol: --:--", is_active=False)

    # ================= SİSTEM BAŞLAT / DURDUR =================

    def _toggle_system(self):
        if self.toggle_block_until:
            if datetime.datetime.now() < self.toggle_block_until:
                remaining = (self.toggle_block_until - datetime.datetime.now()).seconds
                self.snackbar_signal.emit(f"Çok fazla deneme yaptınız. {remaining} sn bekleyin.", "warning")
                return
            else:
                self.toggle_block_until = None

        now = datetime.datetime.now()
        self.toggle_timestamps.append(now)
        cutoff = now - datetime.timedelta(seconds=30)
        self.toggle_timestamps = [t for t in self.toggle_timestamps if t > cutoff]

        if len(self.toggle_timestamps) > 4:
            self.toggle_block_until = now + datetime.timedelta(seconds=30)
            self.snackbar_signal.emit("Çok hızlı işlem yapıyorsunuz. Sistem 30 saniye kilitlendi.", "error")
            return

        self.control_card.btn_toggle.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.control_card.btn_toggle.setEnabled(True))

        if self.is_system_running:
            self._stop_system()
        else:
            self._start_system()

    def _start_system(self):
        credentials = SessionManager.load_session()
        if not credentials:
            self.snackbar_signal.emit("Oturum bilgileri bulunamadı. Lütfen tekrar giriş yapın.", "error")
            return

        student_id, password = credentials

        settings = self._load_settings_from_file()
        settings["student_id"] = student_id
        settings["obis_password"] = password
        settings["timeline_callback"] = self._on_timeline_from_worker

        check_interval_minutes = int(settings.get("check_interval", 20))
        self.CHECK_INTERVAL = check_interval_minutes * 60
        self.time_left = self.CHECK_INTERVAL

        try:
            self.notifier = OBISNotifier(settings)
        except Exception as e:
            self.snackbar_signal.emit(f"Sistem başlatılamadı: {str(e)}", "error")
            logging.error(f"OBISNotifier oluşturma hatası: {e}")
            return

        self.is_system_running = True
        self.check_count = 0

        # UI Güncelle
        self.control_card.update_badge_style(True)
        self.control_card.btn_toggle.setText(" Sistemi Durdur")
        self.control_card.btn_toggle.set_type("danger")
        self.control_card.btn_toggle.setIcon(qta.icon("fa5s.stop-circle", color="white"))

        self.timeline_card.add_item("Sistem başlatıldı. İlk kontrol hazırlanıyor...", "system")
        logging.info(f"Not kontrol sistemi başlatıldı. Kontrol aralığı: {check_interval_minutes} dk")
        self.snackbar_signal.emit("Sistem başarıyla başlatıldı!", "success")
        self.system_status_changed.emit(True)

        self._run_check()
        self._update_timer_label()
        self.timer.start()

    def _stop_system(self, auto_stopped: bool = False):
        self._reset_timer()
        self.notifier = None

        if self.check_worker and self.check_worker.isRunning():
            logging.info("Çalışan worker işlemi sonlanması bekleniyor...")
            try:
                self.check_worker.check_finished.disconnect()
            except TypeError:
                pass

        self.is_checking = False
        self.is_system_running = False

        self.control_card.update_badge_style(False)
        self.control_card.btn_toggle.setText(" Sistemi Başlat")
        self.control_card.btn_toggle.set_type("primary")
        self.control_card.btn_toggle.setIcon(qta.icon("fa5s.play", color="white"))

        if auto_stopped:
            self.timeline_card.add_item("Sistem otomatik olarak durduruldu!", "error")
            self.snackbar_signal.emit("Sistem ardışık hatalar nedeniyle durduruldu!", "error")
        else:
            self.timeline_card.add_item("Sistem kullanıcı tarafından durduruldu.", "system")
            self.snackbar_signal.emit("Sistem durduruldu.", "info")

        logging.info("Not kontrol sistemi durduruldu.")
        self.system_status_changed.emit(False)

    # ================= KONTROL DÖNGÜSÜ =================

    def _on_timer_tick(self):
        if not self.is_system_running:
            self._reset_timer()
            return
        self.time_left -= 1
        if self.time_left <= 0:
            if not self.is_checking:
                self._run_check()
            self.time_left = self.CHECK_INTERVAL
        self._update_timer_label()

    def _run_check(self):
        if self.is_checking:
            logging.warning("Zaten bir kontrol işlemi devam ediyor, atlanıyor.")
            return
        if not self.notifier:
            logging.error("Notifier başlatılmamış!")
            return

        self.is_checking = True
        self.check_count += 1
        self.stats_card.set_count(self.check_count)

        self.timeline_card.add_item(f"{self.check_count}. kontrol döngüsü başlatıldı.", "info")
        logging.info(f"====== {self.check_count}. KONTROL BAŞLATILDI ======")

        self.control_card.btn_check.setEnabled(False)
        self.control_card.btn_check.setText("Kontrol Ediliyor...")

        self.check_worker = CheckWorker(self.notifier)
        self.check_worker.check_finished.connect(self._on_check_finished)
        self.check_worker.start()

    @pyqtSlot(bool, bool, list, str, float)
    def _on_check_finished(self, success: bool, should_stop: bool, changes: list, message: str, elapsed: float):
        self.is_checking = False
        self.control_card.btn_check.setEnabled(True)
        self.control_card.btn_check.setText("Şimdi Kontrol Et")

        if not self.is_system_running:
            return

        if success:
            if changes:
                for change in changes:
                    ders_adi = change.get("ders", "Bilinmeyen Ders")
                    yeni = change.get("yeni", {})
                    sinavlar = yeni.get("Sınavlar", "-")
                    harf = yeni.get("Harf Notu", "-")
                    sonuc = yeni.get("Sonuç", "-")
                    
                    if change.get("eski"):
                        self.timeline_card.add_item(f"📝 {ders_adi} güncellendi — Sınavlar: {sinavlar} | Harf: {harf} | Sonuç: {sonuc}", "warn")
                    else:
                        self.timeline_card.add_item(f"🆕 {ders_adi} — Sınavlar: {sinavlar} | Harf: {harf} | Sonuç: {sonuc}", "warn")
                self.timeline_card.add_item(f"Bildirimler gönderildi. ({len(changes)} ders değişikliği)", "success")
                if message and "mail" in message.lower():
                    self.timeline_card.add_item("❌ E-Mail gönderme hatası: Bilgilerinizi kontrol ediniz.", "error")
                
                try:
                    winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    pass
            logging.info(f"{self.check_count}. kontrol başarıyla tamamlandı. (Süre: {elapsed:.1f} sn)")
        else:
            logging.warning(f"{self.check_count}. kontrol başarısız: {message} (Süre: {elapsed:.1f} sn)")
            if should_stop or "bulunamadı" in message.lower() or "hata" in message.lower():
                self.timeline_card.add_item(f"❌ {message}", "error")

        # Son kontrol zamanını topbar'a bildir
        now_str = datetime.datetime.now().strftime("%H:%M")
        status_text = "Başarılı" if success else "Başarısız"
        self.last_check_updated.emit(f"{now_str} ({status_text})")

        if should_stop:
            self._stop_system(auto_stopped=True)

    def _on_timeline_from_worker(self, message: str, msg_type: str):
        QTimer.singleShot(0, lambda: self.timeline_card.add_item(message, msg_type))

    # ================= ŞİMDİ KONTROL ET =================

    def _check_now(self):
        if not self.is_system_running:
            self.snackbar_signal.emit("Önce sistemi başlatmalısınız.", "error")
            return
        if self.is_checking:
            self.snackbar_signal.emit("Bir kontrol zaten devam ediyor.", "warning")
            return
        if self.time_left < 600:
            self.snackbar_signal.emit("Otomatik kontrole 10 dakikadan az kaldı, manuel kontrol gerekmez.", "warning")
            return
        if self.last_manual_check_time:
            elapsed = (datetime.datetime.now() - self.last_manual_check_time).total_seconds()
            if elapsed < 600:
                self.snackbar_signal.emit("Çok sık kontrol yapamazsınız. Lütfen bekleyin.", "warning")
                return

        self.last_manual_check_time = datetime.datetime.now()
        self.snackbar_signal.emit("Manuel kontrol başlatıldı.", "success")
        logging.info("Kullanıcı tarafından manuel kontrol tetiklendi.")
        self.timeline_card.add_item("Manuel kontrol başlatıldı (Kullanıcı tarafından)", "system")

        self.time_left = self.CHECK_INTERVAL
        self._update_timer_label()
        self._run_check()

    def _load_settings_from_file(self) -> dict:
        settings = {}
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
        except Exception as e:
            logging.error(f"Ayar dosyası okunamadı: {e}")

        for sensitive_key in ["obis_password", "student_id"]:
            if sensitive_key in settings:
                settings.pop(sensitive_key)
                logging.warning(f"Settings dosyasından güvenlik açığı temizlendi: {sensitive_key}")
                try:
                    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                        json.dump(settings, f, indent=4)
                except Exception:
                    pass
        return settings

    def force_stop(self):
        if self.is_system_running:
            self._reset_timer()
            self.notifier = None
            self.is_system_running = False
            self.is_checking = False
            self.control_card.update_badge_style(False)
            self.control_card.btn_toggle.setText(" Sistemi Başlat")
            self.control_card.btn_toggle.set_type("primary")
            self.control_card.btn_toggle.setIcon(qta.icon("fa5s.play", color="white"))
            self.system_status_changed.emit(False)
            logging.info("Sistem zorla durduruldu (logout/exit).")

    def reset_state(self):
        if self.is_system_running:
            self.force_stop()

        self.check_count = 0
        self.stats_card.set_count(0)
        self._reset_timer()
        self.time_left = self.CHECK_INTERVAL
        self.toggle_timestamps.clear()
        self.toggle_block_until = None
        self.last_manual_check_time = None
        
        self.timeline_card.clear()
        self.control_card.btn_check.setEnabled(True)
        self.control_card.btn_check.setText("Şimdi Kontrol Et")