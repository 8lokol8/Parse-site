import pandas as pd

df = pd.DataFrame({
    "column": ["Привет", "Австралийская овчарка", "Гигантские питомники"]
})

df.to_excel("test_utf.xlsx", index=False)
print("Файл создан: test_utf.xlsx")
