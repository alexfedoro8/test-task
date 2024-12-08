from fastapi import FastAPI, HTTPException

app = FastAPI()


# Определяем наполнение таблиц, в соответствии с условием
T1 = [
    {"id": 1, "name": "ДФО"},
    {"id": 2, "name": "ЦФО"},
    {"id": 3, "name": "ДФО"},
    {"id": 4, "name": "УФО"},
    {"id": 5, "name": "ЦФО"},
]

T2 = [
    {"id": 1, "name": "ЦФО"},
    {"id": 2, "name": "ДФО"},
    {"id": 3, "name": "ЦФО"},
    {"id": 4, "name": "СФО"},
    {"id": 5, "name": "СЗФО"},
    {"id": 6, "name": "ДФО"},
]

T3 = [
    {"id": 1, "name": "СФО"},
    {"id": 2, "name": "ЦФО"},
    {"id": 3, "name": "СФО"},
    {"id": 4, "name": "УФО"},
    {"id": 5, "name": "СЗФО"},
]

# Пользовательские права
PERMISSIONS = {
    "П1": {"menu": ["ПМ1", "ПМ2", "ПМ3"], "filter": None},
    "П2": {"menu": ["ПМ1", "ПМ2"], "filter": {"name": ["ДФО"]}},
    "П3": {"menu": ["ПМ2", "ПМ3"], "filter": {"name": ["СФО", "СЗФО"]}},
}

TABLES = {
    "ПМ1": T1,
    "ПМ2": T2,
    "ПМ3": T3,
}


@app.get("/menu/{username}")
async def get_menu(username: str):
    """
    Проверяем пользователя в базе и если есть, то возвращаем список доступных пунктов меню.
    """
    if username not in PERMISSIONS:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    permissions = PERMISSIONS[username]
    return {"user": username, "menu": permissions["menu"]}

@app.get("/data/{username}/{menu}")
async def get_data(username: str, menu: str):
    """
    Возврат данных из таблиц, учитывая права доступа пользователя.
    """
    if username not in PERMISSIONS:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    permissions = PERMISSIONS[username]

    if menu not in permissions["menu"]:
        raise HTTPException(status_code=403, detail="Отсутствуют права")

    data = TABLES.get(menu, [])

    # Применение фильтров
    user_filter = permissions["filter"]
    if user_filter:
        data = [row for row in data if row["name"] in user_filter["name"]]

    return {"user": username, "menu": menu, "data": data}
