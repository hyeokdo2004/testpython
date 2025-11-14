# crawler.py
import asyncio
from playwright.async_api import async_playwright
import os
import json

BOARD_ID = 27  # 테스트용 게시판
BASE_DOMAIN = "https://www.koref.or.kr"
LIST_PAGE = BASE_DOMAIN + f"/web/board/boardContentsListPage.do?board_id={BOARD_ID}"
XHR_URL_PART = "/web/board/boardContentsList.do"

OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        contents_ids = []

        # XHR 응답 감지
        async def handle_response(response):
            url = response.url
            if XHR_URL_PART in url:
                try:
                    json_data = await response.json()
                    board_list = json_data.get("boardList", [])
                    for board in board_list:
                        cid = board.get("contents_id")
                        if cid:
                            contents_ids.append(cid)
                except:
                    pass

        page.on("response", handle_response)

        print(f"🔗 페이지 접속: {LIST_PAGE}")
        await page.goto(LIST_PAGE, timeout=60000)
        await page.wait_for_load_state("networkidle")
        # AJAX가 완료될 시간을 잠깐 대기
        await asyncio.sleep(2)

        # 결과 저장
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cid in contents_ids:
                f.write(cid + "\n")

        print(f"✅ 총 {len(contents_ids)}개 contents_id 저장 완료 → {OUTPUT_FILE}")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
