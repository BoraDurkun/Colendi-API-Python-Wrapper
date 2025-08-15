import threading
import time
import hashlib
import hmac
import base64
import json
from typing import Any, Dict, Optional, Callable
import requests

import asyncio
from websockets.client import WebSocketClientProtocol # type: ignore
import websockets
import ssl
import os
import logging

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
    Singleton HMAC‐imzali REST API istemcisi.
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
        Tekil API nesnesini doner. İlk cagrida api_url, api_key, secret_key zorunludur.
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
        self._client_key  = api_key
        self._secret_key  = secret_key
        self._last_req = 0.0
        self.interval = 1 # İstekler arasinda kac saniye olsun
        

        # --- Token yukleme ve gecerlilik kontrolu (evvelden ekledigimiz) ---
        self._jwt_token = self._load_saved_token()
        if self._jwt_token:
            if self.verbose:
                logger.info(f"✅ Yuklendi: {self.TOKEN_FILE}")
            resp = self.get_subaccounts()
            stat = resp.get("statusCode", "status")
            
            if stat == 200:
                if self.verbose:
                    logger.info("✅ Kaydedilmis token gecerli.")
            else:
                if self.verbose:
                    logger.warning(f"❌ Kaydedilmis token gecersiz ({stat}), temizleniyor.")
                self._jwt_token = ""
                self._clear_saved_token()

        # --- AUTO SESSION REFRESH baslat ---
        self._start_session_refresher()

    # ————— HELPERS —————
        # ————— AUTO-SESSION REFRESH MEKANİZMASI —————
    def _start_session_refresher(self):
        """
        Arka planda daemon thread ile her 60 saniyede bir
        get_subaccounts() cagirip session'i yeniler.
        """
        thread = threading.Thread(target=self._session_refresher_loop, daemon=True)
        thread.start()

    def _session_refresher_loop(self):
        while True:
            time.sleep(60)
            if not self._jwt_token:
                # Henuz login olunmadiysa atla
                continue
            try:
                self.get_subaccounts()
                if self.verbose:
                    logger.info("🔄 Session refreshed via get_subaccounts()")
            except Exception as e:
                if self.verbose:
                    logger.warning(f"❌ Session refresh failed: {e}")

    # ——— Token helper’lari ———
    @classmethod
    def _load_saved_token(cls) -> str:
        # Dosya yoksa olustur ve bos token dondur
        if not os.path.isfile(cls.TOKEN_FILE):
            with open(cls.TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump({"jwtToken": ""}, f, ensure_ascii=False)
            return ""
        # Var olan dosyayi oku
        try:
            with open(cls.TOKEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("jwtToken", "")
        except Exception as e:
            # Hata varsa dosyayi sifirla
            logger.warning(f"Hata olustu: {e}. Token dosyasi sifirlaniyor.")
            with open(cls.TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump({"jwtToken": ""}, f, ensure_ascii=False)
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
            json.dump({"jwtToken": self._jwt_token}, f, ensure_ascii=False)
        
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
        Tum POST istekleri bu metot uzerinden gider.
        `require_auth=False` ise JWT header eklenmez.
        """
        path     = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        ts       = self._timestamp()
        body_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        sig      = self._make_signature(path, body_str, ts)

        headers = {
            "X-ClientKey": self._client_key,
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
        
        if self.verbose and resp.status_code == 200:
            logger.info(f"[POST] {path}  --> status {resp.status_code}, body={body_str}")
            logger.info(f"[RESP] {resp.json()}")            
            return resp.json()
        else:
            logger.error(f"[POST] {path}  --> status={resp.status_code}, resp={resp.content}")
            return {"status": resp.status_code}
        
    # ————— Authentication —————
    def send_otp(self, internet_user: str, password: str) -> Dict[str, Any]:
        """
        OTP gonderir. require_auth=False ile JWT header eklenmez.
        """
        return self._post("Identity/SendOtp",
                          {"internetUser": internet_user, "password": password},
                          require_auth=False)

    def login(self, token: str, otp: str) -> Dict[str, Any]:
        """
        SMS koduyla login olur ve JWT token’i kaydeder.
        """
        resp = self._post("Identity/Login",
                          {"token": token, "otp": otp},
                          require_auth=False)
        self._jwt_token = resp["data"]["jwtToken"]
        self._save_token()
        if self.verbose:
            logger.info("✅ Login successful, JWT token stored.")
        return resp

    # ————— Portfolio Endpoints —————
    def get_subaccounts(self) -> Dict[str, Any]:
        return self._post("Portfolio/SubAccounts", {})

    def get_account_summary(self, portfolio_number: int) -> Dict[str, Any]:
        return self._post("Portfolio/AccountSummary",
                          {"portfolioNumber": portfolio_number})

    def get_cash_assets(self, portfolio_number: int) -> Dict[str, Any]:
        return self._post("Portfolio/CashAssets",
                          {"portfolioNumber": portfolio_number})

    def get_cash_balance(self, portfolio_number: int) -> Dict[str, Any]:
        return self._post("Portfolio/CashBalance",
                          {"portfolioNumber": portfolio_number})

    def get_account_overall(self, portfolio_number: int) -> Dict[str, Any]:
        return self._post("Portfolio/AccountOverall",
                          {"portfolioNumber": portfolio_number})

    # ————— Stock Endpoints —————
    def get_stock_create_order(
        self,
        portfolio_number: int,
        equity_code: str,
        quantity: int,
        direction: str,
        price: float,
        order_method: str,
        order_duration: str,
        market_risk_approval: Optional[bool] = None
    ) -> Dict[str, Any]:
        payload = {
            "portfolioNumber": portfolio_number,
            "equityCode": equity_code,
            "quantity": quantity,
            "direction": direction,
            "price": price,
            "orderMethod": order_method,
            "orderDuration": order_duration,
        }

        if market_risk_approval is not None:
            payload["marketRiskApproval"] = market_risk_approval

        return self._post("Stock/StockCreateOrder", payload)

    def get_stock_replace_order(
        self,
        portfolio_number: int,
        order_ref: str,
        price:  float,
        quantity: int
    ) -> Dict[str, Any]:
        payload= {
            "portfolioNumber": portfolio_number,
            "orderRef": order_ref,
            "price" : price,
            "quantity": quantity
        }
        
        return self._post("Stock/StockReplaceOrder", payload)
                          
    def get_stock_delete_order(self, portfolio_number: int, order_ref: str) -> Dict[str, Any]:
        return self._post("Stock/StockDeleteOrder", {
            "portfolioNumber": portfolio_number,
            "orderRef":        order_ref
        })

    def get_stock_order_list(
        self,
        portfolio_number: int,
        order_status: Optional[str],
        order_direction: Optional[str],
        order_method: Optional[str],
        order_duration: Optional[str],
        equity_code: Optional[str],
        equity_type: Optional[str],
        page_number: int,
        descending_order: Optional[bool]
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "portfolioNumber":  portfolio_number,
            "pageNumber":       page_number
        }
        
        if order_status is not None:
            payload["orderStatus"] = order_status

        if order_direction is not None:
            payload["orderDirection"] = order_direction

        if order_method is not None:
            payload["orderMethod"] = order_method

        if order_duration is not None:
            payload["orderDuration"] = order_duration

        if equity_type is not None:
            payload["equityType"] = equity_type
            
        if equity_code is not None:
            payload["equityCode"] = equity_code

        if descending_order is not None:
            payload["descendingOrder"] = descending_order
            
        return self._post("Stock/StockOrderList", payload)

    def get_stock_positions(
        self,
        portfolio_number: int,
        equity_code: Optional[str],
        equity_type: Optional[str],
        without_depot: Optional[bool] = None,
        without_t1_qty: Optional[bool] = None
    ) -> Dict[str, Any]:
        
        payload: Dict[str, Any] = {
            "portfolioNumber": portfolio_number
        }           
        if equity_code is not None:
            payload["equityCode"] = equity_code

        if equity_type is not None:
            payload["equityType"] = equity_type   

        if without_depot is not None:
            payload["withOutDepot"] = without_depot
            
        if without_t1_qty is not None:
            payload["withOutT1Qty"] = without_t1_qty
            
        return self._post("Stock/StockPositions", payload)

    # ————— Future Endpoints —————
    def get_future_create_order(
        self,
        portfolio_number: int,
        contract_code: str,
        direction: str,
        price: float,
        quantity: int,
        order_method: str,
        order_duration: str,
        after_hour_session_valid: bool,
        expiration_date: str
    ) -> Dict[str, Any]:
        payload = {
            "portfolioNumber":       portfolio_number,
            "contractCode":          contract_code,
            "direction":             direction,
            "price":                 price,
            "quantity":              quantity,
            "orderMethod":           order_method,
            "orderDuration":         order_duration,
            "afterHourSessionValid": after_hour_session_valid,
            "expirationDate":        expiration_date
        }
        return self._post("Future/FutureCreateOrder", payload)

    def get_future_replace_order(
        self,
        portfolio_number: int,
        order_ref: str,
        quantity: int,
        price: float,
        order_type: str,
        expiration_date: str
    ) -> Dict[str, Any]:
        return self._post("Future/FutureReplaceOrder", {
            "portfolioNumber": portfolio_number,
            "orderRef":        order_ref,
            "quantity":        quantity,
            "price":           price,
            "orderType":       order_type,
            "expirationDate":  expiration_date
        })

    def get_future_delete_order(self, portfolio_number: int, order_ref: str) -> Dict[str, Any]:
        return self._post("Future/FutureDeleteOrder", {
            "portfolioNumber": portfolio_number,
            "orderRef":        order_ref
        })

    def get_future_order_list(
        self,
        portfolio_number: int,
        order_validity_date: Optional[str],
        contract_code: Optional[str],
        contract_type: Optional[str],
        long_short: Optional[str],
        pending_orders: Optional[bool],
        untransmitted_orders: Optional[bool],
        partially_executed_orders: Optional[bool],
        cancelled_orders: Optional[bool],
        after_hour_session_valid: Optional[bool]
    ) -> Dict[str, Any]:
        return self._post("Future/FutureOrderList", {
            "portfolioNumber":         portfolio_number,
            "orderValidityDate":       order_validity_date,
            "contractCode":            contract_code,
            "contractType":            contract_type,
            "longShort":               long_short,
            "pendingOrders":           pending_orders,
            "untransmittedOrders":     untransmitted_orders,
            "partiallyExecutedOrders": partially_executed_orders,
            "cancelledOrders":         cancelled_orders,
            "afterHourSessionValid":   after_hour_session_valid
        })

    def get_future_positions(self, portfolio_number: int) -> Dict[str, Any]:
        return self._post("Future/FuturePositions", {
            "portfolioNumber": portfolio_number
        })
              
class WebSocket:
    """
    HMAC imzali WebSocket baglantisi saglayan ve periyodik 'heartbeat' mesaji
    atan bir istemci sinifi.

    ozellikler:
      - Baglanti acildiginda otomatik reconnect.
      - Belirlenen aralikla ('heartbeat_interval') H tipi heartbeat gonderimi.
      - Gelen mesajlari istersen on_message callback’ine, istersen verbose modda console'a yazdirma.
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
          api_url           : REST API base URL (or. "https://api.example.com")
          api_key           : X-ClientKey basligi icin kullanilacak anahtar
          secret_key        : İmzalama icin HMAC secret
          jwt_token         : Yetkili JWT token (Bearer olmadan)
          heartbeat_interval: Kac saniyede bir heartbeat atilacagi
          verbose           : True ise loglama acik olur
        """
        # HTTP → WebSocket URL donusumu (wss/ws)
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

        # İc durum
        self._last_heartbeat = 0.0
        self._ws: Optional[WebSocketClientProtocol] = None

    def _timestamp(self) -> str:
        """su anki Unix timestamp'ini saniye cinsinden string olarak doner."""
        return str(int(time.time()))

    def _make_signature(self, path: str, body_str: str, timestamp: str) -> str:
        """
        HMAC-SHA256 imzasi olusturur ve base64 ile kodlar.

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
        WebSocket baglantisini baslatir, header'lari ekler ve
        alici/gonderici dongulerini tetikler.
        """
        path = '/ws'
        ts = self._timestamp()
        sig = self._make_signature(path, '', ts)

        headers = {
            'X-ClientKey': self._client_key,
            'Authorization': self._jwt_token,
            'X-Signature': sig,
            'X-Timestamp': ts,
        }

        # Ara sertifikayı içeren dosyanın yolu
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True

        # Baglantiyi ac
        self._ws = await websockets.connect(self.ws_url, ssl=ssl_context, additional_headers=headers)
        if self.verbose:
            logger.info(f"✅ WebSocket baglantisi kuruldu: {self.ws_url}")
        # Gelen mesajlari dinlemeye basla
        asyncio.create_task(self._receive_loop())
        # Periyodik heartbeat dongusunu baslat
        asyncio.create_task(self._send_loop())

    async def _receive_loop(self):
        """
        WebSocket uzerinden gelen her mesaji alir.
        Eger on_message callback atanmissa oraya, degilse verbose modda logger.info'e yollar.
        Baglanti kapanirsa otomatik reconnect dener.
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
                logger.info("🔄 Baglanti kapandi, yeniden baglaniliyor...")
            await self.connect()

    async def _send_loop(self):
        """
        Belirlenen interval kadar bekleyip her seferinde
        sadece H tipi heartbeat mesaji yollar.
        """
        assert self._ws is not None
        while True:
            now = time.time()
            if now - self._last_heartbeat >= self.heartbeat_interval:
                self._last_heartbeat = now
                # Heartbeat mesaji
                await self._send({
                    "Token": self._jwt_token,
                    "Type": "H",
                    "Symbols": []
                })
            # CPU kullanimini sinirlamak icin kisa uyku
            await asyncio.sleep(1)

    async def _send(self, payload: dict):
        """
        Verilen sozlugu JSON'a cevirir ve WebSocket uzerinden gonderir.
        """
        assert self._ws is not None
        msg = json.dumps(payload)
        await self._ws.send(msg)
        if self.verbose:
            logger.info("Gönderilen mesaj: %s", msg)


    def start(self):
        """
        Senkron olarak event loop baslatir ve connect() metodunu calistirir.
        """
        asyncio.get_event_loop().run_until_complete(self.connect())
