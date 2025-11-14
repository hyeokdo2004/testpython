# crawler.py
import asyncio
from playwright.async_api import async_playwright
import os

BASE_DOMAIN = "https://www.koref.or.kr"
BOARD_ID = 27
OUTPUT_FILE = os.path.join("docs", "collected_contents_ids.txt")
os.makedirs("docs", exist_ok=True)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        list_url = f"{BASE_DOMAIN}/web/board/boardContentsListPage.do?board_id={BOARD_ID}"
        print(f"🔗 페이지 접속: {list_url}")
        await page.goto(list_url, timeout=60000)

        # AJAX 요청이 끝날 때까지 대기
        try:
            response = await page.wait_for_response(lambda resp: "boardContentsList.do" in resp.url and resp.status == 200, timeout=10000)
            json_data = await response.json()
        except Exception as e:
            print("⚠️ AJAX 요청/응답 실패:", e)
            json_data = {}

        board_list = json_data.get("boardList", [])
        contents_ids = [item.get("contents_id") for item in board_list if "contents_id" in item]

        # 결과 저장
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cid in contents_ids:
                f.write(cid + "\n")

        print(f"✅ 총 {len(contents_ids)}개 contents_id 추출")
        print(f"✅ 결과 저장 → {OUTPUT_FILE}")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
