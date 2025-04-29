import threading
import time
import hashlib
import hmac
import base64
import json
from typing import Any, Dict, Optional, Callable
import requests
import asyncio
import websockets

class API:
    """
    Singleton HMAC‐imzalı REST API istemcisi.
    """

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
        self._api_url     = api_url.rstrip("/")      # Örneğin "https://api.example.com"
        self._client_key  = api_key
        self._secret_key  = secret_key
        self._jwt_token   = ""                        # login sonrası dolacak
        self._last_req    = 0.0                       # saniyede 1 istek throttle

    # ————— HELPERS —————
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
        wait = (self._last_req + 1) - time.time()
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
        resp = requests.post(url, data=body_str.encode("utf-8"), headers=headers, timeout=15)
        resp.raise_for_status()
        if self.verbose:
            print(f"[POST] {path} → status {resp.status_code}, body={body_str}")
        return resp.json()

    # ————— Authentication —————
    def send_otp(self, internet_user: str, password: str) -> Dict[str, Any]:
        """
        OTP gönderir. require_auth=False ile JWT header eklenmez.
        """
        return self._post("Identity/SendOtp",
                          {"InternetUser": internet_user, "Password": password},
                          require_auth=False)

    def login(self, token: str, otp: str) -> Dict[str, Any]:
        """
        SMS koduyla login olur ve JWT token’ı kaydeder.
        """
        resp = self._post("Identity/Login",
                          {"token": token, "otp": otp},
                          require_auth=False)
        self._jwt_token = resp["data"]["jwtToken"]
        if self.verbose:
            print("✅ Login successful, JWT token stored.")
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
        direction: int,
        price: int,
        order_method: int,
        order_duration: int,
        market_risk_approval: bool
    ) -> Dict[str, Any]:
        payload = {
            "portfolioNumber":    portfolio_number,
            "equityCode":         equity_code,
            "quantity":           quantity,
            "direction":          direction,
            "price":              price,
            "orderMethod":        order_method,
            "orderDuration":      order_duration,
            "marketRiskApproval": market_risk_approval,
        }
        return self._post("Stock/StockCreateOrder", payload)

    def get_stock_replace_order(
        self,
        portfolio_number: int,
        order_ref: str,
        price: int,
        quantity: int
    ) -> Dict[str, Any]:
        return self._post("Stock/StockReplaceOrder", {
            "portfolioNumber": portfolio_number,
            "orderRef":        order_ref,
            "price":           price,
            "quantity":        quantity
        })

    def get_stock_delete_order(self, portfolio_number: int, order_ref: str) -> Dict[str, Any]:
        return self._post("Stock/StockDeleteOrder", {
            "portfolioNumber": portfolio_number,
            "orderRef":        order_ref
        })

    def get_stock_order_list(
        self,
        portfolio_number: int,
        order_status: int,
        order_direction: int,
        order_method: int,
        order_duration: int,
        equity_code: str,
        equity_type: int,
        page_number: int,
        descending_order: bool
    ) -> Dict[str, Any]:
        return self._post("Stock/StockOrderList", {
            "portfolioNumber":  portfolio_number,
            "orderStatus":      order_status,
            "orderDirection":   order_direction,
            "orderMethod":      order_method,
            "orderDuration":    order_duration,
            "equityCode":       equity_code,
            "equityType":       equity_type,
            "pageNumber":       page_number,
            "descendingOrder":  descending_order
        })

    def get_stock_positions(
        self,
        portfolio_number: int,
        equity_code: str,
        equity_type: int,
        without_depot: bool,
        without_t1_qty: bool
    ) -> Dict[str, Any]:
        return self._post("Stock/StockPositions", {
            "portfolioNumber": portfolio_number,
            "equityCode":      equity_code,
            "equityType":      equity_type,
            "withOutDepot":    without_depot,
            "withOutT1Qty":    without_t1_qty
        })

    # ————— Future Endpoints —————
    def get_future_create_order(
        self,
        portfolio_number: int,
        contract_code: str,
        direction: int,
        price: int,
        quantity: int,
        order_method: int,
        order_duration: int,
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
        price: int,
        order_type: int,
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
        order_validity_date: str,
        contract_code: str,
        contract_type: int,
        long_short: int,
        pending_orders: bool,
        untransmitted_orders: bool,
        partially_executed_orders: bool,
        cancelled_orders: bool,
        after_hour_session_valid: bool
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
    HMAC imzalı WebSocket bağlantısı sağlayan ve periyodik 'heartbeat' mesajı
    atan bir istemci sınıfı.

    Özellikler:
      - Bağlantı açıldığında otomatik reconnect.
      - Belirlenen aralıkla ('heartbeat_interval') H tipi heartbeat gönderimi.
      - Gelen mesajları istersen on_message callback’ine, istersen verbose modda console'a yazdırma.
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
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

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
            'X-ClientKey': self._client_key,
            'Authorization': self._jwt_token,
            'X-Signature': sig,
            'X-Timestamp': ts,
        }

        # Bağlantıyı aç
        self._ws = await websockets.connect(self.ws_url, extra_headers=headers)
        if self.verbose:
            print(f"✅ WebSocket bağlantısı kuruldu: {self.ws_url}")

        # Gelen mesajları dinlemeye başla
        asyncio.create_task(self._receive_loop())
        # Periyodik heartbeat döngüsünü başlat
        asyncio.create_task(self._send_loop())

    async def _receive_loop(self):
        """
        WebSocket üzerinden gelen her mesajı alır.
        Eğer on_message callback atanmışsa oraya, değilse verbose modda print'e yollar.
        Bağlantı kapanırsa otomatik reconnect dener.
        """
        assert self._ws is not None
        try:
            async for msg in self._ws:
                if callable(self.on_message):
                    self.on_message(msg)
                elif self.verbose:
                    print("Gelen mesaj:", msg)
        except websockets.ConnectionClosed:
            if self.verbose:
                print("🔄 Bağlantı kapandı, yeniden bağlanılıyor...")
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
            print("Gönderilen mesaj:", msg)

    def start(self):
        """
        Senkron olarak event loop başlatır ve connect() metodunu çalıştırır.
        """
        asyncio.get_event_loop().run_until_complete(self.connect())
