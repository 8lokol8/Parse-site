import pandas as pd

data = [
    "Привет",
    "Австралийская овчарка",
    "Гигантские питомники",
]

df = pd.DataFrame({"col": data})
df.to_excel("debug.xlsx", index=False)

print("OK")
