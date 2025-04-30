import os
import sys
from dotenv import load_dotenv, find_dotenv
from api_client import API, WebSocket
from typing import Optional
from datetime import datetime
import sys
from requests.exceptions import RequestException

# ——— Ortam değişkenlerini yükle ———
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
        print("\nEmir Menüsü — Lütfen yapmak istediğiniz işlemi seçin:")
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
        print("\nEmir Menüsü — Lütfen yapmak istediğiniz işlemi seçin:")
        print(" '1' Future Emir Gönder")
        print(" '2' Future Emir Düzelt")
        print(" '3' Future Emir Sil (Stock)")
        print(" '4' Future Emir Listesi")
        print(" '5' Future pozisyonları")
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

# ——— Optional-input helper’ları ———

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

def ask_optional_bool(prompt: str) -> Optional[bool]:
    while True:
        val = input(f"{prompt} (1=Evet, 0=Hayır, boş için Enter): ").strip().lower()
        if val == "":
            return None
        if val in ("1",):
            return True
        if val in ("0",):
            return False
        if val in ("y", "e", "yes", "true", "t"):
            return True
        if val in ("n", "h", "no", "false", "f"):
            return False
        print("❌ Geçersiz girdi. Lütfen 1/0, y/n ya da boş girin.")

def ask_optional_date(prompt: str) -> Optional[str]:
    while True:
        val = input(f"{prompt} (YYYY-MM-DD veya boş için Enter): ").strip()
        if val == "":
            return None
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            print("❌ Geçersiz tarih. Lütfen YYYY-MM-DD formatında ya da boş bırakın.")

# ——— Portfolio Endpoints ———

def get_subaccounts():
    resp = api.get_subaccounts()
    print(resp)

def get_account_summary():
    port = ask_optional_int("Portfolio Number")
    resp = api.get_account_summary(portfolio_number=port)
    print(resp)

def get_cash_assets():
    port = ask_optional_int("Portfolio Number")
    resp = api.get_cash_assets(portfolio_number=port)
    print(resp)

def get_cash_balance():
    port = ask_optional_int("Portfolio Number")
    resp = api.get_cash_balance(portfolio_number=port)
    print(resp)

def get_account_overall():
    port = ask_optional_int("Portfolio Number")
    resp = api.get_account_overall(portfolio_number=port)
    print(resp)

# ——— Stock Endpoints ———
# HATA Alıyor
def get_stock_create_order():
    port      = ask_optional_int("Portfolio Number")
    symbol    = ask_optional_str("Equity Code")
    qty       = ask_optional_int("Quantity")
    direction = ask_optional_int("Direction (1=Buy, 2=Sell)")
    price     = ask_optional_int("Price")
    method    = ask_optional_int("Order Method")
    duration  = ask_optional_int("Order Duration")
    mra       = ask_optional_bool("Market Risk Approval?")
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
    print("Response:", resp)

def get_stock_replace_order():
    port  = ask_optional_int("Portfolio Number")
    ref   = ask_optional_str("Order Ref")
    price = ask_optional_int("New Price")
    qty   = ask_optional_int("New Quantity")
    resp = api.get_stock_replace_order(
        portfolio_number=port,
        order_ref=ref,
        price=price,
        quantity=qty
    )
    print("Response:", resp)

def get_stock_delete_order():
    port = ask_optional_int("Portfolio Number")
    ref  = ask_optional_str("Order Ref to delete")
    resp = api.get_stock_delete_order(
        portfolio_number=port,
        order_ref=ref
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
    print("Response:", resp)

def get_stock_positions():
    # 1) Portfolio Number
    while True:
        port_str = input("Portfolio Number: ").strip()
        if port_str.isdigit():
            port = int(port_str)
            break
        print("❌ Geçersiz sayı. Lütfen sadece rakam girin.")

    # 2) Equity Code (isterseniz boş da bırakabilirsiniz)
    eq_code_input = input("Equity Code (boş bırakmak için Enter): ").strip()
    equity_code: Optional[str] = eq_code_input or None

    # 3) Equity Type (sayısal veya boş)
    while True:
        eq_type_str = input("Equity Type (sayısal veya boş): ").strip()
        if eq_type_str == "":
            equity_type = None
            break
        if eq_type_str.isdigit():
            equity_type = int(eq_type_str)
            break
        print("❌ Geçersiz girdi. Lütfen bir sayı girin veya boş bırakın.")

    # 4) Boolean değerleri 1/0 veya y/n ile alalım
    def ask_bool(prompt: str) -> bool:
        while True:
            val = input(prompt + " (1=Evet, 0=Hayır): ").strip().lower()
            if val in ("1", "0"):
                return val == "1"
            if val in ("y", "e", "yes", "true", "t"):
                return True
            if val in ("n", "h", "no", "false", "f"):
                return False
            print("❌ Geçersiz girdi. Lütfen 1 veya 0 girin.")

    without_depot   = ask_bool("without_depot")
    without_t1_qty  = ask_bool("without_t1_qty")

    # 5) Çağrıyı yapıp sonucu yazdıralım
    resp = api.get_stock_positions(
        portfolio_number=port,
        equity_code=equity_code,
        equity_type=equity_type,
        without_depot=without_depot,
        without_t1_qty=without_t1_qty,
    )
    print("Response:", resp)

# ——— Future Endpoints ———
# HATA Alıyor
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
    print("Response:", resp)

# HATA Alıyor
def get_future_replace_order():
    port     = ask_optional_int("Portfolio Number")
    ref      = ask_optional_str("Order Ref")
    qty      = ask_optional_int("New Quantity")
    price    = ask_optional_int("New Price")
    otype    = ask_optional_int("Order Type")
    exp_date = ask_optional_date("Expiration Date")
    resp = api.get_future_replace_order(
        portfolio_number=port,
        order_ref=ref,
        quantity=qty,
        price=price,
        order_type=otype,
        expiration_date=exp_date
    )
    print("Response:", resp)

# HATA Alıyor
def get_future_delete_order():
    port = ask_optional_int("Portfolio Number")
    ref  = ask_optional_str("Order Ref to delete")
    resp = api.get_future_delete_order(
        portfolio_number=port,
        order_ref=ref
    )
    print("Response:", resp)

# HATA Alıyor
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
    print("Response:", resp)

def get_future_positions():
    port = ask_optional_int("Portfolio Number")
    resp = api.get_future_positions(portfolio_number=port)
    print("Response:", resp)

    
def main():
    # API nesnesini oluştur
    global api
    api = API.get_api(
        api_url    = API_URL,
        api_key    = API_KEY,
        secret_key = API_SECRET,
        verbose    = True
    )

    # Eğer kaydedilmiş geçerli bir token yoksa, OTP+login ile al
    if not api._jwt_token:
        try:
            otp_resp = api.send_otp(USERNAME, PASSWORD)
        except RequestException as e:
            print("❌ OTP isteği sırasında HTTP hatası:", e)
            sys.exit(1)

        # OTP yanıtını kontrol edelim
        if not isinstance(otp_resp, dict):
            print("❌ Beklenmeyen OTP yanıtı:", otp_resp)
            sys.exit(1)

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
            print("❌ Login sırasında HTTP hatası:", e)
            sys.exit(1)

        if not isinstance(login_resp, dict) or "data" not in login_resp:
            print("❌ Beklenmeyen login yanıtı:", login_resp)
            sys.exit(1)

        print("✅Login başarılı")
    else:
        # Zaten token varsa, doğrudan menüye geçebiliriz
        print("✅🔑 Kayıtlı token hala geçerli, direkt menüye geçiliyor.")

    main_menu()

if __name__ == "__main__":
    main()
