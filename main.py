
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt

app = FastAPI()

# Словарь с логинами и паролями пользователей
USERS = {
    "user1": {"password": "password1", "permissions": "П1"},
    "user2": {"password": "password2", "permissions": "П2"},
    "user3": {"password": "password3", "permissions": "П3"},
}

# Ключ, алгоритм, и время жизни токена
SECRET_KEY = "key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

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
    "П1": {"menu": ["PM1", "PM2", "PM3"], "filter": None},
    "П2": {"menu": ["PM1", "PM2"], "filter": {"name": ["ДФО"]}},
    "П3": {"menu": ["PM2", "PM3"], "filter": {"name": ["СФО", "СЗФО"]}},
}

TABLES = {
    "PM1": T1,
    "PM2": T2,
    "PM3": T3,
}

# Настраиваем схему аутентификаци и указываем путь для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Модель для токена
class Token(BaseModel):
    access_token: str
    token_type: str

# Принимаем данные пользователя, генерируем токер и отдаем в виде строки
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Проверка токена и получение данных пользователя
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Ошибка учетных данных")
        return USERS[username]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")

# Эндпоинт для аутентификации пользователя и генерции токена
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Эндпоинт для предоставления меню пользователя, учитывая права доступа
@app.get("/menu")
async def get_menu(current_user: dict = Depends(get_current_user)):
    permissions_key = current_user["permissions"]
    permissions = PERMISSIONS.get(permissions_key)
    if not permissions:
        raise HTTPException(status_code=403, detail="Нет прав доступа")
    return {"menu": permissions["menu"]}

# Эндпоинт для получения данных из таблиц меню
@app.get("/data/{menu}")
async def get_data(menu: str, current_user: dict = Depends(get_current_user)):
    permissions_key = current_user["permissions"]
    permissions = PERMISSIONS.get(permissions_key)

    if menu not in permissions["menu"]:
        raise HTTPException(status_code=403, detail="Нет доступа к этой таблице")

    data = TABLES.get(menu, [])
    user_filter = permissions.get("filter")
    if user_filter:
        data = [row for row in data if row["name"] in user_filter["name"]]

    return {"menu": menu, "data": data}