import os
import sys
from dotenv import load_dotenv, find_dotenv
from api_client import API, WebSocket

# ——— Ortam değişkenlerini yükle ———
load_dotenv(find_dotenv())

API_URL    = os.getenv("API_URL")
API_KEY    = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
USERNAME   = os.getenv("USERNAME")
PASSWORD   = os.getenv("PASSWORD")

# Global API istemcisi
api: API

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

# ——— Portfolio Endpoints———
def get_subaccounts():
    resp = api.get_subaccounts()
    print(resp)

def get_account_summary():
    port = int(input("Portfolio Number: ").strip())
    resp = api.get_account_summary(portfolio_number=port)
    print(resp)

def get_cash_assets():
    port = int(input("Portfolio Number: ").strip())
    resp = api.get_cash_assets(portfolio_number=port)
    print(resp)

def get_cash_balance():
    port = int(input("Portfolio Number: ").strip())
    resp = api.get_cash_balance(portfolio_number=port)
    print(resp)

def get_account_overall():
    port = int(input("Portfolio Number: ").strip())
    resp = api.get_account_overall(portfolio_number=port)
    print(resp)

# ——— Stock Endpoints ———
def get_stock_create_order():
    kind = input("Emir tipi (1=Stock, 2=Future): ").strip()
    port = int(input("Portfolio Number: ").strip())
    if kind == '1':
        symbol = input("Equity Code: ").strip()
        qty    = int(input("Quantity: ").strip())
        direction = int(input("Direction (1=Buy, 2=Sell): ").strip())
        price  = int(input("Price: ").strip())
        method = int(input("Order Method: ").strip())
        duration = int(input("Order Duration: ").strip())
        mra = input("Market Risk Approval? (y/n): ").strip().lower() in ('y','e','yes','true')
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
    else:
        contract = input("Contract Code: ").strip()
        direction = int(input("Direction (1=Long, 2=Short): ").strip())
        price  = int(input("Price: ").strip())
        qty    = int(input("Quantity: ").strip())
        method = int(input("Order Method: ").strip())
        duration = int(input("Order Duration: ").strip())
        ahs = input("After Hour Valid? (y/n): ").strip().lower() in ('y','e','yes','true')
        exp_date = input("Expiration Date (YYYY-MM-DD): ").strip()
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

def get_stock_replace_order():
    port = int(input("Portfolio Number: ").strip())
    ref  = input("Order Ref: ").strip()
    price = int(input("New Price: ").strip())
    qty   = int(input("New Quantity: ").strip())
    resp = api.get_stock_replace_order(
        portfolio_number=port,
        order_ref=ref,
        price=price,
        quantity=qty
    )
    print("Response:", resp)

def get_stock_delete_order():
    port = int(input("Portfolio Number: ").strip())
    ref  = input("Order Ref to delete: ").strip()
    resp = api.get_stock_delete_order(
        portfolio_number=port,
        order_ref=ref
    )
    print("Response:", resp)

def get_stock_order_list():
    port = int(input("Portfolio Number: ").strip())
    order_status = int(input("order_status: ").strip())
    order_direction = int(input("order_direction: ").strip())
    order_method = int(input("order_method: ").strip())
    order_duration = int(input("order_duration: ").strip())
    equity_code  = input("Sembol Kodu: ").strip()
    equity_type = int(input("Sembol tipi: ").strip())
    page_number = int(input("Sayfa numarası: ").strip())
    descending_order = bool(input("Tersine Sıralama (1 veya 0 giriniz): ").strip())
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
    port = int(input("Portfolio Number: ").strip())
    equity_code = input("equity_code: ").strip()
    equity_type = int(input("equity_type: ").strip())
    without_depot = bool(input("without_depot (1 veya 0 giriniz): ").strip())
    without_t1_qty = bool(input("without_t1_qty (1 veya 0 giriniz): ").strip())
    resp = api.get_stock_positions(portfolio_number=port,
        equity_code=equity_code,
        equity_type=equity_type,
        without_depot=without_depot,
        without_t1_qty=without_t1_qty,
     )
    print("Response:", resp)

# ——— Future Endpoints———
def get_future_create_order():
    port = int(input("Portfolio Number: ").strip())
    contract = input("Contract Code: ").strip()
    direction = int(input("Direction (1=Long, 2=Short): ").strip())
    price  = int(input("Price: ").strip())
    qty    = int(input("Quantity: ").strip())
    method = int(input("Order Method: ").strip())
    duration = int(input("Order Duration: ").strip())
    ahs = input("After Hour Valid? (y/n): ").strip().lower() in ('y','e','yes','true')
    exp_date = input("Expiration Date (YYYY-MM-DD): ").strip()
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

def get_future_replace_order():
    port = int(input("Portfolio Number: ").strip())
    ref  = input("Order Ref: ").strip()
    qty   = int(input("New Quantity: ").strip())
    price = int(input("New Price: ").strip())
    otype = int(input("Order Type: ").strip())
    exp_date = input("Expiration Date (YYYY-MM-DD): ").strip()
    resp = api.get_future_replace_order(
        portfolio_number=port,
        order_ref=ref,
        quantity=qty,
        price=price,
        order_type=otype,
        expiration_date=exp_date
    )
    print("Response:", resp)

def get_future_delete_order():
    port = int(input("Portfolio Number: ").strip())
    ref  = input("Order Ref to delete: ").strip()
    resp = api.get_future_delete_order(
        portfolio_number=port,
        order_ref=ref
    )
    print("Response:", resp)

def get_future_order_list():
    port = int(input("Portfolio Number: ").strip())
    order_validity_date = input("Order validity date: ").strip()
    contract_code = input("contract_code: ").strip()
    contract_type = int(input("contract_type: ").strip())
    long_short = int(input("long_short: ").strip())
    pending_orders = bool(input("pending_orders (1 veya 0 giriniz):  ").strip())
    untransmitted_orders  = bool(input("untransmitted_orders (1 veya 0 giriniz):  ").strip())
    partially_executed_orders = bool(input("partially_executed_orders (1 veya 0 giriniz):  ").strip())
    cancelled_orders = bool(input("cancelled_orders (1 veya 0 giriniz):  ").strip())
    after_hour_session_valid = bool(input("after_hour_session_valid (1 veya 0 giriniz): ").strip())
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
    port = int(input("Portfolio Number: ").strip())
    resp = api.get_stock_positions(portfolio_number=port
     )
    print("Response:", resp)
    
def main():
    global api
    api = API.get_api(
        api_url    = API_URL,
        api_key    = API_KEY,
        secret_key = API_SECRET,
        verbose    = True
    )

    # İlk OTP + login
    otp_resp = api.send_otp(USERNAME, PASSWORD)
    token    = otp_resp["data"]["token"]
    print("OTP gönderildi, token:", token)
    code = input("SMS kodunu girin: ").strip()
    login_resp = api.login(token, code)
    print("Login başarılı:", login_resp)

    main_menu()

if __name__ == "__main__":
    main()
