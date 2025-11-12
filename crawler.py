import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

# ✅ 결과 저장 폴더 (GitHub Pages용)
OUTPUT_DIR = os.path.join(os.getcwd(), "docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def crawl_board(board_id, max_pages=1):
    """지정된 board_id 게시판을 수집"""
    base_url = f"https://www.koref.or.kr/web/board/boardContentsListPage.do?board_id={board_id}&miv_pageNo="
    print(f"\n==============================")
    print(f"📁 게시판 board_id={board_id} 시작")
    print(f"==============================")

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for page_no in range(1, max_pages + 1):
            url = f"{base_url}{page_no}"
            print(f"\n--- 📄 페이지 {page_no} → {url} ---")
            await page.goto(url, wait_until="load", timeout=60000)

            try:
                await page.wait_for_selector("ul.boardList", timeout=30000)
            except Exception:
                print(f"[WARN] 게시판 목록이 로드되지 않음 (page={page_no})")
                continue

            # 게시물 목록 추출
            items = await page.query_selector_all("ul.boardList li")
            for item in items:
                title = await item.inner_text()
                href = await item.get_attribute("onclick")
                results.append(f"{title.strip()} | onclick={href}")

        await browser.close()

    return results


async def main():
    board_ids = [27]  # 수집할 게시판 ID 목록
    all_results = []

    for bid in board_ids:
        result = await crawl_board(bid, max_pages=2)
        all_results.extend(result)

    # ✅ 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"crawl_result_{timestamp}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        for line in all_results:
            f.write(line + "\n")

    print(f"\n✅ 결과 저장 완료 → {output_path}")


if __name__ == "__main__":
    # GitHub 환경에서 playwright 브라우저 미설치 시 자동 설치
    try:
        import playwright.__main__ as playwright_main
        os.system("playwright install --with-deps chromium")
    except Exception as e:
        print(f"[WARN] Playwright 설치 중 문제 발생: {e}")

    asyncio.run(main())
