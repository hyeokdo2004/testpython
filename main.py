import requests
from bs4 import BeautifulSoup
from datetime import datetime

def collect_urls():
    # URL을 수집하는 부분
    urls = ["https://example.com", "https://another.com"]
    return urls

def update_html(urls):
    html_file = "index.html"
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        html = "<html><body><ul></ul></body></html>"

    soup = BeautifulSoup(html, "html.parser")
    ul = soup.find("ul")

    existing_urls = [a["href"] for a in ul.find_all("a")]

    for url in urls:
        if url not in existing_urls:
            li = soup.new_tag("li")
            a = soup.new_tag("a", href=url)
            a.string = url
            li.append(a)
            ul.append(li)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

if __name__ == "__main__":
    urls = collect_urls()
    update_html(urls)
    print("✅ HTML 업데이트 완료:", datetime.now())
