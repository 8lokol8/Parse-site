import bs4

with open("dump_cat.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = bs4.BeautifulSoup(html, "html.parser")

print("=== Кошка (TopCat) ===")

name_tag = soup.find("h1")
name = name_tag.get_text(strip=True) if name_tag else None
print("Имя:", name)

photo_tag = soup.select_one(".cat-profile-photo img")
photo = photo_tag["src"] if photo_tag else None
print("Фото:", photo)

info_block = soup.find("table", class_="cat-info-table")
data = {}

if info_block:
    for row in info_block.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).rstrip(":")
            val = cols[1].get_text(strip=True)
            data[key] = val

print("\nДанные:")
for k, v in data.items():
    print(f"{k}: {v}")
    
parents_block = soup.select(".parents-info a")
print("\nРодственники/владельцы:")
for p in parents_block:
    print(" -", p.get_text(strip=True), "→", p.get("href"))
