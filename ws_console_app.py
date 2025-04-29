import os
import sys
import subprocess
import time
import threading
import asyncio

from dotenv import load_dotenv, find_dotenv
from api_client import API, WebSocket

def start_ws_loop(ws: WebSocket):
    """
    Arka planda kendi WS instance'ımızı ayağa kaldıracak loop.
    Bu sadece heartbeat + gönderimler için.
    """
    loop = asyncio.new_event_loop()
    ws._loop = loop
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws.connect())
    loop.run_forever()

def main():
    # ——— 1) Ortamı yükle & REST login ———
    load_dotenv(find_dotenv())
    API_URL    = os.getenv("API_URL")
    API_KEY    = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    USERNAME   = os.getenv("USERNAME")
    PASSWORD   = os.getenv("PASSWORD")

    api = API.get_api(
        api_url    = API_URL,
        api_key    = API_KEY,
        secret_key = API_SECRET,
        verbose    = True
    )
    otp_resp = api.send_otp(USERNAME, PASSWORD)
    token    = otp_resp["data"]["token"]
    print("✅ OTP gönderildi, token:", token)
    code = input("SMS kodunu girin: ").strip()
    api.login(token, code)
    print("✅ Login başarılı, JWT_TOKEN alındı.")

    # ——— 2) Aynı JWT ile ws_logger.py'yi ayrı pencerede çalıştır ———
    env = os.environ.copy()
    env["JWT_TOKEN"] = api._jwt_token
    python_exe = sys.executable
    base_dir   = os.path.dirname(__file__)
    ws_logger  = os.path.join(base_dir, "ws_logger.py")

    subprocess.Popen(
        [python_exe, ws_logger],
        creationflags=subprocess.CREATE_NEW_CONSOLE,  # Windows
        env=env
    )
    print("▶️ WS log’ları için ayrı pencere açıldı.")

    # ——— 3) Kendi WS client’ımızı başlat (subscribe/unsubscribe için) ———
    ws = WebSocket(
        api_url            = API_URL,
        api_key            = API_KEY,
        secret_key         = API_SECRET,
        jwt_token          = api._jwt_token,
        heartbeat_interval = 300,
        verbose            = False   # loglamayı ws_logger’a bırakıyoruz
    )

    t = threading.Thread(target=start_ws_loop, args=(ws,), daemon=True)
    t.start()
    time.sleep(1)  # bağlantının kurulması için kısa bekle

    # ——— 4) Menü ———
    while True:
        print("\n=== WebSocket Abonelik Menüsü ===")
        print("1) subscribe   (AddT/AddY/AddD)")
        print("2) unsubscribe (RemoveT/RemoveY/RemoveD)")
        print("0) exit")
        sel = input("Seçiminiz: ").strip()

        if sel == '0':
            print("Çıkış yapılıyor…")
            ws._loop.call_soon_threadsafe(ws._loop.stop)
            break

        if sel in ('1', '2'):
            is_sub = (sel == '1')
            msg_type = input("Mesaj tipi (örn. AddT, AddY, AddD ya da RemoveT…): ").strip()
            syms = input("Semboller (virgülle ayrılmış): ").split(",")
            payload = {
                "Token":   ws._jwt_token,
                "Type":    msg_type,
                "Symbols": [s.strip() for s in syms if s.strip()]
            }

            fut = asyncio.run_coroutine_threadsafe(ws._send(payload), ws._loop)
            try:
                fut.result(timeout=5)
            except Exception as e:
                print("⚠️ Gönderim hatası:", e)
            else:
                action = "Abone olundu" if is_sub else "Abonelik iptal edildi"
                print(f"✅ {action}: {payload}")

        else:
            print("Geçersiz seçim, tekrar deneyin.")

if __name__ == "__main__":
    main()
