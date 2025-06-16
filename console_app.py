"""
Rich tabanlı terminal uygulaması:
  • REST login
  • Portfolio / Stock / Future endpoint menüleri
  • WebSocket abonelik menüsü (AddT/AddY/AddD …)
  • Kapanışta temiz kaynak yönetimi
"""

# ── Standart kütüphaneler ───────────────────────────────────────────────
import os, sys, subprocess, time, json, asyncio, threading
from datetime import datetime
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
    API_URL, API_KEY, API_SECRET, USERNAME, PASSWORD,
    DIRECTION_MAP, ORDER_METHOD_MAP, ORDER_DURATION_MAP,
    ORDER_STATUS_MAP, EQUITY_TYPE_MAP,
    VIOP_LONG_SHORT_MAP, VIOP_CONTRACT_TYPE_MAP,
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
    t.add_row("API Key:",   API_KEY)
    t.add_row("Secret:",    API_SECRET)
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
        api_key            = API_KEY,
        secret_key         = API_SECRET,
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
def rich_login():
    global api
    if not all([API_URL, API_KEY, API_SECRET]):
        console.print("[error]config.py’de API_URL / KEY / SECRET eksik.[/error]")
        sys.exit(1)

    api = API.get_api(api_url=cast(str, API_URL),
                      api_key=cast(str, API_KEY),
                      secret_key=cast(str, API_SECRET),
                      verbose=True)

    if not getattr(api, "_jwt_token", None):
        try:
            otp = api.send_otp(USERNAME or "", PASSWORD or "")
        except RequestException as e:
            console.print("[error]OTP isteği hatası:[/error]", e)
            sys.exit(1)

        token = otp.get("data", {}).get("token")
        if not token:
            console.print("[error]OTP yanıtında token yok.[/error]")
            sys.exit(1)

        console.print("\n[prompt]SMS kodu:[/prompt] ", end="")
        code = input().strip()

        try:
            login_resp = api.login(token, code)
        except RequestException as e:
            console.print("[error]Giriş hatası:[/error]", e)
            sys.exit(1)

        if "data" not in login_resp:
            console.print("[error]Beklenmeyen login yanıtı[/error]", login_resp)
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

def ask_enum_choice(prompt: str, choice_map: dict[int, str], required=False) -> Optional[str]:
    while True:
        console.print(f"\n{prompt} seçenekleri:")
        for k, v in choice_map.items():
            console.print(f" {k}) {v}")
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
        resp = api.get_subaccounts()
        json_panel(resp, title="Alt Hesaplar")

def get_account_summary():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_account_summary(portfolio_number=port)
        json_panel(resp, title="get_account_summary")

def get_cash_assets():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_cash_assets(portfolio_number=port)
        json_panel(resp, title="get_cash_assets")

def get_cash_balance():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_cash_balance(portfolio_number=port)
        json_panel(resp, title="get_cash_balance")

def get_account_overall():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_account_overall(portfolio_number=port)
        json_panel(resp, title="get_account_overall")

# ——— Stock Endpoints ———
def get_stock_create_order():
    port      = ask_optional_int("Portfolio Number", required=True)
    symbol    = ask_optional_str("Equity Code", required=True)
    qty       = ask_optional_int("Quantity", required=True)
    direction = ask_enum_choice("Direction", DIRECTION_MAP, required=True)
    price     = ask_optional_float("Price", required=True)
    method    = ask_enum_choice("Order Method", ORDER_METHOD_MAP, required=True)
    duration  = ask_enum_choice("Order Duration", ORDER_DURATION_MAP, required=True)
    mra       = ask_optional_bool("Market Risk Approval?")

    if port is None or symbol is None or qty is None or direction is None or price is None or method is None or duration is None:
        return
    assert port is not None and symbol is not None and qty is not None and direction is not None and price is not None and method is not None and duration is not None

    if api:
        resp = api.get_stock_create_order(
            portfolio_number=port,
            equity_code=symbol,
            quantity=qty,
            direction=direction,
            price=price,
            order_method=method,
            order_duration=duration,
            market_risk_approval=mra
        )
        json_panel(resp, title="get_stock_create_order")

def get_stock_replace_order():
    port  = ask_optional_int("Portfolio Number", required=True)
    ref   = ask_optional_str("Order Ref", required=True)
    price = ask_optional_float("New Price", required=True)
    qty   = ask_optional_int("New Quantity", required=True)

    if port is None or ref is None or price is None or qty is None:
        return
    assert port is not None and ref is not None and price is not None and qty is not None

    if api:
        resp = api.get_stock_replace_order(
            portfolio_number=port,
            order_ref=ref,
            price=price,
            quantity=qty
        )
        json_panel(resp, title="get_stock_replace_order")

def get_stock_delete_order():
    port = ask_optional_int("Portfolio Number", required=True)
    ref  = ask_optional_str("Order Ref to delete", required=True)
    if port is None or ref is None:
        return
    assert port is not None and ref is not None
    if api:
        resp = api.get_stock_delete_order(
            portfolio_number=port,
            order_ref=ref
        )
        json_panel(resp, title="get_stock_delete_order")

def get_stock_order_list():
    port             = ask_optional_int("Portfolio Number", required=True)
    order_status     = ask_enum_choice("Order Status", ORDER_STATUS_MAP)
    order_direction  = ask_enum_choice("Order Direction", DIRECTION_MAP)
    order_method     = ask_enum_choice("Order Method", ORDER_METHOD_MAP)
    order_duration   = ask_enum_choice("Order Duration", ORDER_DURATION_MAP)
    equity_code      = ask_optional_str("Equity Code")
    equity_type      = ask_enum_choice("Equity Type", EQUITY_TYPE_MAP)
    page_number      = ask_optional_int("Page Number", required=True)
    descending_order = ask_optional_bool("Descending Order?")

    if (port is None or page_number is None):
        console.print("❌ Zorumlu alanlar doldurulmali.")
        return
    assert (port is not None and page_number is not None)

    if api:
        resp = api.get_stock_order_list(
            portfolio_number=port,
            order_status=order_status,
            order_direction=order_direction,
            order_method=order_method,
            order_duration=order_duration,
            equity_code=equity_code,
            equity_type=equity_type,
            page_number=page_number,
            descending_order=descending_order
        )
        json_panel(resp, title="get_stock_order_list")

def get_stock_positions():
    port         = ask_optional_int("Portfolio Number", required=True)
    equity_code  = ask_optional_str("Equity Code")
    equity_type  = ask_enum_choice("Equity Type", EQUITY_TYPE_MAP)
    without_dep  = ask_optional_bool("Without Depot?")
    without_t1   = ask_optional_bool("Without T+1 Qty?")

    if (port is None):
        console.print("❌ Zorunlu alanlar doldurulmali.")
        return
    assert (port is not None)

    if api:
        resp = api.get_stock_positions(
            portfolio_number=port,
            equity_code=equity_code,
            equity_type=equity_type,
            without_depot=without_dep,
            without_t1_qty=without_t1
        )
        json_panel(resp, title="get_stock_positions")

# ——— Future Endpoints ———
def get_future_create_order():
    port      = ask_optional_int("Portfolio Number", required=True)
    contract  = ask_optional_str("Contract Code", required=True)
    direction = ask_enum_choice("Direction", VIOP_LONG_SHORT_MAP, required=True)
    price     = ask_optional_float("Price", required=True)
    qty       = ask_optional_int("Quantity", required=True)
    method    = ask_enum_choice("Order Method", ORDER_METHOD_MAP, required=True)
    duration  = ask_enum_choice("Order Duration", ORDER_DURATION_MAP, required=True)
    ahs       = ask_optional_bool("After Hour Valid?", required=True)
    exp_date  = ask_optional_date("Expiration Date", required=True)

    if (port is None or contract is None or direction is None or price is None or
            qty is None or method is None or duration is None or ahs is None or
            exp_date is None):
        return
    assert (port is not None and contract is not None and direction is not None and
            price is not None and qty is not None and method is not None and
            duration is not None and ahs is not None and exp_date is not None)

    if api:
        resp = api.get_future_create_order(
            portfolio_number=port,
            contract_code=contract,
            direction=direction,
            price=price,
            quantity=qty,
            order_method=method,
            order_duration=duration,
            after_hour_session_valid=ahs,
            expiration_date=exp_date
        )
        json_panel(resp, title="get_future_create_order")

def get_future_replace_order():
    port     = ask_optional_int("Portfolio Number", required=True)
    ref      = ask_optional_str("Order Ref", required=True)
    qty      = ask_optional_int("New Quantity", required=True)
    price    = ask_optional_float("New Price", required=True)
    otype    = ask_enum_choice("Order Type", ORDER_DURATION_MAP, required=True)
    exp_date = ask_optional_date("Expiration Date", required=True)

    if port is None or ref is None or qty is None or price is None or otype is None or exp_date is None:
        return
    assert port is not None and ref is not None and qty is not None and price is not None and otype is not None and exp_date is not None

    if api:
        resp = api.get_future_replace_order(
            portfolio_number=port,
            order_ref=ref,
            quantity=qty,
            price=price,
            order_type=otype,
            expiration_date=exp_date
        )
        json_panel(resp, title="get_future_replace_order")

def get_future_delete_order():
    port = ask_optional_int("Portfolio Number", required=True)
    ref  = ask_optional_str("Order Ref to delete", required=True)

    if port is None or ref is None:
        return
    assert port is not None and ref is not None

    if api:
        resp = api.get_future_delete_order(
            portfolio_number=port,
            order_ref=ref
        )
        json_panel(resp, title="get_future_delete_order")

def get_future_order_list():
    port                      = ask_optional_int("Portfolio Number", required=True)
    order_validity_date       = ask_optional_date("Order Validity Date")
    contract_code             = ask_optional_str("Contract Code")
    contract_type             = ask_enum_choice("Contract Type", VIOP_CONTRACT_TYPE_MAP)
    long_short                = ask_enum_choice("Long/Short", VIOP_LONG_SHORT_MAP)
    pending_orders            = ask_optional_bool("Pending Orders?")
    untransmitted_orders      = ask_optional_bool("Untransmitted Orders?")
    partially_executed_orders = ask_optional_bool("Partially Executed Orders?")
    cancelled_orders          = ask_optional_bool("Cancelled Orders?")
    after_hour_session_valid  = ask_optional_bool("After Hour Session Valid?")

    if (
        port is None
    ):
        return
    assert (
        port is not None
    )

    if api:
        resp = api.get_future_order_list(
            portfolio_number=port,
            order_validity_date=order_validity_date,
            contract_code=contract_code,
            contract_type=contract_type,
            long_short=long_short,
            pending_orders=pending_orders,
            untransmitted_orders=untransmitted_orders,
            partially_executed_orders=partially_executed_orders,
            cancelled_orders=cancelled_orders,
            after_hour_session_valid=after_hour_session_valid
        )
        json_panel(resp, title="get_future_order_list")

def get_future_positions():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    if api:
        resp = api.get_future_positions(portfolio_number=port)
        json_panel(resp, title="get_future_positions")
 
 # ════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════
# Menü yapısı
# ------------------------------------------------------------------------
def main_menu():
    while True:
        ch = select_from_menu("Ana Menü", [
            ("1", "Portfolio Endpoints Menüsü"),
            ("2", "Stock Endpoints Menüsü"),
            ("3", "Future Endpoints Menüsü"),
            ("4", "WebSocket Abonelik Menüsü"),
            ("*", "Çıkış"),
        ])
        if ch == "1":
            portfolio_menu()
        elif ch == "2":
            stock_menu()
        elif ch == "3":
            future_menu()
        elif ch == "4":
            websocket_menu()
        elif ch == "*":
            console.print("[info]Çıkış yapılıyor…[/info]")
            graceful_shutdown()
            sys.exit()
        else:
            console.print("[warning]Geçersiz seçim.[/warning]")

def portfolio_menu() -> None:
    while True:
        choice = select_from_menu("Hesap Bilgisi Menüsü", [
            ("1", "Alt Hesapları Görüntüle"),
            ("2", "get_account_summary Bilgisi"),
            ("3", "get_cash_assets Bilgisi"),
            ("4", "get_cash_balance Bilgisi"),
            ("5", "get_account_overall Bilgisi"),
            ("0", "Ana Menü"),
        ])
        if choice == "0": return
        elif choice == "1": get_subaccounts()
        elif choice == "2": get_account_summary()
        elif choice == "3": get_cash_assets()
        elif choice == "4": get_cash_balance()
        elif choice == "5": get_account_overall()
        else: console.print("[warning]Geçersiz seçim.[/warning]")

def stock_menu() -> None:
    while True:
        choice = select_from_menu("Pay Emir Menüsü", [
            ("1", "Emir Gönder"),
            ("2", "Emir Düzelt"),
            ("3", "Emir Sil"),
            ("4", "Pay Emir Listesi"),
            ("5", "Hisse Senedi Pozisyonları"),
            ("0", "Ana Menü"),
        ])
        if choice == "0": return
        elif choice == "1": get_stock_create_order()
        elif choice == "2": get_stock_replace_order()
        elif choice == "3": get_stock_delete_order()
        elif choice == "4": get_stock_order_list()
        elif choice == "5": get_stock_positions()
        else: console.print("[warning]Geçersiz seçim.[/warning]")

def future_menu() -> None:
    while True:
        choice = select_from_menu("Vadeli Emir Menüsü", [
            ("1", "Emir Gönder"),
            ("2", "Emir Düzelt"),
            ("3", "Emir Sil"),
            ("4", "Vadeli Emir Listesi"),
            ("5", "Pozisyonlar"),
            ("0", "Ana Menü"),
        ])
        if choice == "0": return
        elif choice == "1": get_future_create_order()
        elif choice == "2": get_future_replace_order()
        elif choice == "3": get_future_delete_order()
        elif choice == "4": get_future_order_list()
        elif choice == "5": get_future_positions()
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
