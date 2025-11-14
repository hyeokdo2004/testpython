# crawler.py
import requests
import os

# 게시판 ID 리스트
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]

BASE_DOMAIN = "https://www.koref.or.kr"
LIST_URL = BASE_DOMAIN + "/web/board/boardContentsList.do"
DETAIL_URL_TPL = BASE_DOMAIN + "/web/board/boardContentsView.do?board_id={}&contents_id={}"
FILE_URL_TPL = BASE_DOMAIN + "/web/board/fileDownload.do?file_id={}"

OUTPUT_FILE = os.path.join("docs", "collected_urls.txt")
os.makedirs("docs", exist_ok=True)

# 세션 유지
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
})

total_count = 0

for board_id in BOARD_IDS:
    print(f"\n📁 게시판 board_id={board_id} 수집 시작")

    page_no = 1
    while True:
        data = {
            "board_id": board_id,
            "miv_pageNo": page_no,
            # 필요하면 hidden form 값 등 추가 가능
        }

        try:
            resp = session.post(LIST_URL, data=data)
            resp.raise_for_status()
            json_data = resp.json()
        except Exception as e:
            print(f" ⚠️ board_id={board_id}, page={page_no} 요청/파싱 오류: {e}")
            break

        board_list = json_data.get("boardList", [])
        if not board_list:
            if page_no == 1:
                print(f" ⚠️ board_id={board_id}: 게시물이 없음")
            break

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for board in board_list:
                contents_id = board.get("contents_id")
                file_id = board.get("file_id")

                # 게시물 상세 URL
                detail_url = DETAIL_URL_TPL.format(board_id, contents_id)
                f.write(detail_url + "\n")
                total_count += 1
                print(f" 📰 게시물: {detail_url}")

                # 첨부파일 URL
                if file_id:
                    file_url = FILE_URL_TPL.format(file_id)
                    f.write(file_url + "\n")
                    print(f" └── 첨부파일: {file_url}")

        page_no += 1

print(f"\n📝 총 {total_count}개 게시물 URL 및 첨부파일 URL 저장 완료 → {OUTPUT_FILE}")
