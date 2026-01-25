"""
BU DOSYA: GitHub API kullanarak uygulamanın güncel sürümünü kontrol eder.
"""

import logging
import requests
from packaging import version
from typing import Dict, Optional

def check_for_updates(current_version_str: str, repo_owner: str = "basarob", repo_name: str = "OBIS-Notifier") -> Optional[Dict[str, str]]:
    """
    GitHub releases üzerinden en son sürümü kontrol eder.
    
    Args:
        current_version_str: Şu an çalışan uygulamanın versiyonu (örn: v2.1)
        repo_owner: GitHub repo sahibi
        repo_name: GitHub repo adı
        
    Returns:
        Güncelleme varsa dict döner, yoksa None.
    """
    try:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        response = requests.get(url, timeout=5) # 5 saniye timeout
        response.raise_for_status()
        
        latest_release = response.json()
        latest_tag = latest_release.get("tag_name", "v0.0.0")
        
        # 'v' harfini temizle ve anlamsal versiyonlama (Semantic Versioning) ile karşılaştır
        try:
            v_current = version.parse(current_version_str.lstrip("v"))
            v_latest = version.parse(latest_tag.lstrip("v"))
            
            if v_latest > v_current:
                return {
                    "version": latest_tag,
                    "url": latest_release.get("html_url"),
                    "body": latest_release.get("body", "")
                }
        except Exception:
            # Versiyon parse edilemezse, düz string olarak karşılaştır (Fallback)
            if latest_tag != current_version_str:
                 return {
                    "version": latest_tag,
                    "url": latest_release.get("html_url"),
                    "body": latest_release.get("body", "")
                }

    except Exception as e:
        logging.error(f"Güncelleme kontrolü başarısız: {e}")
    
    return None
