# crawler_github.py
import requests
import os

BASE_DOMAIN = "https://www.koref.or.kr"
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]

OUTPUT_FILE = os.path.join("docs", "urls.txt")
os.makedirs("docs", exist_ok=True)

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

total_count = 0

for board_id in BOARD_IDS:
    print(f"\n📁 게시판 board_id={board_id} 수집 시작")
    data = {
        "board_id": board_id,
        "miv_pageNo": 1,
        # 필요시 브라우저에서 확인한 추가 파라미터도 여기에 넣기
    }

    resp = session.post(f"{BASE_DOMAIN}/web/board/boardContentsList.do", headers=headers, data=data)
    try:
        json_data = resp.json()
    except Exception as e:
        print(f"⚠️ board_id={board_id}: JSON 변환 실패 - {e}")
        continue

    board_list = json_data.get("boardList", [])
    if not board_list:
        print(f"⚠️ board_id={board_id}: 게시물이 없음")
        continue

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for board in board_list:
            contents_id = board.get("contents_id")
            file_id = board.get("file_id")

            # 게시물 상세 URL
            detail_url = f"{BASE_DOMAIN}/web/board/boardContentsView.do?board_id={board_id}&contents_id={contents_id}"
            f.write(detail_url + "\n")
            total_count += 1

            # 첨부파일 URL
            if file_id:
                file_url = f"{BASE_DOMAIN}/web/board/fileDownload.do?file_id={file_id}"
                f.write(file_url + "\n")

print(f"\n📝 총 {total_count}개 게시물 URL과 첨부파일 URL 저장 완료 → {OUTPUT_FILE}")
