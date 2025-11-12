import asyncio
from playwright.async_api import async_playwright
import re
import json
import os

# 수집 대상 게시판
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]
BASE_LIST_URL = "https://www.koref.or.kr/web/board/boardContentsListPage.do?board_id={bid}&miv_pageNo={page}"
BASE_DETAIL_URL = "https://www.koref.or.kr/web/board/boardContentsView.do?board_id={bid}&contents_id={contents_id}"
BASE_DOMAIN = "https://www.koref.or.kr"

# 수집 결과를 담을 리스트
collected_urls = []

async def crawl_board(board_id, page):
    print("\n" + "="*30)
    print(f"📁 게시판 board_id={board_id} 시작")
    print("="*30)

    # 마지막 페이지 확인
    await page.goto(BASE_LIST_URL.format(bid=board_id, page=1), timeout=0)
    await page.wait_for_load_state("networkidle")
    html = await page.content()

    match = re.search(r'go_Page\((\d+)\)[^>]*>\s*<img[^>]+alt="맨뒤로"', html)
    max_page = int(match.group(1)) if match else 1
    print(f"[INFO] 마지막 페이지 번호: {max_page}")

    # 페이지 순회
    for p in range(1, max_page + 1):
        list_url = BASE_LIST_URL.format(bid=board_id, page=p)
        print(f"\n--- 📄 페이지 {p} → {list_url} ---")
        await page.goto(list_url, timeout=0)
        await page.wait_for_load_state("networkidle")

        anchors = await page.query_selector_all("a[href^='javascript:contentsView']")
        if not anchors:
            print(f"⚠️ {p} 페이지에서 게시물 링크를 찾지 못함")
            continue

        for a in anchors:
            href = await a.get_attribute("href") or ""
            match = re.search(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)", href)
            if not match:
                continue

            contents_id = match.group(1)
            detail_url = BASE_DETAIL_URL.format(bid=board_id, contents_id=contents_id)
            print(f"  📰 게시물 URL: {detail_url}")
            collected_urls.append(detail_url)

            # 상세 페이지 접속
            await page.goto(detail_url, timeout=0)
            await page.wait_for_load_state("networkidle")

            # 첨부파일 링크 추출
            attach_links = await page.query_selector_all("dd.vdd.file a[href*='fileidDownLoad']")
            for link in attach_links:
                file_href = await link.get_attribute("href") or ""
                file_url = BASE_DOMAIN + file_href if file_href.startswith("/") else file_href
                print(f"     └── 📎 첨부파일: {file_url}")
                collected_urls.append(file_url)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for bid in BOARD_IDS:
            await crawl_board(bid, page)

        await browser.close()

    # 결과를 docs 폴더에 저장
    os.makedirs("docs", exist_ok=True)
    with open("docs/result_urls.json", "w", encoding="utf-8") as f:
        json.dump(collected_urls, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 전체 수집 완료! 총 {len(collected_urls)}개 URL이 docs/result_urls.json에 저장됨.")

if __name__ == "__main__":
    asyncio.run(main())
