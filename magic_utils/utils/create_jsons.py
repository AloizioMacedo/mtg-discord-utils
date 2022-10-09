import json

with open("oracle-cards.json") as file:
    data = json.load(file)

    n = len(data)
    data1 = [data[i] for i in range(n // 3)]
    data2 = [data[i] for i in range(n // 3, 2 * n // 3)]
    data3 = [data[i] for i in range(2 * n // 3, n)]

with open("oracle-cards-1.json", "w") as file:
    json.dump(data1, file)

with open("oracle-cards-2.json", "w") as file:
    json.dump(data2, file)

with open("oracle-cards-3.json", "w") as file:
    json.dump(data3, file)
