# crawler.py
import asyncio
from playwright.async_api import async_playwright
import re
import os

# 첫 번째 게시판 URL
BOARD_URL = "https://www.koref.or.kr/web/board/boardContentsListPage.do?board_id=27"

# contents_id 추출용 정규식
RE_CONTENTS = re.compile(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)")

# 출력 파일
OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🔗 페이지 접속: {BOARD_URL}")
        await page.goto(BOARD_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # 페이지 내 a 태그 onclick 속성 추출
        link_data = await page.eval_on_selector_all(
            "a",
            """els => els.map(a => a.getAttribute('onclick') || '')"""
        )

        contents_ids = set()
        for onclick in link_data:
            m = RE_CONTENTS.search(onclick)
            if m:
                contents_ids.add(m.group(1))

        # 결과 저장
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cid in sorted(contents_ids):
                f.write(cid + "\n")
                print(f"📝 발견: {cid}")

        print(f"\n✅ 총 {len(contents_ids)}개 contents_id 저장 완료 → {OUTPUT_FILE}")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
