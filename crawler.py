# git.py (동적 렌더링 대기 버전)
import asyncio
from playwright.async_api import async_playwright
import re

BOARD_IDS = [27, 49, 28, 29, 30, 50, 51, 52, 39, 37, 32]
BASE_DOMAIN = "https://www.koref.or.kr"
LIST_TPL = BASE_DOMAIN + "/web/board/boardContentsListPage.do?board_id={}&miv_pageNo={}"
DETAIL_TPL = BASE_DOMAIN + "/web/board/boardContentsView.do?board_id={}&contents_id={}"

RE_CONTENTS = re.compile(r"contentsView\(['\"]?([0-9a-fA-F]+)['\"]?\)")

async def wait_for_dynamic_render(page, selector="ul.boardList a", timeout=10000):
    """게시글이 Ajax로 렌더될 때까지 반복 확인"""
    total_wait = 0
    while total_wait < timeout:
        count = await page.eval_on_selector_all(selector, "els => els.length")
        if count > 0:
            return True
        await asyncio.sleep(0.5)
        total_wait += 500
    return False

async def crawl_board(page, board_id: int):
    print("\n" + "=" * 30)
    print(f"📁 게시판 board_id={board_id} 시작")
    print("=" * 30)

    # 첫 페이지 접속
    first_url = LIST_TPL.format(board_id, 1)
    await page.goto(first_url, timeout=60000)
    await page.wait_for_load_state("networkidle")
    await wait_for_dynamic_render(page)
    await asyncio.sleep(0.5)

    # 마지막 페이지 번호 추출
    last_page = 1
    try:
        last_img = await page.query_selector("img[alt='맨뒤로']")
        if last_img:
            parent_a = await last_img.evaluate_handle("node => node.closest('a')")
            href = await parent_a.get_attribute("href")
            if href and "go_Page" in href:
                m = re.search(r"go_Page\((\d+)\)", href)
                if m:
                    last_page = int(m.group(1))
    except Exception:
        pass

    print(f"[INFO] 마지막 페이지 번호: {last_page}")

    for p in range(1, last_page + 1):
        page_url = LIST_TPL.format(board_id, p)
        print(f"\n--- 📄 페이지 {p} → {page_url}")

        if p > 1:
            try:
                await page.evaluate(f"go_Page({p})")
            except:
                await page.goto(page_url, timeout=60000)

        await page.wait_for_load_state("networkidle")
        await wait_for_dynamic_render(page)
        await asyncio.sleep(0.5)

        link_values = await page.eval_on_selector_all(
            "a",
            """els => els.map(a => ({
                href: a.getAttribute('href') || '',
                onclick: a.getAttribute('onclick') || '',
                text: (a.innerText || '').trim()
            }))"""
        )

        found_any = False
        for item in link_values:
            href = item.get("href", "")
            onclick = item.get("onclick", "")
            joined = href + " " + onclick
            m = RE_CONTENTS.search(joined)
            if not m:
                continue

            found_any = True
            contents_id = m.group(1)
            detail_url = DETAIL_TPL.format(board_id, contents_id)
            print(f" 📰 게시물 URL: {detail_url}")

            # 상세페이지 접근
            try:
                detail_page = await page.context.new_page()
                await detail_page.goto(detail_url, timeout=60000)
                await detail_page.wait_for_load_state("networkidle")
                await wait_for_dynamic_render(detail_page, "a[href*='fileidDownLoad']")
                file_links = await detail_page.eval_on_selector_all(
                    "a[href*='fileidDownLoad'], dd.vdd.file a",
                    "els => els.map(a => a.getAttribute('href'))"
                )

                for fh in file_links:
                    if fh:
                        full = fh if fh.startswith("http") else (BASE_DOMAIN + fh)
                        print(f" └── 📎 첨부파일: {full}")

                await detail_page.close()
            except Exception as e:
                print(f" ⚠️ 상세페이지 접근/추출 오류: {e}")
                try:
                    await detail_page.close()
                except:
                    pass

        if not found_any:
            print(" ⚠️ 이 페이지에서 게시물을 찾지 못함 (렌더링 실패 가능성)")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print("\n=== 시작: 모든 board_id 게시판 수집 ===")

        for bid in BOARD_IDS:
            await crawl_board(page, bid)

        print("\n=== 완료 ===")
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
