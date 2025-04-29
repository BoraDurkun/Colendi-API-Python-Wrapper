# ws_logger.py
import os
import asyncio
from dotenv import load_dotenv, find_dotenv
from api_client import WebSocket

def on_message(msg: str):
    print(f"[WS] {msg}")

async def run_ws():
    load_dotenv(find_dotenv())
    ws = WebSocket(
        api_url            = os.getenv("API_URL"),
        api_key            = os.getenv("API_KEY"),
        secret_key         = os.getenv("API_SECRET"),
        jwt_token          = os.getenv("JWT_TOKEN"),
        heartbeat_interval = 300,
        verbose            = False
    )
    ws.on_message = on_message
    await ws.connect()
    # sonsuz bekleyip gelenleri on_message ile bastıracak
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_ws())
