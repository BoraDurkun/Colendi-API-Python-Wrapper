#!/usr/bin/env python3
# ws_logger.py

import sys, json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    console.print("🟢 Logger başladı. Mesaj bekleniyor...\n")
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
            ts = datetime.now().strftime("%H:%M:%S")
            title = f"[bold green]📩 {ts}[/bold green]"
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
            console.print(Panel.fit(pretty, title=title, border_style="green"))
        except json.JSONDecodeError:
            console.print(f"[red]⚠ JSON parse hatası[/red]: {raw}")

if __name__ == "__main__":
    main()
