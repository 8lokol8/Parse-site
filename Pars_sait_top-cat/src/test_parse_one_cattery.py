# test_parse_one_cattery.py
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ru.top-cat.org"


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def main():
    url = f"{BASE_URL}/catteries/1621"

    print("=== Тест парсинга одного питомника — CONTACTS ===")
    print("URL:", url)

    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else None
    print("\nИмя питомника:", name)

    contacts_header_text = None
    for text_node in soup.find_all(string=True):
        t = text_node.strip()
        if t == "Контакты":
            contacts_header_text = text_node
            break

    if not contacts_header_text:
        print("\n[ОШИБКА] Текст 'Контакты' на странице не найден")
        return

    header_tag = contacts_header_text.parent
    block = header_tag
    for _ in range(5):
        if block.name in ("div", "section", "aside"):
            if len(block.get_text(strip=True)) > len("Контакты") + 10:
                break
        block = block.parent

    print("\n=== СЫРОЙ ТЕКСТ БЛОКА 'Контакты' ===")
    print(block.get_text("\n", strip=True))


if __name__ == "__main__":
    main()
