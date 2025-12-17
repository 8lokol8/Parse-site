import requests

url = "https://ru.top-cat.org/catteries/1621"  # <-- сюда ставь URL КОНКРЕТНОГО питомника
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/129.0 Safari/537.36"
}

resp = requests.get(url, headers=headers, timeout=15)
resp.raise_for_status()

with open("dump_cattery.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

print("saved dump_cattery.html")
