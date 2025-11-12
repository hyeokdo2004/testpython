import requests
from bs4 import BeautifulSoup
import os
import time

BASE_URL = "https://www.koref.or.kr"
LIST_URL = f"{BASE_URL}/web/board/boardContentsList.do"

# 👇 실제 사용하는 게시판 ID 전체
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]

# docs 폴더에 결과 저장 (GitHub Pages에서 바로 접근 가능)
os.makedirs("docs", exist_ok=True)
output_path = os.path.join("docs", "collected_urls.txt")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": BASE_URL,
    "Referer": BASE_URL + "/web/board/boardContentsListPage.do",
}

def crawl_board(board_id, max_pages=5):
    all_links = []
    print(f"\n==============================")
    print(f"📁 게시판 board_id={board_id} 시작")
    print(f"==============================")

    for page_no in range(1, max_pages + 1):
        payload = {
            "board_id": board_id,
            "miv_pageNo": page_no
        }

        res = requests.post(LIST_URL, headers=HEADERS, data=payload)
        res.encoding = "utf-8"

        if res.status_code != 200:
            print(f"❌ 요청 실패: {res.status_code}")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("ul.boardList li a")

        if not rows:
            print(f"⚠️ 페이지 {page_no}: 게시물 없음 (더 이상 없음)")
            break

        print(f"📄 페이지 {page_no} → 게시물 {len(rows)}개")

        for a in rows:
            href = a.get("href")
            title = a.get_text(strip=True)
            if href and "javascript" not in href:
                full_url = href if href.startswith("http") else BASE_URL + href
                all_links.append((title, full_url))

        time.sleep(0.5)

    return all_links

def main():
    all_results = []
    for bid in BOARD_IDS:
        board_links = crawl_board(bid, max_pages=20)
        all_results.extend(board_links)

    if not all_results:
        print("⚠️ 수집된 게시물 없음.")
        return

    with open(output_path, "w", encoding="utf-8") as f:
        for title, url in all_results:
            f.write(f"<a href=\"{url}\">{title}</a>\n")

    print(f"\n✅ 완료: 총 {len(all_results)}개 URL 저장됨 → {output_path}")

if __name__ == "__main__":
    main()
