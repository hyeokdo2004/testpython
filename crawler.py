# crawler.py
import asyncio
from playwright.async_api import async_playwright
import re
import os

# 게시판 ID 리스트 (테스트용은 27 하나만)
BOARD_IDS = [27]

BASE_DOMAIN = "https://www.koref.or.kr"
LIST_URL = BASE_DOMAIN + "/web/board/boardContentsListPage.do?board_id={}"

# contents_id 추출 정규식
RE_CONTENTS = re.compile(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)")

OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

async def crawl_board(board_id: int):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ko-KR",
        )
        page = await context.new_page()

        print(f"\n🔗 페이지 접속: {LIST_URL.format(board_id)}")
        await page.goto(LIST_URL.format(board_id), timeout=60000)
        await page.wait_for_load_state("networkidle")

        # 페이지 전체 HTML 가져오기
        content = await page.content()

        # contents_id 추출
        contents_ids = RE_CONTENTS.findall(content)

        # 결과 저장
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cid in contents_ids:
                f.write(cid + "\n")

        print(f"✅ 총 {len(contents_ids)}개 contents_id 추출")
        print(f"✅ 결과 저장 → {OUTPUT_FILE}")

        await context.close()
        await browser.close()

async def main():
    for bid in BOARD_IDS:
        await crawl_board(bid)

if __name__ == "__main__":
    asyncio.run(main())
