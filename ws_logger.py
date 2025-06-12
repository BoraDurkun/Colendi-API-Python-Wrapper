import os
import asyncio
from dotenv import load_dotenv, find_dotenv
from api_client import WebSocket
from config import *
def on_message(msg: str):
    print(f"[WS] {msg}")

async def run_ws():

    api_url   = API_URL
    api_key   = API_KEY
    secret_key = API_SECRET
    jwt_token = os.getenv("JWT_TOKEN")

    # Ortam değişkenlerinin None olmamasını garanti altına al
    if api_url is None:
        raise EnvironmentError("API_URL ortam değişkeni tanımlı değil.")
    if api_key is None:
        raise EnvironmentError("API_KEY ortam değişkeni tanımlı değil.")
    if secret_key is None:
        raise EnvironmentError("API_SECRET ortam değişkeni tanımlı değil.")
    if jwt_token is None:
        raise EnvironmentError("JWT_TOKEN ortam değişkeni tanımlı değil.")

    ws = WebSocket(
        api_url            = api_url,
        api_key            = api_key,
        secret_key         = secret_key,
        jwt_token          = jwt_token,
        heartbeat_interval = 300,
        verbose            = False
    )
    ws.on_message = on_message
    await ws.connect()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_ws())
