# 📈 Rich-Tabanlı Terminal Trading İstemcisi

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python\&logoColor=white)](#gereksinimler)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Rich](https://img.shields.io/badge/ui-rich-9B59B6?logo=python)](https://github.com/Textualize/rich)

> **Hızlı bakış:**
>
> * 🖥️ Monokai temalı **zengin** (Rich) CLI
> * 🔐 HMAC-imzalı **REST** + SMS-OTP oturum yönetimi
> * 🔄 Otomatik **WebSocket** heartbeat & reconnect
> * 📊 Portföy, Hisse, Vadeli işlem menüleri
> * 📜 Renkli JSON & ayrı **WS log** konsolu

---

## 📂 Projedeki Dosyalar

| Dosya                | Açıklama                          | Öne Çıkanlar                                          |
| -------------------- | --------------------------------- | ----------------------------------------------------- |
| **terminal\_app.py** | Uygulamanın giriş noktası         | Tema, menüler, REST login, WS abonelik                |
| **api\_client.py**   | REST & WS yardımcı sınıflar       | HMAC imza, token saklama, throttle, session refresher |
| **ws\_logger.py**    | WS mesajlarını ayrı ekranda izler | Renkli JSON paneli, zaman damgası                     |

---

## 🗺️ İçindekiler

1. [Özellikler](#özellikler)
2. [Gereksinimler](#gereksinimler)
3. [Kurulum](#kurulum)
4. [Yapılandırma](#yapılandırma)
5. [Kullanım](#kullanım)
6. [Geliştirici Notları](#geliştirici-notları)
7. [Sık Sorulanlar](#sık-sorulanlar)
8. [Katkı](#katkı) & [Lisans](#lisans)

---

## ✨ Özellikler

|                                 |                                                            |
| :------------------------------ | :--------------------------------------------------------- |
| 🎨 **Zengin Arayüz**            | Monokai renk paleti, paneller, tablolar                    |
| 🔑 **Güvenli Kimlik Doğrulama** | HMAC-SHA256 + JWT token, SMS OTP                           |
| 🕒 **Rate-Limit & Yenileme**    | İstek başına gecikme, 60 sn’de bir otomatik token tazeleme |
| 🌐 **WebSocket İstemcisi**      | TLS, heartbeat paketi, kopmada otomatik bağlanma           |
| 📈 **Menü Tabanlı İş Akışı**    | Portföy, Hisse, Vadeli, WS abonelik menüleri               |
| 📑 **Renkli JSON Log**          | `json_panel()` ile tek komutla okunabilir çıktı            |
| 🪄 **Ayrı Log Konsolu**         | `ws_logger.py` WS mesajlarını canlı gösterir               |

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
# önerilen: sanal ortam
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Kurulum

```bash
git clone https://github.com/your-org/terminal-trader.git
cd terminal-trader
cp example.config.py config.py   # şablonu düzenleyin
```

> **SSL Notu**
> API’niz RapidSSL zinciri kullanıyorsa ara + kök sertifikaları
> `rapidssl_chain.crt` dosyasında birleştirin ve proje köküne koyun.

---

## 🛠️ Yapılandırma

`config.py` içeriği (kısaltılmış):

```python
API_URL   = "https://api.broker.com"
API_KEY   = "public-key"
API_SECRET= "super-secret"

USERNAME  = "internetUser"
PASSWORD  = "••••"

DIRECTION_MAP = {1: "BUY", 2: "SELL"}
WEBSOCKET_SUBSCRIBE   = {1: "AddT", 2: "AddY"}
WEBSOCKET_UNSUBSCRIBE = {1: "RemoveT", 2: "RemoveY"}
```

*Dosyayı `.gitignore`’a eklemeyi unutmayın.*

---

## ▶️ Kullanım

```bash
python terminal_app.py
```

1. **API Bilgileri** gösterilir.
2. Kayıtlı JWT varsa doğrulanır, yoksa **OTP** akışı başlar.
3. Başarılı login’den sonra **Ana Menü**:

```
1) Portfolio Endpoints Menüsü
2) Stock Endpoints Menüsü
3) Future Endpoints Menüsü
4) WebSocket Abonelik Menüsü
*) Çıkış
```

### WebSocket Aboneliği

```
[1] Abone Ol
[2] Abonelikten Çık
```

* Abonelik tipi (`AddT`, `RemoveY` …) seçin
* Sembolleri virgülle yazın → ✓ Başarılı mesaj

WS mesajları yeni açılan log penceresinde akar.

---

## 🧑‍💻 Geliştirici Notları

* **Threading + asyncio** – WS, ayrı daemon thread’e özel event-loop ile çalışır.
* **Throttle** – `API.interval` (varsayılan 1 sn) her POST arasında bekler.
* **Loglama** – Tüm REST & WS olayları `logs.log` (INFO) dosyasına yazılır.
* **Kod stili** –  `black --line-length 100`  &  `ruff` önerilir.

---

## ❓ Sık Sorulanlar

| Problem                          | Çözüm                                                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `SSL: CERTIFICATE_VERIFY_FAILED` | `rapidssl_chain.crt` yolunu kontrol edin, CA zincirini ekleyin.                                                     |
| `OTP yanıtında token yok`        | `USERNAME / PASSWORD` değerlerini doğrulayın.                                                                       |
| Sürekli `ConnectionClosed`       | Ağ kesintisi / sunucu idle timeout. Uygulama yeniden bağlanır; ihtiyaca göre `heartbeat_interval` değerini düşürün. |

---

## 🤝 Katkı

1. **Fork** → yeni branch → değişiklik → **Pull Request**
2. PR açıklamasında neyi, neden değiştirdiğinizi belirtin.
3. Test eklemeyi unutmayın.

---

## 📜 Lisans

Bu proje **MIT** lisansı ile dağıtılmaktadır – ayrıntılar için `LICENSE` dosyasına bakın.

---

> “Terminalin gücü, renklerin cazibesiyle buluştu.” ✨
