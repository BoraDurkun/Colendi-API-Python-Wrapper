import threading
import time
import hashlib
import hmac
import base64
import json
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import requests

import asyncio
from websockets.client import WebSocketClientProtocol # type: ignore
import websockets
import ssl
import os
import logging
from urllib.parse import urlencode

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    filename='logs.log',          
    filemode='w',                       
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("api_client")

class API:
    """
    Singleton HMAC imzalı REST API istemcisi.
    """
    TOKEN_FILE = "api_settings.json"
    _instance: Optional["API"] = None
    _lock = threading.Lock()
    
    @classmethod
    def get_api(
        cls,
        *,
        api_url: str,
        api_key: str,
        secret_key: str,
        verbose: bool = True
    ) -> "API":
        """
        Tekil API nesnesini döner. İlk çağrıda api_url, api_key, secret_key zorunludur.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(
                    api_url=api_url,
                    api_key=api_key,
                    secret_key=secret_key,
                    verbose=verbose
                )
            return cls._instance

    def __init__(
        self,
        *,
        api_url: str,
        api_key: str,
        secret_key: str,
        verbose: bool
    ):
        self.verbose      = verbose
        self._api_url     = api_url.rstrip("/")
        self._client_key  = api_key.strip()
        self._secret_key  = secret_key.strip()
        self._last_req = 0.0
        self.interval = 1 # İstekler arasında kaç saniye olsun
        

        # --- Token yükleme ve geçerlilik kontrolü (evvelden eklediğimiz) ---
        self._jwt_token = self._load_saved_token()
        if self._jwt_token:
            if self.verbose:
                logger.info(f"✅ Yüklendi: {self.TOKEN_FILE}")
            resp = self.get_portfolio_stock()
            stat = resp.get("statusCode", "status")
            
            if stat == 200:
                if self.verbose:
                    logger.info("✅ Kaydedilmiş token geçerli.")
            else:
                if self.verbose:
                    logger.warning(f"❌ Kaydedilmiş token geçersiz ({stat}), temizleniyor.")
                self._jwt_token = ""
                self._clear_saved_token()

        # --- AUTO SESSION REFRESH başlat ---
        self._start_session_refresher()

    # ————— HELPERS —————
        # ————— AUTO-SESSION REFRESH MEKANİZMASI —————
    def _start_session_refresher(self):
        """
        Arka planda daemon thread ile her 270 saniyede bir
        PortfolioStock çağırıp session'ı yeniler.
        """
        thread = threading.Thread(target=self._session_refresher_loop, daemon=True)
        thread.start()

    def _session_refresher_loop(self):
        while True:
            time.sleep(270) # 4.5 dakika bekle
            if not self._jwt_token:
                # Henüz login olunmadıysa atla
                continue
            try:
                self.get_portfolio_stock()
                if self.verbose:
                    logger.info("Session refreshed via PortfolioStock")
            except Exception as e:
                if self.verbose:
                    logger.warning(f"❌ Session refresh failed: {e}")

    # ——— Token helper'ları ———
    @classmethod
    def _load_saved_token(cls) -> str:
        # Dosya yoksa oluştur ve boş token döndür
        if not os.path.isfile(cls.TOKEN_FILE):
            with open(cls.TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump({"accessToken": ""}, f, ensure_ascii=False)
            return ""
        # Var olan dosyayı oku
        try:
            with open(cls.TOKEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("accessToken") or data.get("jwtToken", "")
        except Exception as e:
            # Hata varsa dosyayı sıfırla
            logger.warning(f"Hata oluştu: {e}. Token dosyası sıfırlanıyor.")
            with open(cls.TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump({"accessToken": ""}, f, ensure_ascii=False)
            return ""

    @classmethod
    def _clear_saved_token(cls):
        try:
            import os
            os.remove(cls.TOKEN_FILE)
        except FileNotFoundError:
            pass

    def _save_token(self):
        with open(self.TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump({"accessToken": self._jwt_token}, f, ensure_ascii=False)
        
    def _timestamp(self) -> str:
        return str(int(time.time()))

    def _make_signature(
        self,
        path: str,
        body_str: str,
        timestamp: str
    ) -> str:
        raw = f"{self._client_key}|{path}|{body_str}|{timestamp}"
        mac = hmac.new(
            self._secret_key.encode("utf-8"),
            raw.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(mac).decode("utf-8")

    def _throttle(self):
        wait = (self._last_req + self.interval) - time.time()
        if wait > 0:
            time.sleep(wait)
        self._last_req = time.time()
        
    # ————— CORE REQUEST —————
    def _post(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        *,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Tüm POST istekleri bu metot üzerinden gider.
        `require_auth=False` ise JWT header eklenmez.
        """
        path     = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        sign_path = path.split("?", 1)[0]
        ts       = self._timestamp()
        body_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        sig      = self._make_signature(sign_path, body_str, ts)

        headers = {
            "X-ApiKey": self._client_key,
            "X-Timestamp": ts,
            "X-Signature": sig,
            "Content-Type": "application/json; charset=utf-8",
            "Accept":       "application/json; charset=utf-8",
        }
        if require_auth and self._jwt_token:
            headers["Authorization"] = f"Bearer {self._jwt_token}"

        self._throttle()
        url = f"{self._api_url}{path}"
        resp = requests.post(url, data=body_str.encode("utf-8"),
                             headers=headers, timeout=60)
        
        if resp.status_code == 200:
            data = resp.json()
            if self.verbose:
                logger.info(f"[POST] {path}  --> status {resp.status_code}, body={body_str}")
                logger.info(f"[RESP] {data}")
            return data

        try:
            data = resp.json()
        except ValueError:
            data = {"status": resp.status_code, "content": resp.text}

        if self.verbose:
            logger.error(f"[POST] {path}  --> status={resp.status_code}, resp={resp.content}")
        return data

    def _get(
        self,
        endpoint: str,
        *,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        GET istekleri bu metot üzerinden gider.
        Signature hesaplanırken body boş string olarak kullanılır.
        """
        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        ts = self._timestamp()
        sig = self._make_signature(path, "", ts)

        headers = {
            "X-ApiKey": self._client_key,
            "X-Timestamp": ts,
            "X-Signature": sig,
            "Accept": "application/json; charset=utf-8",
        }
        if require_auth and self._jwt_token:
            headers["Authorization"] = f"Bearer {self._jwt_token}"

        self._throttle()
        url = f"{self._api_url}{path}"
        resp = requests.get(url, headers=headers, timeout=60)

        if resp.status_code == 200:
            data = resp.json()
            if self.verbose:
                logger.info(f"[GET] {path}  --> status {resp.status_code}")
                logger.info(f"[RESP] {data}")
            return data

        try:
            data = resp.json()
        except ValueError:
            data = {"status": resp.status_code, "content": resp.text}

        if self.verbose:
            logger.error(f"[GET] {path}  --> status={resp.status_code}, resp={resp.content}")
        return data
        
    # ————— Authentication —————
    def send_otp(self, internet_user: str, password: str) -> Dict[str, Any]:
        """
        SMS Alma
        Bu endpoint, kullanıcı doğrulama işlemleri için kullanılmaktadır.
        Endpoint: /Login/LoginSendOtp
        İstek Değişkenleri:
        "userName": İnternet şubesi kullanıcı giriş bilgisi. String değer girilmelidir.
        "password": İnternet şubesi kullanıcı şifresi. String değer girilmelidir.
        """
        resp = self._post("/Login/LoginSendOtp",
                          {"userName": internet_user, "password": password},
                          require_auth=False)

        # SMS OTP'si kapatılmış kullanıcılar bu endpoint'ten doğrudan token
        # alabilir. Bu durumda LoginVerifyOtp çağrısı yapmadan oturumu kur.
        data = resp.get("data") or resp.get("Data") or {}
        access_token = data.get("accessToken") or data.get("AccessToken")
        if access_token:
            self._jwt_token = access_token
            self._save_token()
            if self.verbose:
                logger.info("LoginSendOtp yanıtından JWT token kaydedildi.")

        return resp

    def login(
        self,
        otp_code: str,
        *,
        user_name: str,
        password: str
    ) -> Dict[str, Any]:
        """
        SMS Doğrulama
        Bu endpoint, kullanıcı OTP doğrulama işlemleri için kullanılmaktadır.
        Endpoint: /Login/LoginVerifyOtp
        İstek Değişkenleri:
        "userName": İnternet şubesi kullanıcı giriş bilgisi. String değer girilmelidir.
        "password": İnternet şubesi kullanıcı şifresi. String değer girilmelidir.
        "otpCode": Kullanıcının kayıtlı telefon numarasına SMS ile gönderilen OTP doğrulama kodu. String değer girilmelidir.
        """
        resp = self._post("/Login/LoginVerifyOtp",
                          {
                              "userName": user_name,
                              "password": password,
                              "otpCode": otp_code
                          },
                          require_auth=False)
        data = resp.get("data") or resp.get("Data") or {}
        access_token = data.get("accessToken") or data.get("AccessToken")
        if not access_token:
            return resp
        self._jwt_token = access_token
        self._save_token()
        if self.verbose:
            logger.info("✅ Login successful, JWT token stored.")
        return resp

    # ————— Portfolio Endpoints —————
    def get_portfolio_stock(self) -> Dict[str, Any]:
        """
        Hisse Senedi Portföyü ve Nakit Akışı
        Bu endpoint, kullanıcı portföy nakit akışı ve limit bilgilerini görüntülemek için kullanılmaktadır.
        Endpoint: /Portfolio/PortfolioStock
        Bu endpoint için request body gönderilmez.
        """
        return self._get("Portfolio/PortfolioStock")

    def get_portfolio_future(self) -> Dict[str, Any]:
        """
        Viop Portföyü ve Viop Nakit Akışı
        Bu endpoint, kullanıcı VIOP portföy nakit akışı ve limitlerini görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Portfolio/PortfolioFuture
        Bu endpoint için request body gönderilmez.
        """
        return self._get("Portfolio/PortfolioFuture")

    def get_portfolio_fund(self) -> Dict[str, Any]:
        """
        Fon Portföyü ve Fon Nakit Akışı
        Bu endpoint, kullanıcı fon portföy nakit akışı ve limitlerini görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Portfolio/PortfolioFund
        Bu endpoint için request body gönderilmez.
        """
        return self._get("Portfolio/PortfolioFund")

    # ————— Stock Endpoints —————
    def new_stock_order(
        self,
        code: str,
        buy_sell: str,
        order_type: str,
        session: str,
        quantity: float,
        price: float,
        sub_market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hisse Senedi Yeni Emir İletim
        Bu endpoint, kullanıcı hisse senedi emir iletimi işlemleri için kullanılmaktadır.
        Endpoint: /Stock/NewStockOrder
        İstek Değişkenleri:
        "code": Hisse senedi sembolü. Örneğin: "THYAO"
        "buySell": İşlem yönü. Aşağıdaki değerlerden biri girilmelidir: "Alis", "Satis", "AcigaSatis".
        "orderType": Emir tipi. Aşağıdaki değerlerden biri girilmelidir: "LMT", "PYS", "PKP", "MLM", "MPY".
        "session": Emir geçerlilik/seans tipi. Aşağıdaki değerlerden biri girilmelidir: "Gunluk", "KalaniIptalEt", "IptalEdileneKadarGecerli", "TarihliEmir", "GerceklesmezseIptalEt", "DengeleyiciEmir", "KapanisSeansi".
        "quantity": Emir adedi. Sayısal değer girilmelidir.
        "price": Emir fiyatı. Sayısal değer girilmelidir. Piyasa emir tiplerinde 0 gönderilebilir.
        "subMarket": Alt pazar/risk bildirim tipi. Opsiyoneldir. Aşağıdaki değerlerden biri girilebilir: "AltPazar", "YipRiskBildirimFormu", "PoipRiskBildirimFormu".
        """
        payload: Dict[str, Any] = {
            "code": code,
            "buySell": buy_sell,
            "orderType": order_type,
            "session": session,
            "quantity": quantity,
            "price": price,
        }
        if sub_market:
            payload["subMarket"] = sub_market
        return self._post("Stock/NewStockOrder", payload)

    def update_stock_order(self, order_no: int, price: float) -> Dict[str, Any]:
        """
        Hisse Senedi Emir Düzeltme
        Bu endpoint, kullanıcı hisse senedi emir düzeltme işlemleri için kullanılmaktadır.
        Endpoint: /Stock/UpdateStockOrder
        İstek Değişkenleri:
        "orderNo": Düzenlenecek emrin numarası. Integer değer girilmelidir.
        "price": Emirin yeni fiyat bilgisi. Double değer girilmelidir.
        """
        return self._post("Stock/UpdateStockOrder", {
            "orderNo": order_no,
            "price": price
        })

    def cancel_stock_order(self, order_no: int) -> Dict[str, Any]:
        """
        Hisse Senedi Emir Silme
        Bu endpoint, kullanıcı hisse senedi emir silme işlemleri için kullanılmaktadır.
        Endpoint: /Stock/CancelStockOrder
        İstek Değişkenleri:
        "orderNo": Silinecek emrin numarası. Integer değer girilmelidir.
        """
        return self._post("Stock/CancelStockOrder", {"orderNo": order_no})

    def get_stock_orders(
        self,
        start_date: Optional[datetime] = None,
        *,
        startDate: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Hisse Senedi Emirleri
        Bu endpoint, kullanıcı günlük hisse senedi emirlerini görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Stock/StockOrders
        İstek Değişkenleri:
        "startDate": Emirlerin listeleneceği başlangıç tarihi. datetime tipinde değer girilmelidir.
        """
        selected_start_date = start_date if start_date is not None else startDate
        endpoint = "Stock/StockOrders"
        if selected_start_date is not None:
            endpoint = f"{endpoint}?{urlencode({'startDate': selected_start_date.isoformat()})}"
        return self._post(endpoint, {})

    def get_stock_order_detail(self, order_no: int) -> Dict[str, Any]:
        """
        Hisse Senedi Emir Detayı
        Bu endpoint, kullanıcı hisse senedi emir detaylarını görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Stock/StockOrderDetail
        İstek Değişkenleri:
        "orderNo": Detayı görüntülenecek emrin numarası. Integer değer girilmelidir.
        """
        return self._post("Stock/StockOrderDetail", {"orderNo": order_no})

    # ————— Future Endpoints —————
    def new_future_order(
        self,
        code: str,
        buy_sell: str,
        order_type: str,
        session: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """
        Viop Emir İletim
        Bu endpoint, kullanıcı VİOP emir iletimi işlemleri için kullanılmaktadır.
        Endpoint: /Future/NewFutureOrder
        İstek Değişkenleri:
        "code": VİOP sözleşme kodu. String değer girilmelidir.
        "buySell": İşlem yönü. Aşağıdaki değerlerden biri girilmelidir: "Uzun", "Kisa".
        "orderType": Emir tipi. Aşağıdaki değerlerden biri girilmelidir: "LMT", "PYS", "PKP", "MLM", "MPY".
        "session": Emir geçerlilik/seans tipi. Aşağıdaki değerlerden biri girilmelidir: "Gunluk", "KalaniIptalEt", "IptalEdileneKadarGecerli", "TarihliEmir", "GerceklesmezseIptalEt", "DengeleyiciEmir", "KapanisSeansi".
        "quantity": Emir adedi. Integer değer girilmelidir.
        "price": Emir fiyatı. Double değer girilmelidir. Piyasa emir tiplerinde 0 gönderilebilir.
        """
        return self._post("Future/NewFutureOrder", {
            "code": code,
            "buySell": buy_sell,
            "orderType": order_type,
            "session": session,
            "quantity": quantity,
            "price": price,
        })

    def update_future_order(self, order_no: int, price: float) -> Dict[str, Any]:
        """
        Viop Emir Düzeltme
        Bu endpoint, kullanıcı viop emir düzeltme işlemleri için kullanılmaktadır.
        Endpoint: /Future/UpdateFutureOrder
        İstek Değişkenleri:
        "orderNo": Düzenlenecek emrin numarası. Integer değer girilmelidir.
        "price": Emirin yeni fiyat bilgisi. Double değer girilmelidir.
        """
        return self._post("Future/UpdateFutureOrder", {
            "orderNo": order_no,
            "price": price
        })

    def cancel_future_order(self, order_no: int) -> Dict[str, Any]:
        """
        Viop Emir Silme
        Bu endpoint, kullanıcı hisse senedi emir silme işlemleri için kullanılmaktadır.
        Endpoint: /Future/CancelFutureOrder
        İstek Değişkenleri:
        "orderNo": Silinecek emrin numarası. Integer değer girilmelidir.
        """
        return self._post("Future/CancelFutureOrder", {"orderNo": order_no})

    def get_future_orders(self) -> Dict[str, Any]:
        """
        Viop Emirleri
        Bu endpoint, kullanıcı günlük hisse senedi emirlerini görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Future/FutureOrders
        Bu endpoint için request body gönderilmez.
        """
        return self._post("Future/FutureOrders", {})

    def get_future_order_detail(self, order_no: int) -> Dict[str, Any]:
        """
        Viop Emir Detayı
        Bu endpoint, kullanıcı viop emir detaylarını görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Future/FutureOrderDetail
        İstek Değişkenleri:
        "orderNo": Detayı görüntülenecek emrin numarası. Integer değer girilmelidir.
        """
        return self._post("Future/FutureOrderDetail", {"orderNo": order_no})

    # ------------------- Fund Endpoints -------------------
    def get_available_fund_list(self) -> Dict[str, Any]:
        """
        İşlem Yapılabilir Fon Listesi
        Bu endpoint, işlem yapılabilen TEFAS fonlarını görüntülemek için kullanılmaktadır.
        Endpoint: /Fund/AvaiableFundList
        Bu endpoint için request body gönderilmez.
        """
        return self._post("Fund/AvaiableFundList", {})

    def get_fund_orders(self) -> Dict[str, Any]:
        """
        Fon Emirleri
        Bu endpoint, kullanıcı günlük hisse senedi emirlerini görüntüleme işlemleri için kullanılmaktadır.
        Endpoint: /Stock/StockOrders
        Bu endpoint için request body gönderilmez.
        """
        return self._post("Fund/FundOrders", {})

    def new_fund_order(
        self,
        fund_id: int,
        buy_sell: str,
        quantity: float,
        price: float
    ) -> Dict[str, Any]:
        """
        Fon Emir İletim
        Bu endpoint, kullanıcı fon emir iletimi işlemleri için kullanılmaktadır.
        Endpoint: /Fund/NewFundOrder
        İstek Değişkenleri:
        "fundId": İşlem yapılacak fonun ID bilgisidir. Integer değer girilmelidir.
        "buySell": İşlem yönü. Aşağıdaki değerlerden biri girilmelidir: "Alis", "Satis".
        "quantity": Emir adedi/miktarı. Double değer girilmelidir.
        "price": Emir fiyatı/tutarı. Double değer girilmelidir.
        """
        return self._post("Fund/NewFundOrder", {
            "fundId": fund_id,
            "buySell": buy_sell,
            "quantity": quantity,
            "price": price
        })

    def cancel_fund_order(self, order_no: int) -> Dict[str, Any]:
        """
        Fon Emir Silme
        Bu endpoint, kullanıcı fon emir silme işlemleri için kullanılmaktadır.
        Endpoint: /Fund/CancelFundOrder
        İstek Değişkenleri:
        "orderNo": Silinecek emrin numarası. Integer değer girilmelidir.
        """
        return self._post("Fund/CancelFundOrder", {"orderNo": order_no})
              
class WebSocket:
    """
    HMAC imzalı WebSocket bağlantısı sağlayan ve periyodik 'heartbeat' mesajı
    atan bir istemci sınıfı.

    Özellikler:
      - Bağlantı açıldığında otomatik reconnect.
      - Belirlenen aralıkla ('heartbeat_interval') H tipi heartbeat gönderimi.
      - Gelen mesajları istersen on_message callback'ine, istersen verbose modda console'a yazdırma.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        secret_key: str,
        jwt_token: str,
        heartbeat_interval: int = 300,
        verbose: bool = True
    ):
        """
        Parametreler:
          api_url           : REST API base URL (ör. "https://api.example.com")
          api_key           : X-ClientKey başlığı için kullanılacak anahtar
          secret_key        : İmzalama için HMAC secret
          jwt_token         : Yetkili JWT token (Bearer olmadan)
          heartbeat_interval: Kaç saniyede bir heartbeat atılacağı
          verbose           : True ise loglama açık olur
        """
        # HTTP → WebSocket URL dönüşümü (wss/ws)
        self.ws_url = api_url.rstrip('/') \
            .replace('https://', 'wss://') \
            .replace('http://', 'ws://') + '/ws'

        self._client_key = api_key
        self._secret_key = secret_key
        self._jwt_token = jwt_token
        self.heartbeat_interval = heartbeat_interval
        self.verbose = verbose

        # callback placeholder
        self.on_message: Optional[Callable[[str], None]] = None

        # İç durum
        self._last_heartbeat = 0.0
        self._ws: Optional[WebSocketClientProtocol] = None

    def _timestamp(self) -> str:
        """Şu anki Unix timestamp'ini saniye cinsinden string olarak döner."""
        return str(int(time.time()))

    def _make_signature(self, path: str, body_str: str, timestamp: str) -> str:
        """
        HMAC-SHA256 imzası oluşturur ve base64 ile kodlar.

        İmza girdisi: "{client_key}|{path}|{body}|{timestamp}"
        """
        raw = f"{self._client_key}|{path}|{body_str}|{timestamp}"
        mac = hmac.new(
            self._secret_key.encode('utf-8'),
            raw.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(mac).decode('utf-8')

    async def connect(self):
        """
        WebSocket bağlantısını başlatır, header'ları ekler ve
        alıcı/gönderici döngülerini tetikler.
        """
        path = '/ws'
        ts = self._timestamp()
        sig = self._make_signature(path, '', ts)

        headers = {
            'X-ApiKey': self._client_key,
            'X-Timestamp': ts,
            'X-Signature': sig,
            'Authorization': self._jwt_token,
        }

        # Ara sertifikayı içeren dosyanın yolu
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True

        # Bağlantıyı aç
        self._ws = await websockets.connect(self.ws_url, ssl=ssl_context, additional_headers=headers)
        if self.verbose:
            logger.info(f"✅ WebSocket bağlantısı kuruldu: {self.ws_url}")
        # Gelen mesajları dinlemeye başla
        asyncio.create_task(self._receive_loop())
        # Periyodik heartbeat döngüsünü başlat
        asyncio.create_task(self._send_loop())

    async def _receive_loop(self):
        """
        WebSocket üzerinden gelen her mesajı alır.
        Eğer on_message callback atanmışsa oraya, değilse verbose modda logger.info'e yollar.
        Bağlantı kapanırsa otomatik reconnect dener.
        """
        assert self._ws is not None
        try:
            async for msg in self._ws:
                if callable(self.on_message):
                    self.on_message(msg)
                elif self.verbose:
                    logger.info("Gelen mesaj: %s", msg)
        except websockets.ConnectionClosed:
            if self.verbose:
                logger.info("🔄 Bağlantı kapandı, yeniden bağlanılıyor...")
            await self.connect()

    async def _send_loop(self):
        """
        Belirlenen interval kadar bekleyip her seferinde
        sadece H tipi heartbeat mesajı yollar.
        """
        assert self._ws is not None
        while True:
            now = time.time()
            if now - self._last_heartbeat >= self.heartbeat_interval:
                self._last_heartbeat = now
                # Heartbeat mesajı
                await self._send({
                    "Token": self._jwt_token,
                    "Type": "H",
                    "Symbols": []
                })
            # CPU kullanımını sınırlamak için kısa uyku
            await asyncio.sleep(1)

    async def _send(self, payload: dict):
        """
        Verilen sözlüğü JSON'a çevirir ve WebSocket üzerinden gönderir.
        """
        assert self._ws is not None
        msg = json.dumps(payload)
        await self._ws.send(msg)
        if self.verbose:
            logger.info("Gönderilen mesaj: %s", msg)


    def start(self):
        """
        Senkron olarak event loop başlatır ve connect() metodunu çalıştırır.
        """
        asyncio.get_event_loop().run_until_complete(self.connect())
