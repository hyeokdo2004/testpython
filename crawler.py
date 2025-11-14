# crawler.py
import asyncio
from playwright.async_api import async_playwright
import re
import os

BOARD_ID = 27  # 테스트용, 필요하면 리스트로 확장 가능
BASE_URL = "https://www.koref.or.kr"
LIST_PAGE = f"{BASE_URL}/web/board/boardContentsListPage.do?board_id={BOARD_ID}"

OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

# contents_id 추출용 정규식
RE_CONTENTS = re.compile(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"\n🔗 페이지 접속: {LIST_PAGE}")
        await page.goto(LIST_PAGE, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # 페이지 전체 HTML 가져오기
        html = await page.content()

        # contents_id 추출
        ids = RE_CONTENTS.findall(html)
        print(f"✅ 총 {len(ids)}개 contents_id 추출")

        # 결과 저장
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cid in ids:
                f.write(cid + "\n")

        print(f"✅ 결과 저장 → {OUTPUT_FILE}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
