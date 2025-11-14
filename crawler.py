# crawler.py
import asyncio
from playwright.async_api import async_playwright
import re
import os

# 수집할 게시판 URL (첫 페이지만)
BOARD_URLS = [
    "https://www.koref.or.kr/web/board/boardContentsListPage.do?board_id=27"
]

# contents_id 추출용 정규식
RE_CONTENTS = re.compile(r"contentsView\(['\"]([0-9a-fA-F]+)['\"]\)")

# 결과 파일
OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

async def crawl_board(page, url):
    print(f"🔗 페이지 접속: {url}")
    await page.goto(url, timeout=60000)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)  # AJAX 렌더링 대기

    # 페이지 HTML 가져오기
    html = await page.content()

    # contents_id 추출
    ids = RE_CONTENTS.findall(html)
    print(f"✅ 총 {len(ids)}개 contents_id 추출")

    # 파일 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cid in ids:
            f.write(cid + "\n")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for url in BOARD_URLS:
            await crawl_board(page, url)

        await context.close()
        await browser.close()
        print(f"✅ 결과 저장 → {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
