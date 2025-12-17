import html
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import BASE_URL, HEADERS

TEST_KENNEL_URL = "https://ru.top-dog.pro/kennels/14"  # TripleMoon


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "lxml")


def clean_dict(d: dict) -> dict:
    """
    Прогоняем все строковые значения через html.unescape,
    чтобы на раннем этапе проверить, что нигде не лезут &#NNNN;.
    """
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, str):
            cleaned[k] = html.unescape(v)
        else:
            cleaned[k] = v
    return cleaned


def parse_kennel(url: str) -> None:
    soup = get_soup(url)

    # Фото питомника
    img = soup.select_one(".kennel-info .photo img")
    photo = urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

    # Название
    name_tag = soup.select_one(".kennel-name h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    # Город / страна
    city_tag = soup.select_one(".kennel-info .city")
    city = city_tag.get_text(strip=True) if city_tag else None

    # Детали (dt/dd)
    details = {}
    for dt in soup.select(".details-container dt"):
        key = dt.get_text(strip=True).rstrip(":")
        dd = dt.find_next("dd")
        if not dd:
            continue

        # Соцсети
        if "profile-social-icons" in (dd.get("class") or []):
            links = [a.get("href") for a in dd.select("a[href]")]
            value = ", ".join(links)
        else:
            value = dd.get_text(" ", strip=True)

        details[key] = value

 
    details = clean_dict(details)

    print("=== Питомник ===")
    print("Фото:", photo)
    print("Название:", html.unescape(name) if isinstance(name, str) else name)
    print("Город/Страна:", html.unescape(city) if isinstance(city, str) else city)
    print("Заводчик:", details.get("Заводчик"))
    print("Породы:", details.get("Породы"))
    print("Заводская приставка:", details.get("Заводская приставка"))
    print("Веб-сайт:", details.get("Веб-сайт"))
    print("Эл. почта:", details.get("Эл. почта"))
    print("Телефон:", details.get("Телефон"))
    print("Соц. сети:", details.get("Соц. сети"))

    
    dogs = [
        urljoin(BASE_URL, a["href"])
        for a in soup.select(".dogs-grid-item .dog-name a[href^='/dogs/']")
    ]

    print("Ссылок на собак:", len(dogs))
    for d in dogs:
        print(" ", d)


if __name__ == "__main__":
    parse_kennel(TEST_KENNEL_URL)
