import requests

url = input("Вставь URL страницы: ").strip()

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

r = requests.get(url, headers=headers)
r.encoding = "utf-8"

with open("dump.html", "w", encoding="utf-8") as f:
    f.write(r.text)

print("Готово! Файл сохранён: dump.html")
