import argparse
import asyncio
import os
import random
import socket
import subprocess
import sys
from pathlib import Path
from playwright.async_api import Browser, async_playwright, Page, Locator


CDP_PORT = 9222
CDP_URL = f"http://localhost:{CDP_PORT}"
PROFILE_DIR = Path.home() / ".blooket_chrome_profile"
START_PAGE = "https://dashboard.blooket.com/"
ANSWER_TEXT = "yes"
ANSWER_COUNT = 255

def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def launch_chrome_cdp(port: int = CDP_PORT) -> None:
    """Запускает Chrome с открытым CDP-портом и отдельным профилем, если он еще не запущен."""
    if is_port_open(port):
        print(f"[*] Chrome уже запущен на порту {port}.")
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
        f"--remote-debugging-port={port}",
        f"--user-data-dir={PROFILE_DIR}",
        "--mute-audio",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        START_PAGE,
    ]

    print(f"[*] Запуск Chrome с профилем: {PROFILE_DIR}")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def human_click(page: Page, locator: Locator) -> bool:
    """Наведение и клик со случайным смещением и проверкой, что кнопка не перекрыта."""
    try:
        box = await locator.bounding_box(timeout=800)
        if not box or box["width"] <= 0 or box["height"] <= 0:
            return False

        pos_x = box["width"] * random.uniform(0.22, 0.78)
        pos_y = box["height"] * random.uniform(0.22, 0.78)

        await locator.click(
            position={"x": pos_x, "y": pos_y},
            delay=random.uniform(15, 35),
            timeout=600,
        )
        return True
    except Exception:
        return False


async def get_page(browser: Browser, url_part: str, timeout: float = 5.0) -> Page:
    context = browser.contexts[0]
    steps = max(1, int(timeout * 10))
    for _ in range(steps):
        page = next((p for p in context.pages if url_part in p.url), None)
        if page:
            return page
        await asyncio.sleep(0.1)

    print(f"[!] Не нашлась страница `{url_part}`")
    sys.exit(1)


async def navigate_to_solo(browser: Browser) -> None:
    """Выполняет навигацию от страницы сета до старта квиза в режиме Study."""
    print("[*] Навигация к режиму Solo -> Study...")

    page = await get_page(browser, START_PAGE)

    sets_btn = page.locator('span:has-text("My Sets")')
    await sets_btn.click(timeout=3000)

    solo_btn = page.locator('button:has-text("Solo")').first
    await solo_btn.click(timeout=3000)

    page = await get_page(browser, "play.blooket.com")
    study_mode = page.locator('img[alt="Select Study"]').first
    await study_mode.click(timeout=3000)

    play_mode_btn = page.locator('button:has-text("Play")').first
    await play_mode_btn.click(timeout=3000)

    page = await get_page(browser, "solo.blooket.com")
    start_play_btn = page.locator('span:has-text("Play")').first
    await start_play_btn.click(timeout=5000)

    await asyncio.sleep(0.4)
    print("[*] Переход к игровому экрану выполнен успешно.")

async def finish_study_game(browser: Browser) -> None:
    """Завершает игру (End Now -> Yes -> Next) и забирает награду."""
    print("[*] Завершаем игру и забираем награду...")
    try:
        page = await get_page(browser, "solo.blooket.com", timeout=2.0)

        # 1. Нажимаем кнопку с флажком End Now
        end_btn = page.locator('button[class*="EndNowFlag_button"], button:has(img[alt="End Now"])').first
        await end_btn.wait_for(state="visible", timeout=3000)
        await human_click(page, end_btn)

        # 2. Подтверждаем выход (Yes)
        yes_btn = page.locator('button[class*="_button_"]').filter(has_text="Yes").first
        await yes_btn.wait_for(state="visible", timeout=3000)
        await human_click(page, yes_btn)

        # 3. Ждем появления кнопки Next (анимация итогов может занять 2-4 секунды) и нажимаем
        next_btn = page.locator('button[class*="_button_"]').filter(has_text="Next").last
        try:
            await next_btn.wait_for(state="visible", timeout=6000)
            await asyncio.sleep(random.uniform(0.2, 0.4))
            await human_click(page, next_btn)
            print("[+] Награда успешно получена!")
        except Exception:
            print("[*] Экран Next не найден (возможно, открылось Daily Wheel - покрутите его в окне).")
    except Exception as e:
        print(f"[!] Не удалось автоматически завершить игру: {e}")


async def farm_study_mode(answers_count: int, answer_text: str | None) -> None:
    async with async_playwright() as playwright:

        browser = await playwright.chromium.connect_over_cdp(CDP_URL)
        if not browser.contexts:
            print("[!] В браузере нет активных контекстов.")
            sys.exit(1)

        await navigate_to_solo(browser)

        print(f"[*] Начинаем цикл: {answers_count} ответов (~{answers_count * 2} монет)")

        completed = 0
        next_pause_at = random.randint(35, 50)

        while completed < answers_count:
            try:
                page = await get_page(browser, "solo.blooket.com", timeout=0.5)

                answer_locator = page.locator('button[class*="_answerButton_"]').filter(has_text=answer_text).last

                if await answer_locator.is_visible(timeout=800):
                    clicked = await human_click(page, answer_locator)
                    if clicked:
                        completed += 1
                        await asyncio.sleep(random.uniform(0.16, 0.24))

                        await page.keyboard.press("Space")
                        await asyncio.sleep(random.uniform(0.10, 0.18))

                        # Редкие короткие паузы для естественности
                        if completed >= next_pause_at:
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            next_pause_at = completed + random.randint(35, 50)

                        print(f"[*] Прогресс: {completed}/{answers_count}")
                        continue  # Сразу переходим к следующему вопросу, минуя fallback
                else:
                    print("Skipping")

                # Fallback на случай задержки интерфейса
                await page.keyboard.press("Space")
                await asyncio.sleep(random.uniform(0.15, 0.3))

            except KeyboardInterrupt:
                print("\n[!] Остановлено пользователем.")
                break
            except Exception:
                await asyncio.sleep(0.2)

        if completed >= answers_count:
            await finish_study_game(browser)

        print("СКРИПТ ОКОНЧЕН")
        await browser.close()


def cli_entry() -> None:
    parser = argparse.ArgumentParser(description="Blooket Study Mode CDP Automation")
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Автоматически запустить Chrome с нужным портом отладки (9222)",
    )
    parser.add_argument(
        "-n",
        "--answers",
        type=int,
        default=ANSWER_COUNT,
        help="Количество ответов (по умолчанию: 255 для гарантированных 500 монет)",
    )
    parser.add_argument(
        "-t",
        "--text",
        type=str,
        default=ANSWER_TEXT,
        help="Точный текст правильного ответа (если не указан, ищет первую карточку ответа автоматически)",
    )
    args = parser.parse_args()

    if args.launch:
        launch_chrome_cdp()
        print("[*] Войдите в аккаунт Blooket, потом запустите скрипт без флага --launch.")
        return

    try:
        launch_chrome_cdp()
        asyncio.run(farm_study_mode(args.answers, args.text))
    except KeyboardInterrupt:
        print("\n[!] Выход.")


if __name__ == "__main__":
    cli_entry()