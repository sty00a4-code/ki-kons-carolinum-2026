import json

with open("vorlesung.json", encoding="utf-8") as f:
    data = json.load(f)

print(json.dumps(data, indent=2, ensure_ascii=False))

with open("vorlesungFull.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(data, indent=2, ensure_ascii=False))



