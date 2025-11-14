# crawler.py
import requests
import re
import os

BASE_URL = "https://www.koref.or.kr"
BOARD_ID = 27
LIST_PAGE_URL = f"{BASE_URL}/web/board/boardContentsListPage.do?board_id={BOARD_ID}"
AJAX_URL = f"{BASE_URL}/web/board/boardContentsList.do"

OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "collected_contents_ids.txt")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 세션 및 헤더
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": LIST_PAGE_URL
}

# AJAX 요청 파라미터 (첫 페이지)
data = {
    "board_id": BOARD_ID,
    "miv_pageNo": 1
}

try:
    resp = session.post(AJAX_URL, headers=headers, data=data, timeout=15)
    resp.raise_for_status()
except requests.RequestException as e:
    print(f"⚠️ AJAX 요청 실패: {e}")
    exit(1)

try:
    json_data = resp.json()
except Exception as e:
    print(f"⚠️ JSON 파싱 실패: {e}")
    exit(1)

board_list = json_data.get("boardList", [])
contents_ids = []

for item in board_list:
    onclick_val = item.get("onclick", "")
    # contentsView('572b4a95fc0e43c39900d9b7a4d39091')
    m = re.search(r"contentsView\(['\"]([0-9a-fA-F]+)['\"]\)", onclick_val)
    if m:
        contents_ids.append(m.group(1))

# 파일 저장
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for cid in contents_ids:
        f.write(cid + "\n")

print(f"🔗 페이지 접속: {LIST_PAGE_URL}")
print(f"✅ 총 {len(contents_ids)}개 contents_id 추출")
print(f"✅ 결과 저장 → {OUTPUT_FILE}")
