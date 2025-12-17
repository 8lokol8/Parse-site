import requests
import html
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from config import BASE_URL, HEADERS


def multi_unescape(x, max_rounds: int = 5):

    if not isinstance(x, str):
        return x
    prev = x
    for _ in range(max_rounds):
        cur = html.unescape(prev)
        if cur == prev:
            break
        prev = cur
    return prev


def clean_dict(d: dict) -> dict:
    return {k: multi_unescape(v) for k, v in d.items()}


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "lxml")


def extract_id(url: str) -> str:
    return urlparse(url).path.rstrip("/").split("/")[-1]


def parse_kennel(url: str):
    soup = get_soup(url)

    img = soup.select_one(".kennel-info .photo img")
    photo = urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

    name_tag = soup.select_one(".kennel-name h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    city_tag = soup.select_one(".kennel-info .city")
    city = city_tag.get_text(strip=True) if city_tag else None

    details = {}
    for dt in soup.select(".details-container dt"):
        key = dt.get_text(strip=True).rstrip(":")
        dd = dt.find_next("dd")
        if not dd:
            continue

        if "profile-social-icons" in (dd.get("class") or []):
            value = ", ".join(a.get("href") for a in dd.select("a[href]"))
        else:
            value = dd.get_text(" ", strip=True)

        details[key] = value

    dog_links = [
        urljoin(BASE_URL, a["href"])
        for a in soup.select(".dogs-grid-item .dog-name a[href^='/dogs/']")
    ]

    raw_kennel = {
        "kennel_id": extract_id(url),
        "kennel_url": url,
        "kennel_name": name,
        "city_country": city,
        "breeder_person": details.get("Заводчик"),
        "breeds": details.get("Породы"),
        "kennel_prefix": details.get("Заводская приставка"),
        "website": details.get("Веб-сайт"),
        "email": details.get("Эл. почта"),
        "phone": details.get("Телефон"),
        "social_links": details.get("Соц. сети"),
        "photo_url": photo,
        "dogs_count_on_page": len(dog_links),
    }

    kennel_dict = clean_dict(raw_kennel)

    print("=== DEBUG KENNEL ===")
    print("raw city_country:", repr(city))
    print("clean city_country:", repr(kennel_dict["city_country"]))
    print("raw breeds:", repr(details.get("Породы")))
    print("clean breeds:", repr(kennel_dict["breeds"]))
    print("raw breeder:", repr(details.get("Заводчик")))
    print("clean breeder:", repr(kennel_dict["breeder_person"]))
    print("====================\n")

    return kennel_dict, dog_links



def parse_dog(url: str):
    soup = get_soup(url)

    img = soup.select_one(".primary-info-section .avatar img")
    photo = urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

    name_tag = soup.select_one(".primary-info-section .name h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    data = {}
    for row in soup.select(".secondary-info .info-column table tr"):
        def_td = row.select_one(".definition")
        val_td = row.select_one(".value")
        if not def_td or not val_td:
            continue
        key = def_td.get_text(strip=True).rstrip(":")
        value = val_td.get_text(" ", strip=True)
        data[key] = value

    raw_dog = {
        "dog_id": extract_id(url),
        "dog_url": url,
        "dog_name": name,
        "sex": data.get("Пол"),
        "breed": data.get("Порода"),
        "color": data.get("Окрас"),
        "birthday": data.get("День рождения"),
        "father": data.get("Отец"),
        "mother": data.get("Мать"),
        "owner": data.get("Владелец"),
        "co_owner": data.get("Совладелец"),
        "breeder_person": data.get("Заводчик"),
        "kennel_name": data.get("Питомник"),
        "photo_url": photo,
    }

    dog_dict = clean_dict(raw_dog)

    if extract_id(url) == extract_id(url):  # всегда true, просто один раз печатаем
        print("=== DEBUG DOG ===")
        print("raw breed:", repr(data.get("Порода")))
        print("clean breed:", repr(dog_dict["breed"]))
        print("raw owner:", repr(data.get("Владелец")))
        print("clean owner:", repr(dog_dict["owner"]))
        print("=================\n")

    return dog_dict


# ---------- MAIN ----------

def main():
    KENNEL_URL = "https://ru.top-dog.pro/kennels/14"

    print("Парсим питомник...")
    kennel_dict, dog_links = parse_kennel(KENNEL_URL)

    print("Парсим собак...")
    dogs_data = [parse_dog(u) for u in dog_links]

    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(exist_ok=True)
    out_xlsx = out_dir / "test_output_fix.xlsx"

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
        pd.DataFrame([kennel_dict]).to_excel(w, sheet_name="kennels", index=False)
        pd.DataFrame(dogs_data).to_excel(w, sheet_name="dogs", index=False)

    print("\nГотово:", out_xlsx)


if __name__ == "__main__":
    main()
