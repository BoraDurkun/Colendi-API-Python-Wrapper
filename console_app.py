import sys
from typing import Optional, cast
from datetime import datetime
from requests.exceptions import RequestException

import json
from rich.console import Console
from rich.theme import Theme
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table

theme = Theme({
    "repr.string": "#E6DB74",
    "repr.number": "#81A7FF",
    "repr.bool_true": "#A6E22E",
    "repr.bool_false": "#F92672",
    "repr.none": "#75715E",
    "repr.key": "bold #66D9EF",

    "label": "bold #E6DB74",
    "value": "italic #F8F8F2",

    "info": "bold #66D9EF",
    "warning": "italic #E69F00",
    "error": "bold #FF5555",
    "success": "bold #50FA7B",

    "prompt": "bold #8BE9FD",
    "menu": "#F8F8F2",
    "title": "bold #81A7FF",
    "highlight": "reverse #44475A",
})

console = Console(theme=theme)

from api_client import API, WebSocket
from config import *

# Global API istemcisi
api: Optional[API] = None

# ——— Pretty print functions ———

def show_api_info():
    table = Table.grid(padding=(0, 1))
    table.add_column(style="label", justify="right")
    table.add_column(style="value")
    table.add_row("Api Url:", f"[highlight]{API_URL}[/]")
    table.add_row("Api Key:", API_KEY)
    table.add_row("Secret Key:", API_SECRET)
    table.add_row("Müşteri No:", USERNAME or "-")
    table.add_row("Şifre:", PASSWORD or "-")

    console.print()
    console.print(Panel(table, title="[title]Api Bilgileri[/title]", border_style="highlight", padding=(1, 2)))
    console.print()


def json_panel(data: dict | list, title: str = "JSON") -> None:
    """
    JSON verisini renklendirip panel içinde gösterir.
    """
    syntax = Syntax(
        json.dumps(data, indent=2, ensure_ascii=False),
        "json",
        theme="monokai",
        line_numbers=False,
    )
    console.print()
    console.print(Panel(syntax, title=f"[title]{title}[/title]", border_style="highlight", padding=(1, 2)))
    console.print()

def select_from_menu(title: str, options: list[tuple[str, str]]) -> str:

    lines = [f"[prompt]{key}[/prompt]  {desc}" for key, desc in options]
    body = Text.from_markup("\n".join(lines))
    panel = Panel(body, title=f"[title]{title}[/title]", border_style="highlight", expand=False)
    console.print()
    console.print(panel)
    console.print()

    return Prompt.ask("[prompt]Seçiminiz[/prompt]", default="").strip()

# ── MENÜ FONKSİYONLARI ────────────────────────────────────────────────────────
def main_menu() -> None:
    while True:
        choice = select_from_menu("Ana Menü", [
            ("1", "Portfolio Endpoints Menüsü"),
            ("2", "Stock Endpoints Menüsü"),
            ("3", "Future Endpoints Menüsü"),
            ("*", "Çıkış"),
        ])
        if choice == "1":
            portfolio_menu()
        elif choice == "2":
            stock_menu()
        elif choice == "3":
            future_menu()
        elif choice == "*":
            console.print("[error]Çıkış yapılıyor…[/error]")
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

# ——— Choice Functions ———
def ask_optional_str(prompt: str, required: bool = False) -> Optional[str]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(bos icin Enter)'} : ").strip()
        if val == "":
            if required:
                console.print("❌ Bu alan zorunlu, lutfen bir deger girin.")
                continue
            return None
        return val

def ask_optional_int(prompt: str, required: bool = False) -> Optional[int]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(bos icin Enter)'} : ").strip()
        if val == "":
            if required:
                console.print("❌ Bu alan zorunlu, lutfen bir sayi girin.")
                continue
            return None
        if val.isdigit():
            return int(val)
        console.print("❌ Gecersiz girdi. Lutfen bir sayi girin veya bos birakin.")

def ask_optional_float(prompt: str, required: bool = False) -> Optional[float]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(bos icin Enter)'} : ").strip().replace(",", ".")
        if val == "":
            if required:
                console.print("❌ Bu alan zorunlu, lutfen bir ondalikli sayi girin.")
                continue
            return None
        try:
            return float(val)
        except ValueError:
            console.print("❌ Gecersiz sayi. Lutfen ondalikli bir deger girin veya bos birakin.")

def ask_optional_bool(prompt: str, required: bool = False) -> Optional[bool]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(bos icin Enter)'} (1=Evet, 0=Hayir): ").strip().lower()
        if val == "":
            if required:
                console.print("❌ Bu alan zorunlu, lutfen evet veya hayir girin.")
                continue
            return None
        if val in ("1", "y", "e", "yes", "true", "t"):
            return True
        if val in ("0", "n", "h", "no", "false", "f"):
            return False
        console.print("❌ Gecersiz girdi. Lutfen 1/0 veya evet/hayir yazin.")

def ask_optional_date(prompt: str, required: bool = False) -> Optional[str]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(bos icin Enter)'} (YYYY-MM-DD): ").strip()
        if val == "":
            if required:
                console.print("❌ Bu alan zorunlu, lutfen gecerli bir tarih girin.")
                continue
            return None
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            console.print("❌ Gecersiz tarih formati. YYYY-MM-DD biciminde giriniz.")

def ask_enum_choice(
    prompt: str,
    choice_map: dict[int, str],
    required: bool = False
) -> Optional[str]:
    """
    :param prompt: Soru metni
    :param choice_map: {1: "A", 2: "B", ...}
    :param required: True ise bos gecilmesine izin vermez
    :return: Secilen deger veya None
    """
    while True:
        console.print(f"\n{prompt} secenekleri:")
        for key, val in choice_map.items():
            console.print(f" {key}) {val}")
        sel = input(f"{prompt} seciminiz{' (zorunlu)' if required else '(bos icin Enter)'}: ").strip()
        
        if sel == "":
            if required:
                console.print("❌ Bu alan zorunlu, lutfen bir secim yapin.")
                continue
            return None
        
        if sel.isdigit() and int(sel) in choice_map:
            return choice_map[int(sel)]
        
        console.print("❌ Gecersiz secim. Tekrar deneyin.")

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
 
def main():
    global api
    if not all([API_URL, API_KEY, API_SECRET]):
        console.print("❌ config.py dosyasindaki API_URL, API_KEY veya API_SECRET eksik.")
        sys.exit()

    # Pylance icin kesin tip belirtimi:
    api_url: str = cast(str, API_URL)
    api_key: str = cast(str, API_KEY)
    secret_key: str = cast(str, API_SECRET)

    try:
        api = API.get_api(
            api_url=api_url,
            api_key=api_key,
            secret_key=secret_key,
            verbose=True
        )

    except Exception as e:
        console.print("❌ API baslatilamadi:", e)
        sys.exit()

    if not api._jwt_token:
        try:
            otp_resp = api.send_otp(USERNAME or "", PASSWORD or "")
        except RequestException as e:
            console.print("❌ OTP istegi sirasinda hata:", e)
            sys.exit()

        data = otp_resp.get("data")
        if not isinstance(data, dict) or "token" not in data:
            console.print("❌ OTP yanitinda token bulunamadi:", otp_resp)
            sys.exit()

        token = data["token"]
        console.print("✅ OTP gonderildi.\n")
        code = input("SMS kodunu girin: ").strip()

        try:
            login_resp = api.login(token, code)
        except RequestException as e:
            console.print("❌ Giris sirasinda hata:", e)
            sys.exit()

        if not isinstance(login_resp, dict) or "data" not in login_resp:
            console.print("❌ Beklenmeyen login yaniti:", login_resp)
            sys.exit()

        console.print("✅ Giris basarili.")
    else:
        console.print("✅🔑 Kayitli token gecerli. Menuye geciliyor...")

    main_menu()

if __name__ == "__main__":
    show_api_info()
    main()
