# crawler.py
import asyncio
from playwright.async_api import async_playwright
import re
import os

BASE_URL = "https://www.koref.or.kr/web/board/boardContentsListPage.do?board_id=27"
OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

# contentsView('...') 추출용 정규식
RE_CONTENTS = re.compile(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🔗 페이지 접속: {BASE_URL}")
        await page.goto(BASE_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # a 태그의 onclick 속성에서 contents_id 추출
        elements = await page.query_selector_all("a")
        contents_ids = []
        for el in elements:
            onclick = await el.get_attribute("onclick") or ""
            m = RE_CONTENTS.search(onclick)
            if m:
                contents_ids.append(m.group(1))

        print(f"✅ 총 {len(contents_ids)}개 contents_id 저장 완료 → {OUTPUT_FILE}")

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cid in contents_ids:
                f.write(cid + "\n")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
