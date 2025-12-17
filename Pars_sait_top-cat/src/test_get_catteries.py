import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ru.top-cat.org"

def get_cattery_links(page=1):
    url = f"{BASE_URL}/catteries?page={page}"
    print("Запрос:", url)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.select("a[href^='/catteries/']"):
        href = a.get("href")
        if href.count("/") == 2:  # /catteries/1234
            full = BASE_URL + href
            if full not in links:
                links.append(full)

    return links


def main():
    print("=== Тест: получаем первую страницу списка питомников ===")
    links = get_cattery_links(1)

    print(f"Найдено ссылок: {len(links)}")
    print("\nПервые 5:")
    for l in links[:5]:
        print("  ", l)


if __name__ == "__main__":
    main()
