````markdown
# 📈 Rich-Tabanlı Terminal Trading İstemcisi

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](#kurulum)  
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)  
[![Rich](https://img.shields.io/badge/ui-rich-9B59B6?logo=python)](https://github.com/Textualize/rich)

> **Hızlı Bakış**  
> • Monokai temalı **Rich** CLI  
> • 🔐 HMAC-imzalı **REST** + SMS-OTP oturum yönetimi  
> • 🔄 Otomatik **WebSocket** heartbeat & reconnect  
> • 📊 Portföy / Hisse / Vadeli menüleri  
> • 📜 Renkli JSON & ayrı **WS log** konsolu  

---

## 📁 Proje Yapısı

| Dosya / Dizin           | Açıklama                                                      |
|-------------------------|--------------------------------------------------------------|
| `console_app.py`        | Uygulamanın **giriş noktası** – menüler, REST login, WS UI    |
| `api_client.py`         | REST + WS yardımcı sınıflar (HMAC, throttle, token saklama)   |
| `config.py`             | **Boş kimlik alanları** bulunan yapılandırma dosyası          |
| `ws_logger.py`          | WebSocket mesajlarını ayrı konsolda renkli olarak gösterir    |
| `rapidssl_chain.crt`    | Sunucuya ait **ara sertifika** zinciri                       |
| `requirements.txt`      | Pip bağımlılıkları                                           |
| `.gitattributes`, `.gitignore` | Git yardımcı dosyaları                              |
| `LICENSE`               | MIT lisansı                                                  |

---

## ✨ Özellikler

| | |
|:-|:-|
| 🎨 **Zengin Arayüz** | Monokai renk paleti, paneller, tablolar |
| 🔑 **Güvenli Kimlik Doğrulama** | HMAC-SHA256 imzası + JWT token, SMS-OTP |
| 🕒 **Rate-Limit & Yenileme** | İstek başına bekleme, 60 s’de bir otomatik token tazeleme |
| 🌐 **WebSocket İstemcisi** | TLS, `heartbeat` paketi, kopmada otomatik bağlanma |
| 🪄 **Ayrı Log Konsolu** | `ws_logger.py` gelen WS mesajlarını canlı gösterir |

---

## ⚙️ Gereksinimler

```text
Python 3.10+
rich        >= 13
requests    >= 2.32
websockets  >= 12
urllib3     >= 2
````

---

## 🚀 Kurulum

```bash
git clone https://github.com/your-org/terminal-trader.git
cd terminal-trader

# Sanal ortam (önerilir)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### SSL Sertifikası

Broker’ın sunucusu RapidSSL zinciri kullanıyorsa kök + ara sertifikalar **rapidssl\_chain.crt** dosyasında hazırdır. Gerekirse kendi zincirinizi aynı dosya adına yazarak değiştirin.

---

## 🔐 Yapılandırma (❗ Zorunlu)

1. `config.py` dosyasını açın.
2. Aşağıdaki alanları **müşterinizin API kimlik bilgileri** ile doldurun:

```python
API_KEY    = "🚀 public key buraya"
API_SECRET = "🔑 secret key buraya"
USERNAME   = "👤 internet kullanıcı adı"
PASSWORD   = "🔒 şifre"
```

> Boş bırakırsanız uygulama başlarken hata verir ve kapanır.

3. Gerekirse `API_HOST`/`API_URL`/`API_WS_URL` değerlerini değiştirin.

Kimlik bilgileri sadece yerel makinenizde saklanır; Git’e **asla** commit etmeyin.

---

## ▶️ Çalıştırma

```bash
python console_app.py
```

1. **API bilgileri** ekranda görünür.
2. Kayıtlı bir `api_settings.json` dosyası varsa token doğrulanır; yoksa **OTP** akışı başlar:

   * “SMS kodu:” prompt’una gelen kodu girin.
3. Başarılı girişten sonra **Ana Menü** açılır:

```
1) Portfolio Endpoints Menüsü
2) Stock Endpoints Menüsü
3) Future Endpoints Menüsü
4) WebSocket Abonelik Menüsü
*) Çıkış
```

### WebSocket Abonelik Akışı

```
[1] Abone Ol   •  AddT / AddD / AddY
[2] Abonelikten Çık •  RemoveT / RemoveY / RemoveD
```

* İstenen mesaj tipini seçin.
* Sembolleri virgülle ayırarak girin (`GARAN,AKBNK` …).
* Başarılı işlem ✓ ile onaylanır.
* Tüm gelen WS paketleri yeni açılan **ws\_logger** penceresine akar.

---

## 🛠️ Geliştirici Notları

* **Threading + asyncio** – WebSocket ayrı daemon thread içinde kendi event-loop’una sahiptir.
* **Throttle** – `API.interval` (varsayılan `1 s`) her çağrı arasında bekler.
* **Token saklama** – JWT, `api_settings.json` dosyasında AES’siz düz metin olarak tutulur; güvenlik modeli kendi sorumluluğunuzdadır.
* **Kod stili** – `black --line-length 100` & `ruff` ile uyumlu.

---

## ❓ Sık Sorulanlar

| Problem                          | Çözüm                                                                                                                         |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `SSL: CERTIFICATE_VERIFY_FAILED` | `rapidssl_chain.crt` yolunu ve içerdiği CA zincirini kontrol edin.                                                            |
| `OTP yanıtında token yok`        | `USERNAME` / `PASSWORD` hatalı olabilir; broker hesabınızı kontrol edin.                                                      |
| Sürekli `ConnectionClosed`       | Ağ kesintisi veya sunucu ‘idle timeout’. Uygulama otomatik yeniden bağlanır; gerekirse `heartbeat_interval` değerini düşürün. |

---

## 🤝 Katkı

1. **Fork** → yeni branch → değişiklik → **Pull Request**
2. PR açıklamasında neyi, neden değiştirdiğinizi belirtin.
3. Test eklemeyi unutmayın.

---

## 📜 Lisans

Bu proje **MIT** lisansı ile dağıtılmaktadır – ayrıntılar için `LICENSE` dosyasına bakın.

---

> *“Terminalin gücü, renklerin cazibesiyle buluştu.”* ✨

```
```
