import os
import requests
from bs4 import BeautifulSoup

BASE_DOMAIN = "https://www.koref.or.kr"
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]
LIST_URL = f"{BASE_DOMAIN}/web/board/boardContentsList.do"

def crawl_board(board_id):
    urls = []
    data = {"board_id": board_id, "miv_pageNo": 1}
    res = requests.post(LIST_URL, data=data, timeout=20)
    res.encoding = "utf-8"

    if "contentsView" not in res.text:
        print(f"⚠️ board_id={board_id}: 게시물 없음 또는 비정상 응답")
        return urls

    soup = BeautifulSoup(res.text, "html.parser")
    for a in soup.select("a[href*='contentsView']"):
        href = a.get("href", "")
        if "contentsView" in href:
            urls.append(BASE_DOMAIN + href.replace("javascript:", ""))

    print(f"✅ board_id={board_id}: {len(urls)}개 수집 완료")
    return urls

def main():
    os.makedirs("docs", exist_ok=True)
    out_path = os.path.join("docs", "collected_urls.txt")

    all_urls = []
    for bid in BOARD_IDS:
        urls = crawl_board(bid)
        all_urls.extend(urls)

    with open(out_path, "w", encoding="utf-8") as f:
        for u in all_urls:
            f.write(u + "\n")

    print(f"\n📝 총 {len(all_urls)}개 URL 저장 완료 → {out_path}")

if __name__ == "__main__":
    main()
