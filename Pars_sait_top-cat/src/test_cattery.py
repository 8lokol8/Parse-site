import requests
from bs4 import BeautifulSoup


CATTERY_URL = "https://ru.top-cat.org/catteries/1621"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_cattery_basic(html: str) -> dict:
    """
    Минимальный разбор HTML питомника — просто для проверки.
    Забираем title и, по возможности, имя питомника.
    """
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.get_text(strip=True) if soup.title else ""

    # Имя питомника обычно в h1 внутри блока с классом "cattery-name" или просто первый <h1>
    h1 = soup.find("h1")
    cattery_name = h1.get_text(strip=True) if h1 else ""

    return {
        "title": title,
        "cattery_name": cattery_name,
    }


def fetch_pets_json(cattery_id: int):
    """
    Делаем тот же запрос, что показал DevTools:
    pets.json?cattery_id=...
    Возвращаем уже распарсенный JSON.
    """
    url = f"https://ru.top-cat.org/pets.json?cattery_id={cattery_id}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError:
        print("⚠ Не удалось декодировать JSON. Ответ сервера:")
        print(resp.text[:1000])
        return None

    return data


def normalize_pets_list(data):
    """
    JSON может быть либо списком, либо словарём с ключами.
    Здесь пытаемся вытащить список питомцев максимально универсально.
    """
    if data is None:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Если сервер вернёт что-то вроде {"pets": [...]}
        for key in ("pets", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]

        for value in data.values():
            if isinstance(value, list):
                return value

    return []


def main():
    print("=== Питомник (TopCat) — тест HTML и JSON ===")
    print("URL питомника:", CATTERY_URL)

    html = fetch_html(CATTERY_URL)
    basic = parse_cattery_basic(html)

    print("\nБазовая информация из HTML:")
    print("Title страницы :", basic["title"])
    print("Имя питомника  :", basic["cattery_name"])

    cattery_id_str = CATTERY_URL.rstrip("/").split("/")[-1]
    try:
        cattery_id = int(cattery_id_str)
    except ValueError:
        print("\n⚠ Не удалось определить ID питомника из URL.")
        return

    print("\nID питомника:", cattery_id)

    print("\nЗапрос к API с питомцами:")
    pets_raw = fetch_pets_json(cattery_id)
    if pets_raw is None:
        print("⚠ JSON не получен.")
        return

    pets = normalize_pets_list(pets_raw)
    print(f"Всего записей в списке питомцев: {len(pets)}")

    if not pets:
        print("⚠ Список пуст. Значит, либо в питомнике нет питомцев, либо другой формат API.")
        print("Сырые данные JSON (первые 1000 символов):")
        print(str(pets_raw)[:1000])
        return

    print("\nПримеры первых 5 питомцев (как есть в JSON):\n")
    for idx, pet in enumerate(pets[:5], start=1):
        # пытаемся вытащить какие-то осмысленные поля
        name = (
            pet.get("name")
            or pet.get("full_name")
            or pet.get("title")
            or pet.get("pet_name")
            or "<?>"
        )
        pet_id = pet.get("id") or pet.get("pet_id")
        url = pet.get("url") or pet.get("link")

        print(f"{idx}. Имя: {name}")
        if pet_id is not None:
            print(f"   ID: {pet_id}")
        if url:
            print(f"   URL/путь: {url}")
        print(f"   Ключи JSON: {list(pet.keys())}")
        print("-" * 40)


if __name__ == "__main__":
    main()
