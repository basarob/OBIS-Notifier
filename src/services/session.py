"""
BU DOSYA: Oturum bilgilerini güvenli bir şekilde saklamak
ve yönetmekten sorumludur. Windows Credential Manager 
(keyring) altyapısını kullanır.
"""

import os
import json
import keyring
import logging
from typing import Optional, Tuple

# Sabitler
APP_NAME = "OBISNotifier"
APPDATA_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'OBISNotifier')
SESSION_FILE = os.path.join(APPDATA_DIR, 'session.json')

class SessionManager:
    """
    Kullanıcı adı ve şifreyi yöneten güvenli sınıf.
    Şifreleri 'keyring' ile işletim sistemi kasasında,
    kullanıcı adını ise JSON dosyasında tutar.
    """

    @staticmethod
    def save_session(student_id: str, password: str) -> bool:
        """
        Oturumu kaydeder.
        
        Args:
            student_id: Öğrenci numarası
            password: Şifre
            
        Returns:
            Başarılı ise True
        """
        try:
            # 1. Şifreyi güvenli kasaya at
            try:
                keyring.set_password(APP_NAME, student_id, password)
            except Exception as e:
                logging.error(f"Kasa (Keyring) erişim hatası: {e}")
            
            # 2. Öğrenci numarasını dosyaya yaz (Son kullanıcıyı hatırlamak için)
            if not os.path.exists(APPDATA_DIR):
                os.makedirs(APPDATA_DIR)
                
            data = {"last_user": student_id}
            
            with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
                
            logging.info(f"Oturum kaydedildi: {student_id}")
            return True
            
        except Exception as e:
            logging.error(f"Oturum kaydedilemedi: {e}")
            return False

    @staticmethod
    def load_session() -> Optional[Tuple[str, str]]:
        """
        Kayıtlı oturumu yükler.
        
        Returns:
            (student_id, password) tuple'ı veya None
        """
        if not os.path.exists(SESSION_FILE):
            return None
            
        try:
            # 1. Son kullanıcıyı öğren
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user = data.get("last_user")
                
            if not user:
                return None
                
            # 2. Şifreyi kasadan iste
            try:
                password = keyring.get_password(APP_NAME, user)
            except Exception as e:
                logging.error(f"Kasa (Keyring) okuma hatası: {e}")
                return None
            
            if password:
                return (user, password)
            else:
                logging.warning("Kullanıcı bulundu ama şifre kasada yok.")
                return None
                
        except Exception as e:
            # Dosya bozuk olabilir, temizle
            logging.error(f"Oturum yüklenirken hata: {e}")
            return None

    @staticmethod
    def clear_session() -> None:
        """Kayıtlı oturumu tamamen siler."""
        try:
            user = None
            # Şu anki kayıtlı kullanıcıyı bul
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        user = data.get("last_user")
                    except json.JSONDecodeError:
                        pass
                
                # Dosyayı sil
                os.remove(SESSION_FILE)

            # Kasadan sil
            if user:
                try:
                    keyring.delete_password(APP_NAME, user)
                except (keyring.errors.PasswordDeleteError, Exception):
                    pass # Zaten silinmiş olabilir veya erişim yok
            
            logging.info("Oturum temizlendi.")
                
        except Exception as e:
            logging.error(f"Oturum silinirken hata: {e}")