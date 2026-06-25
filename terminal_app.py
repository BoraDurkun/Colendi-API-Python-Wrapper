"""
Rich tabanlı terminal uygulaması:
  • REST login
  • Portfolio / Stock / Future endpoint menüleri
  • WebSocket abonelik menüsü (AddT/AddY/AddD …)
"""

# ── Standart kütüphaneler ───────────────────────────────────────────────
import os, sys, subprocess, time, json, asyncio, threading
from datetime import datetime, timedelta
from typing import Optional, cast

# ── Üçüncü parti ────────────────────────────────────────────────────────
from requests.exceptions import RequestException
from rich.console import Console
from rich.theme import Theme
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table

# ── Yerel modüller ───────────────────────────────────────────────────────
from api_client import API, WebSocket
from config import (
    API_URL, CLIENT_KEY, CLIENT_SECRET, USERNAME, PASSWORD,
    DIRECTION_MAP, ORDER_METHOD_MAP, ORDER_DURATION_MAP,
    ORDER_DURATION_DESCRIPTION_MAP, ORDER_METHOD_DESCRIPTION_MAP,
    VIOP_LONG_SHORT_MAP,
    FUND_DIRECTION_MAP,
    WEBSOCKET_SUBSCRIBE, WEBSOCKET_UNSUBSCRIBE
)

# ── Rich tema tanımı ─────────────────────────────────────────────────────
theme = Theme({
    "repr.string":     "#E6DB74",
    "repr.number":     "#81A7FF",
    "repr.bool_true":  "#A6E22E",
    "repr.bool_false": "#F92672",
    "repr.none":       "#75715E",
    "repr.key":        "bold #66D9EF",
    "label":   "bold #E6DB74",
    "value":   "italic #F8F8F2",
    "info":    "bold #66D9EF",
    "warning": "italic #E69F00",
    "error":   "bold #FF5555",
    "success": "bold #50FA7B",
    "prompt":  "bold #8BE9FD",
    "menu":    "#F8F8F2",
    "title":   "bold #81A7FF",
    "highlight": "reverse #44475A",
})
console = Console(theme=theme)

# ── Global nesneler ──────────────────────────────────────────────────────
api: Optional[API]                      = None
ws: Optional[WebSocket]                 = None
loop: Optional[asyncio.AbstractEventLoop] = None
ws_thread: Optional[threading.Thread]   = None
logger_proc: Optional[subprocess.Popen] = None

# ════════════════════════════════════════════════════════════════════════
# RICH yardımcıları
# ------------------------------------------------------------------------
def json_panel(data: dict | list, title: str = "JSON") -> None:
    syntax = Syntax(json.dumps(data, indent=2, ensure_ascii=False),
                    "json", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"[title]{title}[/title]",
                        border_style="yellow"))

def select_from_menu(title: str, options: list[tuple[str, str]]) -> str:
    body = Text.from_markup("\n".join(f"[prompt]{k}[/prompt]  {d}"
                                      for k, d in options))
    console.print(Panel(body, title=f"[title]{title}[/title]",
                        border_style="green", expand=False))
    return Prompt.ask("[prompt]Seçiminiz[/prompt]", default="").strip()

def show_api_info() -> None:
    t = Table.grid(padding=(0, 1))
    t.add_column(style="label", justify="right")
    t.add_column(style="value")
    t.add_row("API URL:",   f"[highlight]{API_URL}[/]")
    t.add_row("API Key:",   CLIENT_KEY)
    t.add_row("Secret:",    CLIENT_SECRET)
    t.add_row("Kullanıcı:", USERNAME or "-")
    t.add_row("Şifre:",     PASSWORD or "-")
    console.print(Panel(t, title="[title]API Bilgileri[/title]",
                        border_style="yellow"))

# ════════════════════════════════════════════════════════════════════════
# WebSocket yardımcıları
# ------------------------------------------------------------------------
def _run_ws_loop(ws: WebSocket, evloop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(evloop)
    evloop.run_until_complete(ws.connect())
    evloop.run_forever()

def start_websocket() -> None:
    """WS client + logger’ı tek seferde hazırlar."""
    global ws, loop, ws_thread, logger_proc
    if ws:  # zaten başlatılmış
        return

    def on_message(msg: str):
        if logger_proc and logger_proc.stdin:
            logger_proc.stdin.write((msg + "\n").encode())
            logger_proc.stdin.flush()

    # 1) WS logger süreci
    env = os.environ.copy()
    env["JWT_TOKEN"] = api._jwt_token               # type: ignore[attr-defined]
    logger_proc = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), "ws_logger.py")],
        stdin=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        env=env
    )
    console.print("[info]▶ WS log’ları için ayrı pencere açıldı.[/info]")

    # 2) WS istemcisi
    ws = WebSocket(
        api_url            = API_URL,
        api_key            = CLIENT_KEY,
        secret_key         = CLIENT_SECRET,
        jwt_token          = api._jwt_token,        # type: ignore[attr-defined]
        heartbeat_interval = 300,
        verbose            = False
    )
    ws.on_message = on_message

    # 3) Event-loop + thread
    loop = asyncio.new_event_loop()
    ws_thread = threading.Thread(target=_run_ws_loop, args=(ws, loop),
                                 daemon=True)
    ws_thread.start()
    time.sleep(1)

def graceful_shutdown():
    """WS, event-loop, thread ve logger’ı temiz kapatır."""
    if ws and loop:
        try:
            asyncio.run_coroutine_threadsafe(ws.close(), loop).result(3) # type: ignore
        except Exception:
            pass
        loop.call_soon_threadsafe(loop.stop)
    if ws_thread:
        ws_thread.join(timeout=1)
    if logger_proc and logger_proc.stdin:
        logger_proc.stdin.close()

# ════════════════════════════════════════════════════════════════════════
# Giriş (REST login)
# ------------------------------------------------------------------------
def _response_value(resp: dict, key: str):
    return resp.get(key) if key in resp else resp.get(key[:1].upper() + key[1:])

def _is_success_response(resp: dict) -> bool:
    return bool(_response_value(resp, "isSuccess"))

def _message_text(resp: dict) -> str:
    parts = [
        _response_value(resp, "message"),
        _response_value(resp, "messageCode"),
        _response_value(resp, "errorCode"),
    ]
    errors = _response_value(resp, "errors") or []
    if isinstance(errors, list):
        parts.extend(errors)
    return " ".join(str(part) for part in parts if part).lower()

def _can_continue_to_sms(resp: dict) -> bool:
    text = _message_text(resp)
    return "sms" in text and ("hatal" in text or "eksik" in text)

def rich_login():
    global api
    if not all([API_URL, CLIENT_KEY, CLIENT_SECRET]):
        console.print("[error]config.py’de API_URL / KEY / SECRET eksik.[/error]")
        sys.exit(1)

    api = API.get_api(api_url=cast(str, API_URL),
                      api_key=cast(str, CLIENT_KEY),
                      secret_key=cast(str, CLIENT_SECRET),
                      verbose=True)

    if not getattr(api, "_jwt_token", None):
        try:
            otp = api.send_otp(USERNAME or "", PASSWORD or "")
        except RequestException as e:
            console.print("[error]OTP isteği hatası:[/error]", e)
            sys.exit(1)

        if not _is_success_response(otp) and not _can_continue_to_sms(otp):
            console.print("[error]OTP isteği başarısız.[/error]", otp)
            sys.exit()

        console.print("\n[prompt]SMS kodu:[/prompt] ", end="")
        code = input().strip()

        try:
            login_resp = api.login(code, user_name=USERNAME or "", password=PASSWORD or "")
        except RequestException as e:
            console.print("[error]Giriş hatası:[/error]", e)
            sys.exit(1)

        data = _response_value(login_resp, "data") or {}
        access_token = data.get("accessToken") or data.get("AccessToken")
        if not access_token:
            console.print("[error]Giriş başarısız.[/error]", login_resp)
            sys.exit(1)

        console.print("[success]✅ Giriş başarılı.[/success]")
    else:
        console.print("[success]✅ Kayıtlı token geçerli.[/success]")

# ════════════════════════════════════════════════════════════════════════
# Ask yardımcıları
# ------------------------------------------------------------------------
def ask_optional_str(prompt: str, required=False) -> Optional[str]:
    while True:
        val = Prompt.ask(prompt + (" (zorunlu)" if required else ""), default="").strip()
        if val or not required:
            return val or None
        console.print("[error]Bu alan zorunlu.[/error]")

def ask_optional_int(prompt: str, required=False) -> Optional[int]:
    while True:
        val = Prompt.ask(prompt + (" (zorunlu)" if required else ""), default="").strip()
        if not val and not required:
            return None
        if val.isdigit():
            return int(val)
        console.print("[error]Sayı girin.[/error]")

def ask_optional_float(prompt: str, required=False) -> Optional[float]:
    while True:
        val = Prompt.ask(prompt + (" (zorunlu)" if required else ""), default="").strip().replace(",", ".")
        if not val and not required:
            return None
        try:
            return float(val)
        except ValueError:
            console.print("[error]Ondalıklı değer girin.[/error]")

def ask_optional_bool(prompt: str, required=False) -> Optional[bool]:
    while True:
        val = Prompt.ask(prompt + (" (zorunlu)" if required else "") + " (1/0)", default="").strip().lower()
        if not val and not required:
            return None
        if val in ("1", "y", "e", "yes", "true", "t"):
            return True
        if val in ("0", "n", "h", "no", "false", "f"):
            return False
        console.print("[error]1/0 veya evet/hayır yazın.[/error]")

def ask_optional_date(prompt: str, required=False) -> Optional[str]:
    while True:
        val = Prompt.ask(prompt + (" (zorunlu)" if required else "") + " (YYYY-MM-DD)", default="").strip()
        if not val and not required:
            return None
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            console.print("[error]Tarih formatı YYYY-MM-DD olmalı.[/error]")

def ask_relative_datetime(prompt: str, required=False) -> Optional[datetime]:
    """Bugün / Dün gibi hazır seçenekler ya da elle tarih girişi sunar."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    options = {
        1: ("Bugün", today),
        2: ("Dün", today - timedelta(days=1)),
        3: ("Tarih gir (YYYY-MM-DD)", None),
    }
    while True:
        console.print(f"\n{prompt} seçenekleri:")
        for k, (label, _) in options.items():
            console.print(f" {k}) {label}")
        sel = Prompt.ask(f"{prompt} seçiminiz" + (" (zorunlu)" if required else ""), default="").strip()
        if not sel and not required:
            return None
        if sel.isdigit() and int(sel) in options:
            label, value = options[int(sel)]
            if value is not None:
                return value
            manual = ask_optional_date(prompt, required=True)
            if manual is not None:
                manual_dt = datetime.strptime(manual, "%Y-%m-%d")
                if manual_dt > today:
                    console.print("[error]Gelecek bir tarih seçilemez.[/error]")
                    continue
                return manual_dt
        console.print("[error]Geçersiz seçim.[/error]")

def ask_enum_choice(
    prompt: str,
    choice_map: dict[int, str],
    required=False,
    descriptions: Optional[dict[str, str]] = None,
    show_value_with_description: bool = True
) -> Optional[str]:
    while True:
        console.print(f"\n{prompt} seçenekleri:")
        for k, v in choice_map.items():
            description = descriptions.get(v) if descriptions else None
            label = f"{v} - {description}" if description and show_value_with_description else (description or v)
            console.print(f" {k}) {label}")
        sel = Prompt.ask(f"{prompt} seçiminiz" + (" (zorunlu)" if required else ""), default="").strip()
        if not sel and not required:
            return None
        if sel.isdigit() and int(sel) in choice_map:
            return choice_map[int(sel)]
        console.print("[error]Geçersiz seçim.[/error]")

# ════════════════════════════════════════════════════════════════════════
# Endpoint Wrappers
# ------------------------------------------------------------------------

# ——— Portfolio Endpoints ———
def get_subaccounts():
    if api:
        resp = api.get_portfolio_stock()
        json_panel(resp, title="Hisse Senedi Portföyü ve Nakit Akışı")

def get_account_summary():
    if api:
        resp = api.get_portfolio_future()
        json_panel(resp, title="Viop Portföyü ve Viop Nakit Akışı")

def get_cash_assets():
    if api:
        resp = api.get_portfolio_fund()
        json_panel(resp, title="Fon Portföyü ve Fon Nakit Akışı")

def get_cash_balance():
    if api:
        resp = api.get_portfolio_stock()
        json_panel(resp, title="Hisse Senedi Portföyü ve Nakit Akışı")

def get_account_overall():
    if api:
        resp = api.get_portfolio_future()
        json_panel(resp, title="Viop Portföyü ve Viop Nakit Akışı")

# ——— Stock Endpoints ———
def get_stock_create_order():
    symbol = ask_optional_str("Code", required=True)
    direction = ask_enum_choice("Buy/Sell", DIRECTION_MAP, required=True)
    method = ask_enum_choice(
        "Order Type",
        ORDER_METHOD_MAP,
        required=True,
        descriptions=ORDER_METHOD_DESCRIPTION_MAP
    )
    duration = ask_enum_choice(
        "Session",
        ORDER_DURATION_MAP,
        required=True,
        descriptions=ORDER_DURATION_DESCRIPTION_MAP,
        show_value_with_description=False
    )
    qty = ask_optional_float("Quantity", required=True)
    price = ask_optional_float("Price", required=True)
    sub_market = ask_optional_str("Sub Market")

    if symbol is None or qty is None or direction is None or price is None or method is None or duration is None:
        return

    if api:
        resp = api.new_stock_order(
            code=symbol,
            buy_sell=direction,
            order_type=method,
            session=duration,
            quantity=qty,
            price=price,
            sub_market=sub_market
        )
        json_panel(resp, title="Hisse Senedi Yeni Emir İletim")

def get_stock_replace_order():
    order_no = ask_optional_int("Order No", required=True)
    price = ask_optional_float("New Price", required=True)

    if order_no is None or price is None:
        return

    if api:
        resp = api.update_stock_order(order_no=order_no, price=price)
        json_panel(resp, title="Hisse Senedi Emir Düzeltme")

def get_stock_delete_order():
    order_no = ask_optional_int("Order No", required=True)
    if order_no is None:
        return
    if api:
        resp = api.cancel_stock_order(order_no=order_no)
        json_panel(resp, title="Hisse Senedi Emir Silme")

def get_stock_order_list():
    start_date = ask_relative_datetime("Başlangıç tarihi")
    if api:
        resp = api.get_stock_orders(start_date=start_date)
        json_panel(resp, title="Hisse Senedi Emirleri")

def get_stock_order_detail():
    order_no = ask_optional_int("Order No", required=True)
    if order_no is None:
        return

    if api:
        resp = api.get_stock_order_detail(order_no=order_no)
        json_panel(resp, title="Hisse Senedi Emir Detayı")

def get_stock_positions():
    if api:
        resp = api.get_portfolio_stock()
        json_panel(resp, title="Hisse Senedi Portföyü ve Nakit Akışı")

# ——— Future Endpoints ———
def get_future_create_order():
    contract = ask_optional_str("Code", required=True)
    direction = ask_enum_choice("Buy/Sell", VIOP_LONG_SHORT_MAP, required=True)
    method = ask_enum_choice(
        "Order Type",
        ORDER_METHOD_MAP,
        required=True,
        descriptions=ORDER_METHOD_DESCRIPTION_MAP
    )
    duration = ask_enum_choice("Session", ORDER_DURATION_MAP, required=True)
    qty = ask_optional_int("Quantity", required=True)
    price = ask_optional_float("Price", required=True)

    if (contract is None or direction is None or price is None or
            qty is None or method is None or duration is None):
        return
    if api:
        resp = api.new_future_order(
            code=contract,
            buy_sell=direction,
            order_type=method,
            session=duration,
            quantity=qty,
            price=price
        )
        json_panel(resp, title="Viop Emir İletim")

def get_future_replace_order():
    order_no = ask_optional_int("Order No", required=True)
    price = ask_optional_float("New Price", required=True)

    if order_no is None or price is None:
        return

    if api:
        resp = api.update_future_order(order_no=order_no, price=price)
        json_panel(resp, title="Viop Emir Düzeltme")

def get_future_delete_order():
    order_no = ask_optional_int("Order No", required=True)

    if order_no is None:
        return

    if api:
        resp = api.cancel_future_order(order_no=order_no)
        json_panel(resp, title="Viop Emir Silme")

def get_future_order_list():
    if api:
        resp = api.get_future_orders()
        json_panel(resp, title="Viop Emirleri")

def get_future_order_detail():
    order_no = ask_optional_int("Order No", required=True)
    if order_no is None:
        return

    if api:
        resp = api.get_future_order_detail(order_no=order_no)
        json_panel(resp, title="Viop Emir Detayı")

def get_future_positions():
    if api:
        resp = api.get_portfolio_future()
        json_panel(resp, title="Viop Portföyü ve Viop Nakit Akışı")

def get_available_fund_list():
    if api:
        resp = api.get_available_fund_list()
        json_panel(resp, title="İşlem Yapılabilir Fon Listesi")

def get_fund_orders():
    if api:
        resp = api.get_fund_orders()
        json_panel(resp, title="Fon Emirleri")

def new_fund_order():
    fund_id = ask_optional_int("Fund ID", required=True)
    buy_sell = ask_enum_choice("Buy/Sell", FUND_DIRECTION_MAP, required=True)
    quantity = ask_optional_float("Quantity", required=True)
    price = ask_optional_float("Price", required=True)

    if fund_id is None or buy_sell is None or quantity is None or price is None:
        return

    if api:
        resp = api.new_fund_order(
            fund_id=fund_id,
            buy_sell=buy_sell,
            quantity=quantity,
            price=price
        )
        json_panel(resp, title="Fon Emir İletim")

def cancel_fund_order():
    order_no = ask_optional_int("Order No", required=True)
    if order_no is None:
        return

    if api:
        resp = api.cancel_fund_order(order_no=order_no)
        json_panel(resp, title="Fon Emir Silme")
 
 # ════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════
# Menü yapısı
# ------------------------------------------------------------------------
def main_menu():
    while True:
        ch = select_from_menu("Ana Menü", [
            ("1", "Portföy ve Nakit Akışı"),
            ("2", "Pay Menüsü"),
            ("3", "Viop Menüsü"),
            ("4", "Fon Menüsü"),
            ("5", "WebSocket Abonelikleri Menüsü"),
            ("*", "Çıkış"),
        ])
        if ch == "1":
            portfolio_menu()
        elif ch == "2":
            stock_menu()
        elif ch == "3":
            future_menu()
        elif ch == "4":
            fund_menu()
        elif ch == "5":
            websocket_menu()
        elif ch == "*":
            console.print("[info]Çıkış yapılıyor…[/info]")
            graceful_shutdown()
            sys.exit()
        else:
            console.print("[warning]Geçersiz seçim.[/warning]")

def portfolio_menu() -> None:
    while True:
        choice = select_from_menu("Hesap Bilgisi Menusu", [
            ("1", "Hisse Senedi Portföyü ve Nakit Akışı"),
            ("2", "Viop Portföyü ve Viop Nakit Akışı"),
            ("3", "Fon Portföyü ve Fon Nakit Akışı"),
            ("0", "Ana Menu"),
        ])
        if choice == "0": return
        elif choice == "1": get_subaccounts()
        elif choice == "2": get_account_summary()
        elif choice == "3": get_cash_assets()
        else: console.print("[warning]Geçersiz seçim.[/warning]")

def stock_menu() -> None:
    while True:
        choice = select_from_menu("Pay Emir Menüsü", [
            ("1", "Hisse Senedi Yeni Emir İletim"),
            ("2", "Hisse Senedi Emir Düzeltme"),
            ("3", "Hisse Senedi Emir Silme"),
            ("4", "Hisse Senedi Emirleri"),
            ("5", "Hisse Senedi Emir Detayı"),
            ("0", "Ana Menü"),
        ])
        if choice == "0": return
        elif choice == "1": get_stock_create_order()
        elif choice == "2": get_stock_replace_order()
        elif choice == "3": get_stock_delete_order()
        elif choice == "4": get_stock_order_list()
        elif choice == "5": get_stock_order_detail()
        else: console.print("[warning]Geçersiz seçim.[/warning]")

def future_menu() -> None:
    while True:
        choice = select_from_menu("Vadeli Emir Menüsü", [
            ("1", "Viop Emir İletim"),
            ("2", "Viop Emir Düzeltme"),
            ("3", "Viop Emir Silme"),
            ("4", "Viop Emirleri"),
            ("5", "Viop Emir Detayı"),
            ("0", "Ana Menü"),
        ])
        if choice == "0": return
        elif choice == "1": get_future_create_order()
        elif choice == "2": get_future_replace_order()
        elif choice == "3": get_future_delete_order()
        elif choice == "4": get_future_order_list()
        elif choice == "5": get_future_order_detail()
        else: console.print("[warning]Geçersiz seçim.[/warning]")

def fund_menu() -> None:
    while True:
        choice = select_from_menu("Fon Emir Menusu", [
            ("1", "İşlem Yapılabilir Fon Listesi"),
            ("2", "Fon Emirleri"),
            ("3", "Fon Emir İletim"),
            ("4", "Fon Emir Silme"),
            ("0", "Ana Menu"),
        ])
        if choice == "0": return
        elif choice == "1": get_available_fund_list()
        elif choice == "2": get_fund_orders()
        elif choice == "3": new_fund_order()
        elif choice == "4": cancel_fund_order()
        else: console.print("[warning]Geçersiz seçim.[/warning]")

def websocket_menu():
    start_websocket()
    while True:
        choice = select_from_menu("WebSocket Abonelik Menüsü", [
            ("1", "Abone Ol"),
            ("2", "Abonelikten Çık"),
            ("0", "Ana Menü"),
        ])

        if choice == "0":
            return

        elif choice == "1":  # Abone ol
            type_map = WEBSOCKET_SUBSCRIBE
            action = "Abonelik"
        elif choice == "2":  # Abonelikten çık
            type_map = WEBSOCKET_UNSUBSCRIBE
            action = "Abonelik İptali"
        else:
            console.print("[warning]Geçersiz seçim.[/warning]")
            continue

        # Mesaj tipi seçimi (örneğin: AddT / RemoveY)
        typ = ask_enum_choice(f"{action} Tipi Seçin", type_map, required=True)
        if not typ:
            console.print("[warning]İşlem iptal edildi.[/warning]")
            continue

        # Sembol listesi gir
        syms = Prompt.ask("[prompt]Semboller (virgülle ayırın)[/prompt]").split(",")
        symbols = [s.strip() for s in syms if s.strip()]
        if not symbols:
            console.print("[warning]Geçerli sembol girilmedi.[/warning]")
            continue

        # WebSocket mesajı oluştur
        payload = {
            "Token": ws._jwt_token,  # type: ignore[attr-defined]
            "Type": typ,
            "Symbols": symbols,
        }

        try:
            fut = asyncio.run_coroutine_threadsafe(ws._send(payload), loop)  # type: ignore[arg-type]
            fut.result(timeout=5)
            console.print(f"[success]✅ {action} başarılı:[/success]")
        except Exception as e:
            console.print(f"[error]❌ Gönderim hatası:[/error] {e}")

# ════════════════════════════════════════════════════════════════════════
# Uygulama giriş noktası
# ------------------------------------------------------------------------
def main():
    console.clear()
    show_api_info()
    rich_login()
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        graceful_shutdown()
        console.print("\n[info]Program sonlandırıldı (Ctrl-C).[/info]")
