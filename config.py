# -*- coding: utf-8 -*-
"""
config.py

Uygulamanın temel konfigürasyon değerlerini içerir:
- API URL’leri ve WebSocket adresi
- Hesap kimlik bilgileri (API anahtarı, kullanıcı adı, şifre vb.)
- CLI menüleri için enum → string sözlükleri
"""

# ——————————————————————————————————————————————————————————————————————————————
# API URL ve WebSocket
# ——————————————————————————————————————————————————————————————————————————————

API_HOST   = "https://api.codyalgo.com:11443"
API_URL    = API_HOST
API_WS_URL = "wss://api.codyalgo.com:11443/ws"


# ——————————————————————————————————————————————————————————————————————————————
# Hesap Kimlik Bilgileri
# ——————————————————————————————————————————————————————————————————————————————

# API_KEY    = "cfb54634-2a6b-471d-b7ac-4a5e07171fd9"
# API_SECRET = "BAnHzC2jkGUlOYa4XcKe8w+pkziTLRjDIxX5e+GA0z4="
# USERNAME   = "30949"
# PASSWORD   = "Dnz3001*"

API_KEY    = ""
API_SECRET = ""
USERNAME   = ""
PASSWORD   = ""

# ——————————————————————————————————————————————————————————————————————————————
# CLI Menüleri için Enum → String Haritaları
# Tuşlardaki sayısal seçimler 1 bazlıdır.
# ——————————————————————————————————————————————————————————————————————————————

# Alış/Satış yönü seçimi
DIRECTION_MAP = {
    1: "BUY",
    2: "SELL",
    3: "SHORT",
}

# Emir türü seçimi
ORDER_METHOD_MAP = {
    1: "LIMIT",
    2: "MARKET",
    3: "MARKET_TO_LIMIT",
}

# Emir geçerlilik süresi seçimi
ORDER_DURATION_MAP = {
    1: "DAILY",
    2: "FILL_AND_KILL",
    3: "GOOD_TILL_CANCEL",
}

# Emir durumu seçimi
ORDER_STATUS_MAP = {
    1:  "NEW",
    2:  "NOT_SUBMITTED",
    3:  "SUBMITTED",
    4:  "PARTIALLY_REALIZED",
    5:  "REALIZED",
    6:  "AMENDMENT_REQUESTED",
    7:  "DIVIDE_WAITING",
    8:  "CANCEL_REQUESTED",
    9:  "CANCELLED",
    10: "INVALID",
    11: "PARTIALLY_SUBMITTED",
    12: "DIVIDED",
    13: "AMENDMENT_WAITING",
    14: "AMENDED",
    15: "SENDING",
    16: "EXPIRED",
    17: "WAITING_FOR_CONDITION",
    18: "WAITING",
}

# Hisse senedi tipi seçimi
EQUITY_TYPE_MAP = {
    1:  "EQUITY",
    2:  "RIGHTS",
    3:  "EXCHANGE_TRADED_FUND",
    4:  "WARRANT",
    5:  "CERTIFICATE",
    6:  "REAL_ESTATE_CERTIFICATE",
    7:  "PROVISIONAL_RECEIPT",
    8:  "EQUITY_DIVIDEND_MARKET",
    9:  "EQUITY_PRIMARY_MARKET",
    10: "EQUITY_PUBLIC_OFFER_MARKET",
    11: "GOLD_CERTIFICATE",
}

# VİOP (Vadeli İşlem ve Opsiyon) sözleşme türü
VIOP_CONTRACT_TYPE_MAP = {
    1: "FUTURE",
    2: "OPTION",
}

# VİOP pozisyon yönü
VIOP_LONG_SHORT_MAP = {
    1: "LONG",
    2: "SHORT",
}
