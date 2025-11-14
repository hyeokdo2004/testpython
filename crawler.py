# crawler.py
import asyncio
import requests
from playwright.async_api import async_playwright
import os

# 게시판 ID 리스트
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]

BASE_DOMAIN = "https://www.koref.or.kr"
LIST_PAGE_URL = BASE_DOMAIN + "/web/board/boardContentsListPage.do?board_id={}"
LIST_API_URL  = BASE_DOMAIN + "/web/board/boardContentsList.do"
DETAIL_URL    = BASE_DOMAIN + "/web/board/boardContentsView.do?board_id={}&contents_id={}"
FILE_URL      = BASE_DOMAIN + "/web/board/fileDownload.do?file_id={}"

OUTPUT_FILE = os.path.join("docs", "collected_urls.txt")
os.makedirs("docs", exist_ok=True)

async def get_session_cookies():
    """Playwright로 첫 페이지 접속 후 세션 쿠키 획득"""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(LIST_PAGE_URL.format(BOARD_IDS[0]), timeout=60000)
        await page.wait_for_load_state("networkidle")

        cookies = await context.cookies()
        session_cookies = {c['name']: c['value'] for c in cookies}
        await context.close()
        await browser.close()
        print("✅ Playwright로 세션 쿠키 확보:", session_cookies)
        return session_cookies

def fetch_board_list(session: requests.Session, board_id: int, page_no: int = 1):
    """requests로 게시물 목록 요청"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": LIST_PAGE_URL.format(board_id)
    }

    data = {
        "board_id": board_id,
        "miv_pageNo": page_no,
        # 필요시 브라우저에서 확인한 추가 파라미터
    }

    resp = session.post(LIST_API_URL, headers=headers, data=data)
    resp.raise_for_status()
    return resp.json().get("boardList", [])

async def main():
    # 1️⃣ Playwright로 세션 쿠키 확보
    cookies = await get_session_cookies()

    # 2️⃣ requests 세션에 쿠키 적용
    session = requests.Session()
    for k, v in cookies.items():
        session.cookies.set(k, v, domain="www.koref.or.kr")

    # 3️⃣ 게시판 순회
    total_count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for board_id in BOARD_IDS:
            print(f"\n📁 게시판 board_id={board_id} 수집 시작")
            try:
                board_list = fetch_board_list(session, board_id, page_no=1)
            except Exception as e:
                print(f" ⚠️ board_id={board_id}, page=1 요청/파싱 오류:", e)
                continue

            if not board_list:
                print(f" ⚠️ board_id={board_id}, 게시물이 없음")
                continue

            for board in board_list:
                b_id = board.get("board_id")
                contents_id = board.get("contents_id")
                file_id = board.get("file_id")

                detail_url = DETAIL_URL.format(b_id, contents_id)
                f.write(detail_url + "\n")
                total_count += 1
                print(" 📰 게시물 URL:", detail_url)

                if file_id:
                    file_url = FILE_URL.format(file_id)
                    f.write(file_url + "\n")
                    print(" └── 📎 첨부파일 URL:", file_url)

    print(f"\n📝 총 {total_count}개 게시물 URL과 첨부파일 URL 저장 완료 → {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
