Aşağıda  istediğiniz iskelet ve biçimlendirme düzenine *bire bir* uyan, proje ayrıntılarınızı da dâhil eden güncel **README.md** metni yer alıyor. Dosyayı doğrudan kopyalayıp `README.md` olarak kaydedebilirsiniz.

```markdown
# 📈 Rich-Tabanlı Terminal Trading İstemcisi

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](#gereksinimler)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Rich](https://img.shields.io/badge/ui-rich-9B59B6?logo=python)](https://github.com/Textualize/rich)

> **Hızlı bakış:**
>
> * 🖥️ Monokai temalı **Rich** CLI  
> * 🔐 HMAC-imzalı **REST** + SMS-OTP oturum yönetimi  
> * 🔄 Otomatik **WebSocket** heartbeat & reconnect  
> * 📊 Portföy, Hisse, Vadeli işlem menüleri  
> * 📜 Renkli JSON & ayrı **WS log** konsolu  

---

## 📂 Projedeki Dosyalar

| Dosya / Dizin         | Açıklama                                | Öne Çıkanlar                                              |
|-----------------------|-----------------------------------------|-----------------------------------------------------------|
| **`terminal_app.py`** | Uygulamanın giriş noktası              | Tema, menüler, REST login, WS abonelik                    |
| **`api_client.py`**   | REST & WS yardımcı sınıflar            | HMAC imza, token saklama, throttle, session refresher     |
| **`ws_logger.py`**    | WS mesajlarını ayrı ekranda izler      | Renkli JSON paneli, zaman damgası                         |
| **`config.py`**       | Kullanıcı-parametreleri (🛑 **boş değerleri doldurun**) | API URL, anahtarlar, kullanıcı kimlik bilgileri |
| `rapidssl_chain.crt`  | Sunucunun ara sertifika zinciri        | TLS doğrulaması için                                     |
| `requirements.txt`    | PIP bağımlılık listesi                  | Python ≥ 3.10                                             |

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

|                         |                                                              |
|:------------------------|:-------------------------------------------------------------|
| 🎨 **Zengin Arayüz**    | Monokai renk paleti, paneller, tablolar                      |
| 🔑 **Güvenli Giriş**    | HMAC-SHA256 imzası + JWT token, SMS-OTP                       |
| 🕒 **Rate-Limit**       | İstek başına gecikme, 60 sn’de bir otomatik token yenileme    |
| 🌐 **WebSocket**        | TLS, heartbeat paketi, kopmada otomatik bağlanma             |
| 📈 **Menü Akışı**       | Portföy, Hisse, Vadeli, WS abonelik menüleri                 |
| 📑 **Renkli JSON**      | `json_panel()` ile kolay okunur REST/WS yanıtı                |
| 🪄 **Canlı WS Logu**     | `ws_logger.py` gelen mesajları yeni konsolda gösterir         |

---

## ⚙️ Gereksinimler

```

Python 3.10+
rich        >= 13
requests    >= 2.32
websockets  >= 12
urllib3     >= 2

````

```bash
# önerilen: sanal ortam
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

---

## 🚀 Kurulum

```bash
git clone https://github.com/your-org/terminal-trader.git
cd terminal-trader
cp example.config.py config.py   # şablonu düzenleyin
```

> **SSL Notu**
> Broker RapidSSL zinciri kullanıyorsa kök + ara sertifikaları
> `rapidssl_chain.crt` dosyasında birleştirin veya burada mevcut dosyayı güncelleyin.

---

## 🛠️ Yapılandırma

`config.py` içeriğini **mutlaka** müşterinizin API bilgileri ile doldurun:

```python
API_URL   = "https://api.broker.com"
API_KEY   = "🚀 public-key buraya"
API_SECRET= "🔑 secret-key buraya"

USERNAME  = "👤 kullanıcı_adı"
PASSWORD  = "🔒 şifre"

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
| `SSL: CERTIFICATE_VERIFY_FAILED` | `rapidssl_chain.crt` yolunu ve CA zincirini doğrulayın.                                                                     |
| `OTP yanıtında token yok`        | `USERNAME` / `PASSWORD` hatalı olabilir; broker hesabınızdaki SMS yetkisini kontrol edin.                                   |
| Sürekli `ConnectionClosed`       | Ağ kesintisi veya sunucu idle-timeout. Uygulama otomatik yeniden bağlanır; gerekirse `heartbeat_interval` değerini azaltın. |

---

## 🤝 Katkı & Lisans

* PR göndermeden önce **fork → branch → değişiklik → PR** adımlarını izleyin.
* PR açıklamasına “neyi, neden” değiştirdiğinizi yazın, mümkünse test ekleyin.

Bu proje **MIT** lisansı ile dağıtılmaktadır – ayrıntı için `LICENSE` dosyasına bakın.

---

> “Terminalin gücü, renklerin cazibesiyle buluştu.” ✨

```

> **Not:**  
> Yukarıdaki metin, siz zip dosyanızı incelerken tespit edilen tüm dizin / dosya adları ve işlevlerine göre düzenlendi. `config.py`’deki boş kimlik alanlarını doldurduğunuzdan emin olun; aksi hâlde uygulama açılışta duracaktır.
```
