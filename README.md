# 📈 Rich-Tabanlı Terminal API İstemcisi

> **Hızlı bakış:**
>
> * 🖥️ Monokai temalı **Rich** CLI arabirimi
> * 🔐 **HMAC‑imzalı** REST çağrıları + JWT **token önbelleği / otomatik yenileme**
> * 🔄 **WebSocket** heartbeat & otomatik reconnect, ayrı canlı log penceresi
> * 📊 Menü tabanlı **Portföy / Hisse / Vadeli** endpoint işlemleri
> * ⏱️ Basit **rate‑limit** ve arka planda **session refresher**
> * 📜 Renkli JSON panelleri & zengin hata bildirimleri

---

## 📂 Projedeki Dosyalar

| Dosya / Dizin                | Açıklama                                                | Öne Çıkanlar                                          |
| ---------------------------- | ------------------------------------------------------- | ----------------------------------------------------- |
| **`terminal_app.py`**        | Uygulamanın giriş noktası                               | Tema, menüler, REST login, WS abonelik                |
| **`api_client.py`**          | REST & WS yardımcı sınıflar                             | HMAC imza, token saklama, throttle, session refresher |
| **`ws_logger.py`**           | WS mesajlarını ayrı ekranda izler                       | Renkli JSON paneli, zaman damgası                     |
| **`config.py`**              | Kullanıcı-parametreleri (🛑 **boş değerleri doldurun**) | API URL, anahtarlar, kullanıcı kimlik bilgileri       |
| `RapidSSL_TLS_RSA_CA_G1.crt` | Sunucunun ara sertifika zinciri                         | TLS doğrulaması için                                  |
| `requirements.txt`           | PIP bağımlılık listesi                                  | Python ≥ 3.10                                         |

---

## 🗺️ İçindekiler

1. [Özellikler](#özellikler)
2. [Gereksinimler](#gereksinimler)
3. [Kurulum](#kurulum)
4. [Yapılandırma](#yapılandırma)
5. [Kullanım](#kullanım)
6. [Geliştirici Notları](#geliştirici-notları)
7. [Sık Sorulanlar](#sık-sorulanlar)
8. [Katkı & Lisans](#katkı--lisans)

---

## ✨ Özellikler

|                      |                                                            |
| -------------------- | ---------------------------------------------------------- |
| 🎨 **Zengin Arayüz** | Monokai renk paleti, paneller, tablolar                    |
| 🔑 **Güvenli Giriş** | HMAC-SHA256 imzası + JWT token, SMS-OTP                    |
| 🕒 **Rate-Limit**    | İstek başına gecikme, 60 sn’de bir otomatik token yenileme |
| 🌐 **WebSocket**     | TLS, heartbeat paketi, kopmada otomatik bağlanma           |
| 📈 **Menü Akışı**    | Portföy, Hisse, Vadeli, WS abonelik menüleri               |
| 📑 **Renkli JSON**   | `json_panel()` ile kolay okunur REST/WS yanıtı             |
| 🪄 **Canlı WS Logu** | `ws_logger.py` gelen mesajları yeni konsolda gösterir      |

---

## ⚙️ Gereksinimler

```
Python 3.10+
rich        >= 13
requests    >= 2.32
websockets  >= 12
urllib3     >= 2
```

```bash
git clone https://github.com/BoraDurkun/Colendi-API-Python-Wrapper.git
cd Colendi-API-Python-Wrapper
# Linux/macOS
cp example.config.py config.py

# Windows (PowerShell/CMD)
copy example.config.py config.py
```

> **SSL Notu**
>
> > **SSL Notu**
> > Proje dizininde **`RapidSSL_TLS_RSA_CA_G1.crt`** dosyası *hazır* olarak sunulur; sunucu ara/kök sertifika zincirini paylaşmadığından bağlantı doğrulaması bu dosya üzerinden yapılır.
> > Dosya silinir veya bozulursa HTTPS/WS oturumu kurulamaz. Böyle bir durumda aynı zinciri yeniden indirip **aynı ada** (`RapidSSL_TLS_RSA_CA_G1.crt`) kaydedin ve `api_client.py` içinde `verify="RapidSSL_TLS_RSA_CA_G1.crt"` parametresinin yolu değişmediğinden emin olun.

---

## 🛠️ Yapılandırma

`config.py` içeriğini **mutlaka** müşterinizin API bilgileri ile doldurun:

```python
API_HOST   = "https://api.codyalgo.com:11443"
API_URL    = API_HOST
API_WS_URL = "wss://api.codyalgo.com:11443/ws"

API_KEY    = "🚀 public-key buraya"
API_SECRET = "🔑 secret-key buraya"
USERNAME   = "👤 kullanıcı_adı"
PASSWORD   = "🔒 şifre"

# Enum haritaları (gerekirse düzenleyin)
DIRECTION_MAP          = {1: "BUY", 2: "SELL"}
WEBSOCKET_SUBSCRIBE    = {1: "AddT", 2: "AddY", 3: "AddD"}
WEBSOCKET_UNSUBSCRIBE  = {1: "RemoveT", 2: "RemoveY", 3: "RemoveD"}
```

> `config.py` ve çalışma anında oluşan `api_settings.json` **.gitignore** içinde kalmalıdır.

---

## ▶️ Kullanım

```bash
python terminal_app.py
```

1. **API Bilgileri** ekranda görünür.
2. Kayıtlı token geçerliyse direkt giriş; değilse **OTP** akışı başlar.
3. Giriş başarılıysa **Ana Menü** gelir:

```
1) Portfolio Endpoints Menüsü
2) Stock Endpoints Menüsü
3) Future Endpoints Menüsü
4) WebSocket Abonelik Menüsü
*) Çıkış
```

### WebSocket Aboneliği

```
[1] Abone Ol      # AddT / AddY / AddD ...
[2] Abonelikten Çık  # RemoveT / RemoveY / RemoveD ...
```

* Mesaj tipini seçin
* Sembolleri virgülle ayırarak girin (`GARAN,AKBNK`)
* Başarılıysa ✓ onayı gelir; WS paketleri **ws\_logger** penceresine düşer.

---

## 🧑‍💻 Geliştirici Notları

* **Threading + asyncio** – WS ayrı daemon thread’de kendi event-loop’u ile çalışır.
* **Throttle** – `API.interval` (varsayılan 1 sn) her istekten önce bekler.
* **Loglama** – Tüm REST/WS olayları `logs.log` dosyasına INFO seviyesiyle yazılır.
* **Kod Stili** – `black --line-length 100` & `ruff` kullanmanız önerilir.

---

## ❓ Sık Sorulanlar

| Problem                          | Çözüm                                                                                                                       |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `SSL: CERTIFICATE_VERIFY_FAILED` | `RapidSSL_TLS_RSA_CA_G1.crt` yolunu ve CA zincirini doğrulayın.                                                             |
| `OTP yanıtında token yok`        | `USERNAME` / `PASSWORD` hatalı olabilir; broker hesabınızdaki SMS yetkisini kontrol edin.                                   |
| Sürekli `ConnectionClosed`       | Ağ kesintisi veya sunucu idle-timeout. Uygulama otomatik yeniden bağlanır; gerekirse `heartbeat_interval` değerini azaltın. |

---

## 🤝 Katkı & Lisans

* PR göndermeden önce **fork → branch → değişiklik → PR** adımlarını izleyin.
* PR açıklamasına “neyi, neden” değiştirdiğinizi yazın, mümkünse test ekleyin.

Bu proje **MIT** lisansı ile dağıtılmaktadır – ayrıntı için `LICENSE` dosyasına bakın.

---

> “Terminalin gücü, renklerin cazibesiyle buluştu.” ✨
