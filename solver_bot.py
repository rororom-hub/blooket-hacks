import asyncio
import random
import sys
import cdp

from playwright.async_api import Browser, Locator, Page, async_playwright
from mine import get_page, human_click

GAME_URL_PART = "solo.blooket.com"


async def read_question(page: Page) -> str | None:
    """Возвращает текст текущего вопроса или None, если вопроса на экране нет."""
    # TODO: локатор вопроса
    raise NotImplementedError


async def pick_answer(page: Page, question: str) -> Locator | None:
    """Выбирает кнопку ответа для вопроса."""
    # TODO: логика выбора ответа
    raise NotImplementedError


async def run() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(cdp.CDP_URL)
        if not browser.contexts:
            print("[!] В браузере нет активных контекстов.")
            sys.exit(1)

        print(f"[*] Начинаем цикл решений")

        while True:
            page = await get_page(browser, GAME_URL_PART, timeout=0.5)

            question = await read_question(page)
            if question is None:
                await asyncio.sleep(0.2)
                continue

            answer = await pick_answer(page, question)
            if answer is not None and await human_click(answer):
                completed += 1
                print(f"[*] Прогресс: {completed}/{rounds}")
                await asyncio.sleep(random.uniform(0.15, 0.3))

            # TODO: переход к следующему вопросу (в mine.py это Space)

        print("СКРИПТ ОКОНЧЕН")
        await browser.close()


def cli_entry() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n[!] Выход.")


if __name__ == "__main__":
    cli_entry()