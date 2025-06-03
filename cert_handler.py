# cert_handler.py
import os
import tempfile
import requests
from dotenv import load_dotenv, set_key, dotenv_values
import logging

logger = logging.getLogger("cert_handler")

CERT_URL = "https://cacerts.digicert.com/RapidSSLTLSRSACAG1.crt.pem"
ENV_FILE = ".env"
ENV_KEY = "INTERMEDIATE_CERT_PATH"

def ensure_cert_in_env() -> str:
    """
    Sertifika dosyasını indir, geçici olarak kaydet ve .env içine yolunu yaz.
    """
    load_dotenv(ENV_FILE)
    pem_path = os.getenv(ENV_KEY)

    if pem_path and os.path.exists(pem_path):
        return pem_path

    try:
        response = requests.get(CERT_URL, timeout=10)
        response.raise_for_status()
        pem_text = response.text

        if "BEGIN CERTIFICATE" not in pem_text:
            raise ValueError("Geçersiz PEM içeriği")

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".pem") as f:
            f.write(pem_text)
            pem_path = f.name

        set_key(ENV_FILE, ENV_KEY, pem_path)
        return pem_path
    except Exception as e:
        logger.error(f"Sertifika indirilemedi: {e}")
        raise RuntimeError("Ara sertifika indirilemedi ve kayıt edilemedi.")


def cleanup_cert_from_env():
    """
    .env içindeki cert yolunu sil, geçici dosyayı da kaldır.
    """
    load_dotenv(ENV_FILE)
    pem_path = os.getenv(ENV_KEY)

    if pem_path and os.path.exists(pem_path):
        os.remove(pem_path)

    if os.path.exists(ENV_FILE):
        values = dotenv_values(ENV_FILE)
        if ENV_KEY in values:
            with open(ENV_FILE, "r") as f:
                lines = [line for line in f if not line.strip().startswith(f"{ENV_KEY}=")]
            with open(ENV_FILE, "w") as f:
                f.writelines(lines)
