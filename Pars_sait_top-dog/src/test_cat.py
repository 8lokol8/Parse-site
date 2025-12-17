import requests

url = "https://ru.top-cat.org/cats/528326"  # <-- сюда URL кошки
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/129.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=15)
resp.raise_for_status()

with open("dump_cat.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

print("saved dump_cat.html")
