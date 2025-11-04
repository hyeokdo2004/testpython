import requests
from bs4 import BeautifulSoup
import json
import time

base_url = "https://www.koref.or.kr/web/board/boardContentsListPage.do?board_id={}&page={}"
board_ids = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]
results = []
status = {"progress": 0, "current_board": None, "done": False}

def update_status(progress, board_id=None, done=False):
    status["progress"] = progress
    status["current_board"] = board_id
    status["done"] = done
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

def get_last_page(soup):
    last_link = soup.select_one("a[href*='javascript:go_Page']")
    if not last_link:
        return 1
    last_page = 1
    for a in soup.select("a[href*='javascript:go_Page']"):
        text = a.get("href", "")
        if "go_Page" in text:
            try:
                num = int(text.split("(")[1].split(")")[0])
                last_page = max(last_page, num)
            except:
                continue
    return last_page

total_boards = len(board_ids)

for i, board_id in enumerate(board_ids, start=1):
    print("\n" + "="*30)
    print(f"📁 게시판 board_id={board_id} 시작")
    print("="*30)

    update_status(int((i-1)/total_boards*100), board_id)

    url = base_url.format(board_id, 1)
    res = requests.get(url)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    last_page = get_last_page(soup)
    print(f"📄 총 {last_page} 페이지 탐색")

    for page in range(1, last_page + 1):
        list_url = base_url.format(board_id, page)
        print(f"  ▶ 페이지 {page}/{last_page}: {list_url}")
        res = requests.get(list_url)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a[href*='javascript:go_Contents']"):
            href = a.get("href", "")
            if "go_Contents" in href:
                parts = href.split("(")[1].split(")")[0].replace("'", "").split(",")
                if len(parts) >= 2:
                    ntt_id = parts[1].strip()
                    post_url = f"https://www.koref.or.kr/web/board/boardContentsView.do?board_id={board_id}&contents_no={ntt_id}"
                    print(f"    🔗 {post_url}")
                    results.append(post_url)

    update_status(int(i/total_boards*100), board_id)

update_status(100, done=True)

with open("result_urls.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n✅ 전체 수집 완료! result_urls.json 파일로 저장됨.")
