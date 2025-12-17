import re
import time
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

BASE_URL = "https://ru.top-cat.org"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_cattery_links(max_pages=None, pause=0.5):
    """
    Собирает все ссылки на питомники со страниц /catteries?page=N.

    max_pages: если None — идём до первой пустой страницы.
               если число — ограничиваемся этим количеством страниц.
    """
    links = []
    page = 1

    while True:
        if max_pages is not None and page > max_pages:
            break

        url = f"{BASE_URL}/catteries?page={page}"
        print(f"\n=== Страница {page} ===")
        print("Запрос:", url)

        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            print(f"Страница {page}: статус {resp.status_code}, прекращаю обход.")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        page_links = []
        for a in soup.find_all("a", href=re.compile(r"^/catteries/\d+")):
            href = a.get("href")
            if not href:
                continue
            full_url = BASE_URL + href if href.startswith("/") else href
            if full_url not in links:
                links.append(full_url)
                page_links.append(full_url)

        print(f"Найдено новых ссылок на этой странице: {len(page_links)}")
        print(f"Всего уникальных ссылок: {len(links)}")

        if not page_links:
            break

        page += 1
        time.sleep(pause)

    return links


def parse_contacts_block(block):

    text = block.get_text("\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    if lines and "контакты" in lines[0].lower():
        lines = lines[1:]

    breeder_person = None
    breeder_rating = None
    city_country = None
    email = None
    phone = None
    site = None
    social_links = []

    if not lines:
        return breeder_person, breeder_rating, city_country, email, phone, site, social_links

    breeder_person = lines[0]

    email_re = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    phone_re = re.compile(r"\+?\d[\d\-\s\(\)]{6,}")
    url_re = re.compile(r"https?://\S+")

    for i, line in enumerate(lines):
        low = line.lower()


        if "рейтинг" in low and "заводчика" in low and i + 1 < len(lines):
            breeder_rating = lines[i + 1]


        if email is None:
            m = email_re.search(line)
            if m:
                email = m.group(0)


        if phone is None:

            m = phone_re.search(line)
            if m:
                phone = line


        for m in url_re.findall(line):
            url = m.strip().rstrip(").,;")
            if any(s in url for s in ("vk.com", "ok.ru", "instagram.com", "facebook.com", "t.me", "telegram.me")):
                if url not in social_links:
                    social_links.append(url)
            else:
                if site is None:
                    site = url

    for line in lines:
        if line == breeder_person or (breeder_rating and line == breeder_rating):
            continue
        if "@" in line:
            continue
        if line.startswith("http"):
            continue
        if any(word in line for word in ["Россия", "Украина", "Беларусь", "Казахстан", "Latvia", "Lithuania",
                                         "Estonia", "Germany", "France", "USA", "Россия."]):
            city_country = line
            break

    return breeder_person, breeder_rating, city_country, email, phone, site, social_links


def parse_cattery(url):
    """
    Парсит ОДИН питомник по его URL.
    Возвращает dict с полями:
      cattery_id, cattery_url, cattery_name,
      breeder_person, breeder_rating, city_country,
      email, phone, site, social_links
    """
    print(f"\n=== Парсим питомник ===")
    print("URL:", url)

    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    m = re.search(r"/catteries/(\d+)", url)
    cattery_id = m.group(1) if m else None

    h1 = soup.find("h1")
    cattery_name = h1.get_text(strip=True) if h1 else None

    header = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4")
        and "Контакты" in tag.get_text()
    )

    breeder_person = None
    breeder_rating = None
    city_country = None
    email = None
    phone = None
    site = None
    social_links = []

    if header:

        block = header.find_parent("div")
        if block:
            (breeder_person,
             breeder_rating,
             city_country,
             email,
             phone,
             site,
             social_links) = parse_contacts_block(block)
    else:
        print("ВНИМАНИЕ: блок 'Контакты' не найден, данные будут пустыми.")

    return {
        "cattery_id": cattery_id,
        "cattery_url": url,
        "cattery_name": cattery_name,
        "breeder_person": breeder_person,
        "breeder_rating": breeder_rating,
        "city_country": city_country,
        "email": email,
        "phone": phone,
        "site": site,
        "social_links": ", ".join(social_links) if social_links else None,
    }


def save_to_excel(rows, filename="topcat_catteries.xlsx"):
    """
    Сохраняет список словарей rows в Excel.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "catteries"

    headers = [
        "cattery_id",
        "cattery_url",
        "cattery_name",
        "breeder_person",
        "breeder_rating",
        "city_country",
        "email",
        "phone",
        "site",
        "social_links",
    ]
    ws.append(headers)

    for row in rows:
        ws.append([row.get(col) for col in headers])

    wb.save(filename)
    print(f"\nФайл сохранён: {filename}")


# ====================== MAIN ======================

def main():
    print("=== Сбор ссылок на все питомники TopCat ===")
    # max_pages=None — идти до первой пустой страницы
    cattery_links = get_cattery_links(max_pages=None, pause=0.5)

    print(f"\nВсего найдено питомников: {len(cattery_links)}")

    all_rows = []
    total = len(cattery_links)

    for idx, url in enumerate(cattery_links, start=1):
        print(f"\n[{idx}/{total}] Обработка: {url}")
        try:
            data = parse_cattery(url)
        except Exception as e:
            print(f"ОШИБКА при парсинге {url}: {e}")
            m = re.search(r"/catteries/(\d+)", url)
            c_id = m.group(1) if m else None
            data = {
                "cattery_id": c_id,
                "cattery_url": url,
                "cattery_name": None,
                "breeder_person": None,
                "breeder_rating": None,
                "city_country": None,
                "email": None,
                "phone": None,
                "site": None,
                "social_links": None,
            }

        all_rows.append(data)
        if idx % 20 == 0:
            save_to_excel(all_rows, filename="topcat_catteries_progress.xlsx")

        time.sleep(0.5)

    save_to_excel(all_rows, filename="topcat_catteries.xlsx")


if __name__ == "__main__":
    main()
