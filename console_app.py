import os
import sys
from typing import Optional, cast
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from requests.exceptions import RequestException

from api_client import API, WebSocket
from enums import *

# Ortam değişkenlerini yükle
load_dotenv(find_dotenv())

API_URL    = os.getenv("API_URL")
API_KEY    = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
USERNAME   = os.getenv("INTERNET_USER")
PASSWORD   = os.getenv("PASSWORD")

print(f"\n Api Url: {API_URL}")
print(f"\n Api Key: {API_KEY}")
print(f"\n Secret Key: {API_SECRET}")
print(f"\n Müşteri No: {USERNAME}")
print(f"\n Şifre: {PASSWORD}\n")

# Global API istemcisi
api: Optional[API] = None

def main_menu():
    while True:
        print("\nAna Menüye hoş geldiniz. Lütfen yapmak istediğiniz işlemi seçin:")
        print(" '1' Portfolio Endpoints Menüsü")
        print(" '2' Stock Endpoints Menüsü")
        print(" '3' Future Endpoints Menüsü")
        print(" '*' Çıkış")
        secim = input("\nSeçiminiz: ").strip()

        if secim == '1':
            portfolio_menu()
        elif secim == '2':
            stock_menu()
        elif secim == '3':
            future_menu()
        elif secim == '*':
            print("Çıkış yapılıyor…")
            sys.exit(0)
        else:
            print("Geçersiz seçim. Tekrar deneyin.")

def portfolio_menu():
    while True:
        print("\nHesap Bilgisi Menüsü — Lütfen yapmak istediğiniz işlemi seçin:")
        print(" '1' Alt Hesapları Görüntüle")
        print(" '2' get_account_summary Bilgisi")
        print(" '3' get_cash_assets Bilgisi")
        print(" '4' get_cash_balance Bilgisi")
        print(" '5' get_account_overall Bilgisi")
        print(" '0' Ana Menü")
        secim = input("\nSeçiminiz: ").strip()

        if secim == '1':
            get_subaccounts()
        elif secim == '2':
            get_account_summary()
        elif secim == '3':
            get_cash_assets()
        elif secim == '4':
            get_cash_balance()
        elif secim == '5':
            get_account_overall()
        elif secim == '0':
            return
        else:
            print("Geçersiz seçim. Tekrar deneyin.")

def stock_menu():
    while True:
        print("\nPay Emir Menüsü:")
        print(" '1' Emir Gönder")
        print(" '2' Emir Düzelt")
        print(" '3' Emir Sil")
        print(" '4' Pay Emir Listesi")
        print(" '5' Hisse Senedi Pozisyonları")
        print(" '0' Ana Menü")
        secim = input("\nSeçiminiz: ").strip()

        if secim == '1':
            get_stock_create_order()
        elif secim == '2':
            get_stock_replace_order()
        elif secim == '3':
            get_stock_delete_order()
        elif secim == '4':
            get_stock_order_list()
        elif secim == '5':
            get_stock_positions()
        elif secim == '0':
            return
        else:
            print("Geçersiz seçim. Tekrar deneyin.")

def future_menu():
    while True:
        print("\nVadeli Emir Menüsü:")
        print(" '1' Emir Gönder")
        print(" '2' Emir Düzelt")
        print(" '3' Emir Sil")
        print(" '4' Vadeli Emir Listesi")
        print(" '5' Pozisyonlar")
        print(" '0' Ana Menü")
        secim = input("\nSeçiminiz: ").strip()

        if secim == '1':
            get_future_create_order()
        elif secim == '2':
            get_future_replace_order()
        elif secim == '3':
            get_future_delete_order()
        elif secim == '4':
            get_future_order_list()
        elif secim == '5':
            get_future_positions()
        elif secim == '0':
            return
        else:
            print("Geçersiz seçim. Tekrar deneyin.")

def ask_optional_str(prompt: str) -> Optional[str]:
    val = input(f"{prompt} (boş için Enter): ").strip()
    return val or None

def ask_optional_int(prompt: str) -> Optional[int]:
    while True:
        val = input(f"{prompt} (boş için Enter): ").strip()
        if val == "":
            return None
        if val.isdigit():
            return int(val)
        print("❌ Geçersiz girdi. Lütfen bir sayı girin veya boş bırakın.")

def ask_optional_float(prompt: str) -> Optional[float]:
    while True:
        val = input(f"{prompt} (boş için Enter): ").strip().replace(",", ".")
        if val == "":
            return None
        try:
            return float(val)
        except ValueError:
            print("❌ Geçersiz sayı. Lütfen bir ondalıklı değer girin veya boş bırakın.")

def ask_optional_bool(prompt: str) -> Optional[bool]:
    while True:
        val = input(f"{prompt} (1=Evet, 0=Hayır, boş için Enter): ").strip().lower()
        if val == "":
            return None
        if val in ("1", "y", "e", "yes", "true", "t"):
            return True
        if val in ("0", "n", "h", "no", "false", "f"):
            return False
        print("❌ Geçersiz girdi. Lütfen 1/0 veya evet/hayır yazın.")

def ask_optional_date(prompt: str) -> Optional[str]:
    while True:
        val = input(f"{prompt} (YYYY-MM-DD, boş için Enter): ").strip()
        if val == "":
            return None
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            print("❌ Geçersiz tarih formatı. YYYY-MM-DD biçiminde giriniz.")
def ask_enum_choice(prompt: str, choice_map: dict[int, str]) -> str:
    """Prompt user to select a value from a mapping."""
    while True:
        print(f"\n{prompt} seçenekleri:")
        for key, val in choice_map.items():
            print(f" {key}) {val}")
        sel = input(f"{prompt} seçiminiz: ").strip()
        if sel.isdigit() and int(sel) in choice_map:
            return choice_map[int(sel)]
        print("❌ Geçersiz seçim. Tekrar deneyin.")


def ask_enum_choice(prompt: str, mapping: dict[int, str]) -> Optional[str]:
    """Ask the user to choose one of the enum values.

    Parameters
    ----------
    prompt: str
        Text to show the user.
    mapping: dict[int, str]
        Maps menu numbers to enum strings.

    Returns
    -------
    Optional[str]
        Selected enum value or ``None`` if the user pressed Enter.
    """
    options = " ".join(f"{k}={v}" for k, v in mapping.items())
    while True:
        val = input(f"{prompt} ({options}, boş için Enter): ").strip()
        if val == "":
            return None
        if val.isdigit() and int(val) in mapping:
            return mapping[int(val)]
        print("❌ Geçersiz seçim. Tekrar deneyin.")

# ——— Portfolio Endpoints ———

# Portfolio Endpoints
def get_subaccounts():
    if api:
        resp = api.get_subaccounts()
        print(resp)

def get_account_summary():
    port = ask_optional_int("Portfolio Number")
    if port is None:
        print("❌ Portfolio Number gerekli.")
        return
    if api:
        resp = api.get_account_summary(portfolio_number=port)
        print(resp)

def get_cash_assets():
    port = ask_optional_int("Portfolio Number")
    if port is None:
        print("❌ Portfolio Number gerekli.")
        return
    if api:
        resp = api.get_cash_assets(portfolio_number=port)
        print(resp)

def get_cash_balance():
    port = ask_optional_int("Portfolio Number")
    if port is None:
        print("❌ Portfolio Number gerekli.")
        return
    if api:
        resp = api.get_cash_balance(portfolio_number=port)
        print(resp)

def get_account_overall():
    port = ask_optional_int("Portfolio Number")
    if port is None:
        print("❌ Portfolio Number gerekli.")
        return
    if api:
        resp = api.get_account_overall(portfolio_number=port)
        print(resp)

# ——— Stock Endpoints ———
# HATA Alıyor
def get_stock_create_order():
    port      = ask_optional_int("Portfolio Number")
    symbol    = ask_optional_str("Equity Code")
    qty       = ask_optional_int("Quantity")
    direction = ask_enum_choice("Direction", DIRECTION_MAP)
    price     = ask_optional_float("Price")
    method    = ask_enum_choice("Order Method", ORDER_METHOD_MAP)
    duration  = ask_enum_choice("Order Duration", ORDER_DURATION_MAP)
    mra       = ask_optional_bool("Market Risk Approval?")

    if None in (port, symbol, qty, direction, price, method, duration, mra):
        print("❌ Tüm alanlar zorunludur.")
    if None in (port, symbol, qty, price, mra):
        print("❌ Tüm alanlar doldurulmalı.")
        main
        return

    if api:
        resp = api.get_stock_create_order(
            portfolio_number=cast(int, port),
            equity_code=cast(str, symbol),
            quantity=cast(int, qty),
            direction=cast(str, direction),
            price=cast(float, price),
            order_method=cast(str, method),
            order_duration=cast(str, duration),
            market_risk_approval=cast(bool, mra)
        )
        print("Response:", resp)

def get_stock_replace_order():
    port  = ask_optional_int("Portfolio Number")
    ref   = ask_optional_str("Order Ref")
    price = ask_optional_int("New Price")
    qty   = ask_optional_int("New Quantity")

    if None in (port, ref, price, qty):
        print("❌ Tüm alanlar zorunludur.")
        print("❌ Tüm alanlar doldurulmalı.")
        return

    if api:
        resp = api.get_stock_replace_order(
            portfolio_number=cast(int, port),
            order_ref=cast(str, ref),
            price=cast(int, price),
            quantity=cast(int, qty)
        )
        print("Response:", resp)

def get_stock_delete_order():
    port = ask_optional_int("Portfolio Number")
    ref  = ask_optional_str("Order Ref to delete")
    if port is None or ref is None:
        print("❌ Tüm alanlar zorunludur.")
    if None in (port, ref):
        print("❌ Tüm alanlar doldurulmalı.")
        return
    if api:
        resp = api.get_stock_delete_order(
            portfolio_number=cast(int, port),
            order_ref=cast(str, ref)
        )
        print("Response:", resp)

# HATA Alıyor
def get_stock_order_list():
    port             = ask_optional_int("Portfolio Number")
    order_status     = ask_optional_int("Order Status")
    order_direction  = ask_optional_int("Order Direction")
    order_method     = ask_optional_int("Order Method")
    order_duration   = ask_optional_int("Order Duration")
    equity_code      = ask_optional_str("Equity Code")
    equity_type      = ask_optional_int("Equity Type")
    page_number      = ask_optional_int("Page Number")
    descending_order = ask_optional_bool("Descending Order?")

    if None in (
        port,
        order_status,
        order_direction,
        order_method,
        order_duration,
        equity_code,
        equity_type,
        page_number,
        descending_order,
    ):
        print("❌ Tüm alanlar zorunludur.")
    if None in (port, order_status, order_direction, order_method,
                order_duration, equity_code, equity_type, page_number,
                descending_order):
        print("❌ Tüm alanlar doldurulmalı.")
        return

    if api:
        resp = api.get_stock_order_list(
            portfolio_number=cast(int, port),
            order_status=cast(int, order_status),
            order_direction=cast(int, order_direction),
            order_method=cast(int, order_method),
            order_duration=cast(int, order_duration),
            equity_code=cast(str, equity_code),
            equity_type=cast(int, equity_type),
            page_number=cast(int, page_number),
            descending_order=cast(bool, descending_order),
        )
        print("Response:", resp)

def get_stock_positions():
    port         = ask_optional_int("Portfolio Number")
    equity_code  = ask_optional_str("Equity Code")
    equity_type  = ask_optional_int("Equity Type")
    without_dep  = ask_optional_bool("Without Depot?")
    without_t1   = ask_optional_bool("Without T+1 Qty?")

    if None in (port, equity_code, equity_type, without_dep, without_t1):
        print("❌ Tüm alanlar zorunludur.")
        return
        print("❌ Tüm alanlar doldurulmalı.")
        return

    if api:
        resp = api.get_stock_positions(
            portfolio_number=cast(int, port),
            equity_code=cast(str, equity_code),
            equity_type=cast(int, equity_type),
            without_depot=cast(bool, without_dep),
            without_t1_qty=cast(bool, without_t1)
        )
        print("Response:", resp)

# ——— Future Endpoints ———
def get_future_create_order():
    port      = ask_optional_int("Portfolio Number")
    contract  = ask_optional_str("Contract Code")
    direction = ask_optional_int("Direction (1=Long, 2=Short)")
    price     = ask_optional_int("Price")
    qty       = ask_optional_int("Quantity")
    method    = ask_optional_int("Order Method")
    duration  = ask_optional_int("Order Duration")
    ahs       = ask_optional_bool("After Hour Valid?")
    exp_date  = ask_optional_date("Expiration Date")

    if None in (port, contract, direction, price, qty, method, duration, ahs, exp_date):
        print("❌ Tüm alanlar zorunludur.")
        print("❌ Tüm alanlar doldurulmalı.")
        return

    if api:
        resp = api.get_future_create_order(
            portfolio_number=cast(int, port),
            contract_code=cast(str, contract),
            direction=cast(int, direction),
            price=cast(int, price),
            quantity=cast(int, qty),
            order_method=cast(int, method),
            order_duration=cast(int, duration),
            after_hour_session_valid=cast(bool, ahs),
            expiration_date=cast(str, exp_date)
        )
        print("Response:", resp)

def get_future_replace_order():
    port     = ask_optional_int("Portfolio Number")
    ref      = ask_optional_str("Order Ref")
    qty      = ask_optional_int("New Quantity")
    price    = ask_optional_int("New Price")
    otype    = ask_optional_int("Order Type")
    exp_date = ask_optional_date("Expiration Date")

    if None in (port, ref, qty, price, otype, exp_date):
        print("❌ Tüm alanlar zorunludur.")
        print("❌ Tüm alanlar doldurulmalı.")
        return

    if api:
        resp = api.get_future_replace_order(
            portfolio_number=cast(int, port),
            order_ref=cast(str, ref),
            quantity=cast(int, qty),
            price=cast(int, price),
            order_type=cast(int, otype),
            expiration_date=cast(str, exp_date)
        )
        print("Response:", resp)

def get_future_delete_order():
    port = ask_optional_int("Portfolio Number")
    ref  = ask_optional_str("Order Ref to delete")

    if port is None or ref is None:
        print("❌ Tüm alanlar zorunludur.")
        return
    if None in (port, ref):
        print("❌ Tüm alanlar doldurulmalı.")
        return

      if api:
        resp = api.get_future_delete_order(
            portfolio_number=cast(int, port),
            order_ref=cast(str, ref)
        )
        print("Response:", resp)

def get_future_order_list():
    port                      = ask_optional_int("Portfolio Number")
    order_validity_date       = ask_optional_date("Order Validity Date")
    contract_code             = ask_optional_str("Contract Code")
    contract_type             = ask_optional_int("Contract Type")
    long_short                = ask_optional_int("Long/Short (1/2)")
    pending_orders            = ask_optional_bool("Pending Orders?")
    untransmitted_orders      = ask_optional_bool("Untransmitted Orders?")
    partially_executed_orders = ask_optional_bool("Partially Executed Orders?")
    cancelled_orders          = ask_optional_bool("Cancelled Orders?")
    after_hour_session_valid  = ask_optional_bool("After Hour Session Valid?")

    if None in (
        port,
        order_validity_date,
        contract_code,
        contract_type,
        long_short,
        pending_orders,
        untransmitted_orders,
        partially_executed_orders,
        cancelled_orders,
        after_hour_session_valid,
    ):
        print("❌ Tüm alanlar zorunludur.")

        print("❌ Tüm alanlar doldurulmalı.")
        return

    if api:
        resp = api.get_future_order_list(
            portfolio_number=cast(int, port),
            order_validity_date=cast(str, order_validity_date),
            contract_code=cast(str, contract_code),
            contract_type=cast(int, contract_type),
            long_short=cast(int, long_short),
            pending_orders=cast(bool, pending_orders),
            untransmitted_orders=cast(bool, untransmitted_orders),
            partially_executed_orders=cast(bool, partially_executed_orders),
            cancelled_orders=cast(bool, cancelled_orders),
            after_hour_session_valid=cast(bool, after_hour_session_valid)
        )
        print("Response:", resp)

def get_future_positions():
    port = ask_optional_int("Portfolio Number")
    if port is None:
        print("❌ Portfolio Number gerekli.")
        return
    if api:
        resp = api.get_future_positions(portfolio_number=cast(int, port))
        print("Response:", resp)
 
def main():
    global api
    if not all([API_URL, API_KEY, API_SECRET]):
        print("❌ .env dosyasındaki API_URL, API_KEY veya API_SECRET eksik.")
        sys.exit(1)

    # Pylance için kesin tip belirtimi:
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
        print("❌ API başlatılamadı:", e)
        sys.exit(1)

    if not api._jwt_token:
        try:
            otp_resp = api.send_otp(USERNAME or "", PASSWORD or "")
        except RequestException as e:
            print("❌ OTP isteği sırasında hata:", e)
            sys.exit()

        data = otp_resp.get("data")
        if not isinstance(data, dict) or "token" not in data:
            print("❌ OTP yanıtında token bulunamadı:", otp_resp)
            sys.exit(1)

        token = data["token"]
        print("✅ OTP gönderildi.\n")
        code = input("SMS kodunu girin: ").strip()

        try:
            login_resp = api.login(token, code)
        except RequestException as e:
            print("❌ Giriş sırasında hata:", e)
            sys.exit(1)

        if not isinstance(login_resp, dict) or "data" not in login_resp:
            print("❌ Beklenmeyen login yanıtı:", login_resp)
            sys.exit(1)

        print("✅ Giriş başarılı.")
    else:
        print("✅🔑 Kayıtlı token geçerli. Menüye geçiliyor...")

    main_menu()

if __name__ == "__main__":
    main()
