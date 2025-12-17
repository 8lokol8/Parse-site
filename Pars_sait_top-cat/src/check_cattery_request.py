import requests

url = "https://ru.top-cat.org/catteries/1621"  # Krasnozar
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
}

print("== Делаем реальный запрос ==")
r = requests.get(url, headers=headers)
print("Статус:", r.status_code)

html = r.text
print("\n=== Первые 2000 символов HTML ===")
print(html[:2000])
print("\n================================\n")

keywords = ["Lilit", "Hillarion", "Siaorifly", "Melman", "TopCat"]

print("== Поиск имен котов в сыром HTML ==")
found_any = False
for kw in keywords:
    if kw.lower() in html.lower():
        print(f"Найдено: {kw}")
        found_any = True

if not found_any:
    print("⚠ Ни одно имя кота в HTML не найдено! Вероятно, данные грузятся через JavaScript.")
