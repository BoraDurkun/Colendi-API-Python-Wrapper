# Colendi API Python Wrapper

Colendi Menkul API icin HMAC imzali REST istemcisi, Rich tabanli terminal uygulamasi ve WebSocket yardimci sinifi.

Bu repo iki ana kullanim sunar:

- `terminal_app.py`: OTP login, portfoy, hisse, VIOP, fon ve WebSocket islemleri icin menu tabanli CLI.
- `api_client.py`: Python kodundan dogrudan kullanilabilen `API` ve `WebSocket` siniflari.

## Dosya Yapisi

| Dosya | Aciklama |
| --- | --- |
| `api_client.py` | HMAC imzali REST istemcisi, token saklama, throttle, session refresher ve WebSocket sinifi |
| `terminal_app.py` | Rich tabanli interaktif terminal uygulamasi |
| `config.py` | API URL, client key/secret, kullanici bilgileri ve CLI enum haritalari |
| `ws_logger.py` | WebSocket mesajlarini ayri pencerede izlemek icin yardimci logger |
| `api_settings.json` | Login sonrasi olusan JWT token cache dosyasi |

Not: `config.py` ve `api_settings.json` icinde hassas bilgi bulunabilir. Bu dosyalari paylasmadan once kontrol edin.

## Gereksinimler

- Python 3.10+
- `requests`
- `websockets`
- `rich`

Kurulum:

```bash
pip install -r requirements.txt
```

## Konfigurasyon

`config.py` icindeki alanlari doldurun:

```python
API_HOST = "https://api-client.colendimenkul.com/"
API_URL = API_HOST

CLIENT_KEY = "mail ile paylasilan client key"
CLIENT_SECRET = "mail ile paylasilan client secret"
USERNAME = "Colendi musteri numaraniz"
PASSWORD = "Colendi hesap sifreniz"
```

CLI menulerinde kullanilan enum degerleri de ayni dosyada tutulur:

```python
DIRECTION_MAP = {
    1: "Alis",
    2: "Satis",
    3: "AcigaSatis",
}

ORDER_METHOD_MAP = {
    1: "LMT",
    2: "PYS",
    3: "PKP",
    4: "MLM",
    5: "MPY",
}

ORDER_METHOD_DESCRIPTION_MAP = {
    "LMT": "Limitli",
    "PYS": "Piyasa",
    "PKP": "Piyasa En Iyi Fiyatli",
    "MLM": "MidPoint Limit Emir",
    "MPY": "MidPoint Piyasa Fiyatli emir (Gonderilmez ise LMT kabul edilir)",
}

ORDER_DURATION_MAP = {
    1: "Gunluk",
    2: "KalaniIptalEt",
    3: "IptalEdileneKadarGecerli",
    4: "TarihliEmir",
    5: "GerceklesmezseIptalEt",
    6: "DengeleyiciEmir",
    7: "KapanisSeansi",
}

ORDER_DURATION_DESCRIPTION_MAP = {
    "Gunluk": "GUN - Gunluk",
    "KalaniIptalEt": "KIE - Kalani Iptal Et",
    "IptalEdileneKadarGecerli": "IKG - Iptal Edilene Kadar Gecerli",
    "TarihliEmir": "TAR - Tarihli Emir",
    "GerceklesmezseIptalEt": "GIE - Gerceklesmezse Iptal Et",
    "DengeleyiciEmir": "IMB - Dengeleyici Emir",
    "KapanisSeansi": "KSN - Kapanis Seansi",
}
```

## Terminal Uygulamasini Calistirma

```bash
python terminal_app.py
```

Uygulama acilista API bilgilerini gosterir. Kayitli token varsa once onu dener; token gecersizse SMS OTP akisina gecer.

Ana menu:

```text
1) Hesap Bilgisi Menusu
2) Pay Emir Menusu
3) Vadeli Emir Menusu
4) Fon Emir Menusu
5) WebSocket Abonelik Menusu
*) Cikis
```

## Desteklenen REST Islemleri

### Authentication

| Metot | Endpoint |
| --- | --- |
| `send_otp(internet_user, password)` | `/Login/LoginSendOtp` |
| `login(otp_code, user_name=..., password=...)` | `/Login/LoginVerifyOtp` |

### Portfolio

| Metot | Endpoint |
| --- | --- |
| `get_portfolio_stock()` | `/Portfolio/PortfolioStock` |
| `get_portfolio_future()` | `/Portfolio/PortfolioFuture` |
| `get_portfolio_fund()` | `/Portfolio/PortfolioFund` |

### Stock

| Metot | Endpoint |
| --- | --- |
| `new_stock_order(...)` | `/Stock/NewStockOrder` |
| `update_stock_order(order_no, price)` | `/Stock/UpdateStockOrder` |
| `cancel_stock_order(order_no)` | `/Stock/CancelStockOrder` |
| `get_stock_orders(start_date=None)` | `/Stock/StockOrders` |
| `get_stock_order_detail(order_no)` | `/Stock/StockOrderDetail` |

`get_stock_orders` icin tarih parametresi Python tarafinda `datetime` olarak verilir:

```python
from datetime import datetime, timedelta

yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
orders = api.get_stock_orders(start_date=yesterday)
```

API bu tarihi request body icinde degil query string olarak bekler:

```text
POST /Stock/StockOrders?startDate=2026-06-24T00%3A00%3A00
body: {}
```

HMAC imzasi ise query string olmadan `/Stock/StockOrders` path'i uzerinden uretilir. Bu davranis `api_client.py` icindeki `_post` metodunda merkezi olarak ele alinir.

Geriye uyumluluk icin eski `startDate=` parametre adi da desteklenir:

```python
api.get_stock_orders(startDate=yesterday)
```

Yeni kodda `start_date=` kullanilmasi onerilir.

Hisse senedi emirleri icin durum kodlari:

| Durum Kodu | Karsiligi |
| --- | --- |
| `Y` | BIST'de |
| `Z` | Sistemde |
| `X` | Sistemde tahta kapali |
| `G` | Gerceklesen |
| `H` | Gun Iptal |
| `T` | Iptal |
| `R` | Red |

### Future

| Metot | Endpoint |
| --- | --- |
| `new_future_order(...)` | `/Future/NewFutureOrder` |
| `update_future_order(order_no, price)` | `/Future/UpdateFutureOrder` |
| `cancel_future_order(order_no)` | `/Future/CancelFutureOrder` |
| `get_future_orders()` | `/Future/FutureOrders` |
| `get_future_order_detail(order_no)` | `/Future/FutureOrderDetail` |

VIOP emirleri icin durum kodlari:

| Durum Kodu | Karsiligi |
| --- | --- |
| `Y` | BIST'de |
| `Z` | Sistemde |
| `G` | Gerceklesen |
| `H` | Gun Iptal |
| `T` | Iptal |
| `R` | Red |
| `S` | Askida |
| `K` | Risk Kontrolu |

### Fund

| Metot | Endpoint |
| --- | --- |
| `get_available_fund_list()` | `/Fund/AvaiableFundList` |
| `get_fund_orders()` | `/Fund/FundOrders` |
| `new_fund_order(fund_id, buy_sell, quantity, price)` | `/Fund/NewFundOrder` |
| `cancel_fund_order(order_no)` | `/Fund/CancelFundOrder` |

Fon emirleri icin durum kodlari:

| Durum Kodu | Karsiligi |
| --- | --- |
| `ES` | Gerceklesmeyi Bekliyor |
| `MK` | MKK Sisteminde |
| `IP` | Iptal Edildi |
| `OK` | Gerceklesti |

## Python Kodundan Kullanim

```python
from datetime import datetime, timedelta

from api_client import API
from config import API_URL, CLIENT_KEY, CLIENT_SECRET, USERNAME, PASSWORD

api = API.get_api(
    api_url=API_URL,
    api_key=CLIENT_KEY,
    secret_key=CLIENT_SECRET,
    verbose=True,
)

otp_response = api.send_otp(USERNAME, PASSWORD)
otp_code = input("SMS kodu: ")
login_response = api.login(otp_code, user_name=USERNAME, password=PASSWORD)

portfolio = api.get_portfolio_stock()

yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
stock_orders = api.get_stock_orders(start_date=yesterday)
```

Login basarili oldugunda access token `api_settings.json` dosyasina kaydedilir. Sonraki calistirmalarda istemci bu token'i yukler ve gecerliyse tekrar OTP istemeden devam eder.

## WebSocket

Terminal uygulamasinda WebSocket menusu `AddT`, `AddY`, `AddD` ve karsilik gelen `RemoveT`, `RemoveY`, `RemoveD` islemlerini `config.py` icindeki haritalardan okur.

Dogrudan kullanim ornegi:

```python
from api_client import WebSocket
from config import API_URL, CLIENT_KEY, CLIENT_SECRET

ws = WebSocket(
    api_url=API_URL,
    api_key=CLIENT_KEY,
    secret_key=CLIENT_SECRET,
    jwt_token="access token",
    heartbeat_interval=30,
    verbose=True,
)

ws.start()
```

`WebSocket` sinifi `/ws` path'i icin HMAC imzasi uretir, TLS ile baglanir, heartbeat gonderir ve baglanti kapanirsa yeniden baglanmayi dener.

## Loglama ve Oturum

- REST ve WebSocket olaylari `logs.log` dosyasina yazilir.
- `API.interval` varsayilan olarak `1` saniyedir ve istekler arasinda throttle uygular.
- Arka planda session refresher thread'i calisir ve yaklasik 270 saniyede bir `PortfolioStock` cagrisi yaparak oturumu canli tutar.
- `api_settings.json` token cache dosyasidir. Token gecersizse temizlenir ve yeniden OTP akisi gerekir.

## Gelistirme Notlari

- Wrapper tarafinda dis API alanlari camelCase olsa da Python public parametrelerinde snake_case tercih edilir.
- Geriye uyumluluk gereken yerlerde eski camelCase parametre adlari alias olarak tutulabilir.
- Query string kullanan endpointlerde HMAC imzasinin API'nin bekledigi canonical path ile hesaplandigindan emin olun.
- Degisikliklerden sonra en azindan su kontrolu calistirin:

```bash
python -m py_compile api_client.py terminal_app.py
```

## Lisans

Bu proje MIT lisansi ile dagitilir. Ayrinti icin `LICENSE` dosyasina bakin.
