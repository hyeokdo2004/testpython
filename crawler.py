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

        contents_ids = []

        # 응답 이벤트 처리
        async def handle_response(response):
            if "boardContentsList.do" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    for item in data.get("boardList", []):
                        cid = item.get("contents_id")
                        if cid:
                            contents_ids.append(cid)
                except Exception as e:
                    print("⚠️ JSON 파싱 실패:", e)

        page.on("response", handle_response)

        list_url = f"{BASE_DOMAIN}/web/board/boardContentsListPage.do?board_id={BOARD_ID}"
        print(f"🔗 페이지 접속: {list_url}")
        await page.goto(list_url, timeout=60000)

        # AJAX 로딩 시간 대기
        await asyncio.sleep(3)

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
