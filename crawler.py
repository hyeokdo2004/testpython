# crawl_playwright.py
import asyncio
import json
import os
import re
import time
from datetime import datetime
from playwright.async_api import async_playwright

# 리스트 대상 board_id
BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]

BASE_DOMAIN = "https://www.koref.or.kr"
LIST_TPL = BASE_DOMAIN + "/web/board/boardContentsListPage.do?board_id={}&miv_pageNo={}"
DETAIL_TPL = BASE_DOMAIN + "/web/board/boardContentsView.do?board_id={}&contents_id={}"
RE_CONTENTS = re.compile(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)")

STATUS_FILE = "status.json"
RESULT_FILE = "result_urls.json"

async def update_status(progress, board_id=None, done=False):
    st = {"progress": int(progress), "current_board": board_id, "done": bool(done)}
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

async def run_crawl():
    results = []
    total_boards = len(BOARD_IDS)
    await update_status(0, None, False)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()

        try:
            for idx, board_id in enumerate(BOARD_IDS, start=1):
                await update_status(int((idx-1)/total_boards*100), board_id, False)
                print(f"== board_id={board_id} ==")

                # 첫 페이지 열기
                await page.goto(LIST_TPL.format(board_id, 1), timeout=60000)
                await page.wait_for_load_state("networkidle")
                # '맨뒤로' 이미지 -> 부모 a의 href에서 go_Page(n) 파싱
                last_page = 1
                try:
                    last_img = await page.query_selector("img[alt='맨뒤로']")
                    if last_img:
                        parent = await last_img.evaluate_handle("n => n.closest('a')")
                        href = await parent.get_attribute("href")
                        if href:
                            m = re.search(r"go_Page\((\d+)\)", href)
                            if m:
                                last_page = int(m.group(1))
                except Exception as e:
                    print("last page detect fail:", e)
                    last_page = 1

                print("last_page:", last_page)

                # 페이지 순회
                for pno in range(1, last_page + 1):
                    list_url = LIST_TPL.format(board_id, pno)
                    print("page:", list_url)
                    # 페이지 이동: go_Page 사용 (사이트 동작 방식)
                    if pno == 1:
                        await page.goto(list_url, timeout=60000)
                    else:
                        try:
                            await page.evaluate(f"go_Page({pno})")
                        except Exception:
                            await page.goto(list_url, timeout=60000)
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(0.2)

                    # 모든 <a>의 href/onlick을 문자열로 미리 수집
                    link_vals = await page.eval_on_selector_all(
                        "a",
                        "els => els.map(a => ({href: a.getAttribute('href')||'', onclick: a.getAttribute('onclick')||'', text: (a.innerText||'').trim()}))"
                    )

                    # 게시물 식별
                    for it in link_vals:
                        joined = (it.get("href","") or "") + " " + (it.get("onclick","") or "")
                        m = RE_CONTENTS.search(joined)
                        if not m:
                            continue
                        contents_id = m.group(1)
                        detail_url = DETAIL_TPL.format(board_id, contents_id)
                        print("POST:", detail_url)
                        results.append(detail_url)

                        # 상세페이지에서 첨부파일 추출
                        detail_page = await context.new_page()
                        try:
                            await detail_page.goto(detail_url, timeout=60000)
                            await detail_page.wait_for_load_state("networkidle")
                            file_links = await detail_page.eval_on_selector_all(
                                "dd.vdd.file a[href*='fileidDownLoad'], a[href*='fileidDownLoad']",
                                "els => els.map(a => a.getAttribute('href'))"
                            )
                            for fh in file_links:
                                if not fh:
                                    continue
                                full = fh if fh.startswith("http") else (BASE_DOMAIN + fh)
                                print("  FILE:", full)
                                results.append(full)  # optional: include file links in results
                        except Exception as e:
                            print(" detail page error:", e)
                        finally:
                            try:
                                await detail_page.close()
                            except:
                                pass

                # board done -> update progress
                await update_status(int(idx/total_boards*100), board_id, False)

        finally:
            await context.close()
            await browser.close()

    # 완료
    await update_status(100, None, True)
    # 결과 파일 저장 (중복 제거)
    uniq = []
    for u in results:
        if u not in uniq:
            uniq.append(u)
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=2)

    print("Crawl done. results:", len(uniq))

if __name__ == "__main__":
    asyncio.run(run_crawl())
