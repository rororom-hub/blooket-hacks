import os
import subprocess
import sys
import socket
from pathlib import Path
from playwright.async_api import Browser, async_playwright, Page, Locator

CDP_PORT = 9222
CDP_URL = f"http://localhost:{CDP_PORT}"
PROFILE_DIR = Path.home() / ".blooket_chrome_profile"
START_PAGE = "https://dashboard.blooket.com/"

def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def launch_chrome() -> None:
    """Запускает Chrome с открытым CDP-портом и отдельным профилем, если он еще не запущен."""
    if is_port_open(CDP_PORT):
        print(f"[*] Chrome уже запущен на порту {CDP_PORT}.")
        return

    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_bin = next((p for p in chrome_paths if os.path.exists(p) or "/" not in p), None)
    if not chrome_bin:
        print("[!] Не удалось найти Chrome автоматически. Запустите его вручную с флагом --remote-debugging-port=9222")
        sys.exit(1)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome_bin,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--mute-audio",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        START_PAGE
    ]

    print(f"[*] Запуск Chrome с профилем: {PROFILE_DIR}")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    launch_chrome()