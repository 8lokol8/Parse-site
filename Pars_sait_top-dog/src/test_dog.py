import html
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import BASE_URL, HEADERS

TEST_DOG_URL = "https://ru.top-dog.pro/dogs/1396"  # Chenporewa Nio Njord Pitomec Gigant


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "lxml")


def clean_dict(d: dict) -> dict:
    """
    Прогоняем все строковые значения через html.unescape
    (аналогично тому, как делается в основном парсере перед Excel).
    """
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, str):
            cleaned[k] = html.unescape(v)
        else:
            cleaned[k] = v
    return cleaned


def parse_dog(url: str) -> None:
    soup = get_soup(url)

    # Фото
    img = soup.select_one(".primary-info-section .avatar img")
    photo = urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

    # Кличка
    name_tag = soup.select_one(".primary-info-section .name h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    data = {}
    for row in soup.select(".secondary-info .info-column table tr"):
        def_td = row.select_one("td.definition")
        val_td = row.select_one("td.value")
        if not def_td or not val_td:
            continue
        key = def_td.get_text(strip=True).rstrip(":")
        value = val_td.get_text(" ", strip=True)
        data[key] = value

    data = clean_dict(data)

    print("=== Собака ===")
    print("URL:", url)
    print("Фото:", photo)
    print("Кличка:", html.unescape(name) if isinstance(name, str) else name)
    print("Пол:", data.get("Пол"))
    print("Порода:", data.get("Порода"))
    print("Окрас:", data.get("Окрас"))
    print("Дата рождения:", data.get("День рождения"))
    print("Отец:", data.get("Отец"))
    print("Мать:", data.get("Мать"))
    print("Владелец:", data.get("Владелец"))
    print("Совладелец:", data.get("Совладелец"))
    print("Заводчик:", data.get("Заводчик"))
    print("Питомник:", data.get("Питомник"))


if __name__ == "__main__":
    parse_dog(TEST_DOG_URL)
