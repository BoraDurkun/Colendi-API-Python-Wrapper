import os
import sys
from typing import Optional, cast
from datetime import datetime
from requests.exceptions import RequestException
from rich import print_json

from api_client import API, WebSocket
from config import *

print(f"\n Api Url: {API_URL}")
print(f"\n Api Key: {API_KEY}")
print(f"\n Secret Key: {API_SECRET}")
print(f"\n Müşteri No: {USERNAME}")
print(f"\n Şifre: {PASSWORD}\n")

# Global API istemcisi
api: Optional[API] = None

# ——— Menu Functions ———
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
            sys.exit()
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

# ——— Choice Functions ———
def ask_optional_str(prompt: str, required: bool = False) -> Optional[str]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(boş için Enter)'} : ").strip()
        if val == "":
            if required:
                print("❌ Bu alan zorunlu, lütfen bir değer girin.")
                continue
            return None
        return val

def ask_optional_int(prompt: str, required: bool = False) -> Optional[int]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(boş için Enter)'} : ").strip()
        if val == "":
            if required:
                print("❌ Bu alan zorunlu, lütfen bir sayı girin.")
                continue
            return None
        if val.isdigit():
            return int(val)
        print("❌ Geçersiz girdi. Lütfen bir sayı girin veya boş bırakın.")

def ask_optional_float(prompt: str, required: bool = False) -> Optional[float]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(boş için Enter)'} : ").strip().replace(",", ".")
        if val == "":
            if required:
                print("❌ Bu alan zorunlu, lütfen bir ondalıklı sayı girin.")
                continue
            return None
        try:
            return float(val)
        except ValueError:
            print("❌ Geçersiz sayı. Lütfen ondalıklı bir değer girin veya boş bırakın.")

def ask_optional_bool(prompt: str, required: bool = False) -> Optional[bool]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(boş için Enter)'} (1=Evet, 0=Hayır): ").strip().lower()
        if val == "":
            if required:
                print("❌ Bu alan zorunlu, lütfen evet veya hayır girin.")
                continue
            return None
        if val in ("1", "y", "e", "yes", "true", "t"):
            return True
        if val in ("0", "n", "h", "no", "false", "f"):
            return False
        print("❌ Geçersiz girdi. Lütfen 1/0 veya evet/hayır yazın.")

def ask_optional_date(prompt: str, required: bool = False) -> Optional[str]:
    while True:
        val = input(f"{prompt}{' (zorunlu)' if required else '(boş için Enter)'} (YYYY-MM-DD): ").strip()
        if val == "":
            if required:
                print("❌ Bu alan zorunlu, lütfen geçerli bir tarih girin.")
                continue
            return None
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            print("❌ Geçersiz tarih formatı. YYYY-MM-DD biçiminde giriniz.")

def ask_enum_choice(
    prompt: str,
    choice_map: dict[int, str],
    required: bool = False
) -> Optional[str]:
    """
    :param prompt: Soru metni
    :param choice_map: {1: "A", 2: "B", ...}
    :param required: True ise boş geçilmesine izin vermez
    :return: Seçilen değer veya None
    """
    while True:
        print(f"\n{prompt} seçenekleri:")
        for key, val in choice_map.items():
            print(f" {key}) {val}")
        sel = input(f"{prompt} seçiminiz{' (zorunlu)' if required else '(boş için Enter)'}: ").strip()
        
        if sel == "":
            if required:
                print("❌ Bu alan zorunlu, lütfen bir seçim yapın.")
                continue
            return None
        
        if sel.isdigit() and int(sel) in choice_map:
            return choice_map[int(sel)]
        
        print("❌ Geçersiz seçim. Tekrar deneyin.")

# ——— Portfolio Endpoints ———
def get_subaccounts():
    if api:
        resp = api.get_subaccounts()
        print_json(data=resp)

def get_account_summary():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_account_summary(portfolio_number=port)
        print_json(data=resp)

def get_cash_assets():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_cash_assets(portfolio_number=port)
        print_json(data=resp)

def get_cash_balance():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_cash_balance(portfolio_number=port)
        print_json(data=resp)

def get_account_overall():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    assert port is not None
    if api:
        resp = api.get_account_overall(portfolio_number=port)
        print_json(data=resp)

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
        print_json(data=resp)

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
        print_json(data=resp)

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
        print_json(data=resp)

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
        print("❌ Zorumlu alanlar doldurulmalı.")
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
        print_json(data=resp)

def get_stock_positions():
    port         = ask_optional_int("Portfolio Number", required=True)
    equity_code  = ask_optional_str("Equity Code")
    equity_type  = ask_enum_choice("Equity Type", EQUITY_TYPE_MAP)
    without_dep  = ask_optional_bool("Without Depot?")
    without_t1   = ask_optional_bool("Without T+1 Qty?")

    if (port is None):
        print("❌ Zorunlu alanlar doldurulmalı.")
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
        print_json(data=resp)

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
        print_json(data=resp)

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
        print_json(data=resp)

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
        print_json(data=resp)

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
        print_json(data=resp)

def get_future_positions():
    port = ask_optional_int("Portfolio Number", required=True)
    if port is None:
        return
    if api:
        resp = api.get_future_positions(portfolio_number=port)
        print_json(data=resp)
 
def main():
    global api
    if not all([API_URL, API_KEY, API_SECRET]):
        print("❌ config.py dosyasındaki API_URL, API_KEY veya API_SECRET eksik.")
        sys.exit()

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
        sys.exit()

    if not api._jwt_token:
        try:
            otp_resp = api.send_otp(USERNAME or "", PASSWORD or "")
        except RequestException as e:
            print("❌ OTP isteği sırasında hata:", e)
            sys.exit()

        data = otp_resp.get("data")
        if not isinstance(data, dict) or "token" not in data:
            print("❌ OTP yanıtında token bulunamadı:", otp_resp)
            sys.exit()

        token = data["token"]
        print("✅ OTP gönderildi.\n")
        code = input("SMS kodunu girin: ").strip()

        try:
            login_resp = api.login(token, code)
        except RequestException as e:
            print("❌ Giriş sırasında hata:", e)
            sys.exit()

        if not isinstance(login_resp, dict) or "data" not in login_resp:
            print("❌ Beklenmeyen login yanıtı:", login_resp)
            sys.exit()

        print("✅ Giriş başarılı.")
    else:
        print("✅🔑 Kayıtlı token geçerli. Menüye geçiliyor...")

    main_menu()

if __name__ == "__main__":
    main()
