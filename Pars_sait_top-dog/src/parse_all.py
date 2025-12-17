import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import html

import requests
from bs4 import BeautifulSoup
import pandas as pd

from config import BASE_URL, HEADERS




session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url: str) -> BeautifulSoup:
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return BeautifulSoup(resp.text, "lxml")


def extract_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    last = path.split("/")[-1]
    return last


def clean_dict(d: dict) -> dict:
    """
    Прогоняем все строковые значения через html.unescape,
    чтобы убрать &#NNNN; и другие HTML-сущности, если вдруг они появятся.
    """
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, str):
            cleaned[k] = html.unescape(v)
        else:
            cleaned[k] = v
    return cleaned



def parse_dog(dog_url: str,
              kennel_id: str | None = None,
              kennel_name_from_kennel: str | None = None) -> dict:
    """
    Парсим страницу конкретной собаки.
    Возвращаем dict с нужными полями.
    """
    soup = get_soup(dog_url)

    # Фото
    img = soup.select_one(".primary-info-section .avatar img")
    photo_url = urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

    # Имя
    name_tag = soup.select_one(".primary-info-section .name h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    # Таблицы с данными
    data = {}
    for row in soup.select(".secondary-info .info-column table tr"):
        def_td = row.select_one("td.definition")
        val_td = row.select_one("td.value")
        if not def_td or not val_td:
            continue
        key = def_td.get_text(strip=True).rstrip(":")
        value = val_td.get_text(" ", strip=True)
        data[key] = value

    # Питомник
    kennel_name = data.get("Питомник") or kennel_name_from_kennel

    dog_id = extract_id_from_url(dog_url)

    return {
        "dog_id": dog_id,
        "dog_url": dog_url,
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
        "kennel_name": kennel_name,
        "kennel_id": kennel_id,
        "photo_url": photo_url,
    }


def parse_kennel(kennel_url: str) -> tuple[dict, list[str]]:
    """
    Парсим страницу питомника.
    Возвращаем:
      - dict с данными питомника
      - список URL собак этого питомника
    """
    soup = get_soup(kennel_url)

    # Фото
    img = soup.select_one(".kennel-info .photo img")
    photo_url = urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

    # Название
    name_tag = soup.select_one(".kennel-name h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    # Город/страна
    city_tag = soup.select_one(".kennel-info .city")
    city = city_tag.get_text(strip=True) if city_tag else None

    # Детали (dt/dd)
    details: dict[str, str] = {}
    for dt in soup.select(".details-container dt"):
        key = dt.get_text(strip=True).rstrip(":")
        dd = dt.find_next("dd")
        if not dd:
            continue

        # Соцсети — href всех ссылок
        if "profile-social-icons" in (dd.get("class") or []):
            links = [a.get("href") for a in dd.select("a[href]")]
            value = ", ".join(links)
        else:
            value = dd.get_text(" ", strip=True)

        details[key] = value

    # Ссылки на собак
    dog_links: list[str] = [
        urljoin(BASE_URL, a["href"])
        for a in soup.select(".dogs-grid-item .dog-name a[href^='/dogs/']")
    ]

    kennel_id = extract_id_from_url(kennel_url)

    kennel_data = {
        "kennel_id": kennel_id,
        "kennel_url": kennel_url,
        "kennel_name": name,
        "city_country": city,
        "breeder_person": details.get("Заводчик"),
        "breeds": details.get("Породы"),
        "kennel_prefix": details.get("Заводская приставка"),
        "website": details.get("Веб-сайт"),
        "email": details.get("Эл. почта"),
        "phone": details.get("Телефон"),
        "social_links": details.get("Соц. сети"),
        "photo_url": photo_url,
        "dogs_count_on_page": len(dog_links),
    }

    return kennel_data, dog_links


def collect_all_kennel_links(max_pages: int | None = None) -> list[str]:
    """
    Обходит страницы /kennels?page=N, пока есть новые питомники.
    Если max_pages задан, ограничивает число страниц.
    """
    all_links: list[str] = []
    seen_ids: set[str] = set()
    page = 1

    while True:
        if max_pages is not None and page > max_pages:
            break

        url = f"{BASE_URL}/kennels?page={page}"
        print(f"[KENNELS] Страница {page}: {url}")
        try:
            soup = get_soup(url)
        except requests.HTTPError as e:
            print(f"  Ошибка HTTP ({e}), прекращаем обход.")
            break

        page_links: list[str] = []
        for a in soup.select("a[href^='/kennels/']"):
            href = a.get("href")
            if not href:
                continue
            full_url = urljoin(BASE_URL, href)
            kid = extract_id_from_url(full_url)
            if not kid.isdigit():
                continue
            if kid in seen_ids:
                continue
            seen_ids.add(kid)
            page_links.append(full_url)

        if not page_links:
            print("  На странице не найдено новых питомников, выходим.")
            break

        print(f"  Найдено питомников на странице: {len(page_links)}")
        all_links.extend(page_links)

        page += 1
        time.sleep(0.5)

    print(f"\nВсего найдено питомников: {len(all_links)}\n")
    return all_links



def main():
    kennel_links = collect_all_kennel_links()

    kennels_rows: list[dict] = []
    dogs_rows: list[dict] = []

    for idx, kennel_url in enumerate(kennel_links, start=1):
        print(f"[KENNEL {idx}/{len(kennel_links)}] {kennel_url}")

        try:
            kennel_data, dog_links = parse_kennel(kennel_url)
        except Exception as e:
            print(f"  !! Ошибка при парсинге питомника: {e}")
            continue

        kennels_rows.append(clean_dict(kennel_data))

        for dog_url in dog_links:
            print(f"    [DOG] {dog_url}")
            try:
                dog_data = parse_dog(
                    dog_url,
                    kennel_id=kennel_data["kennel_id"],
                    kennel_name_from_kennel=kennel_data["kennel_name"],
                )
                dogs_rows.append(clean_dict(dog_data))
                time.sleep(0.5)
            except Exception as e:
                print(f"      !! Ошибка при парсинге собаки: {e}")

        time.sleep(0.5)

    output_dir = Path(__file__).resolve().parents[1] / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "topdog_kennels_and_dogs.xlsx"

    df_kennels = pd.DataFrame(kennels_rows)
    df_dogs = pd.DataFrame(dogs_rows)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_kennels.to_excel(writer, sheet_name="kennels", index=False)
        df_dogs.to_excel(writer, sheet_name="dogs", index=False)

    print(f"\nГотово! Файл сохранён: {output_path}")


if __name__ == "__main__":
    main()
