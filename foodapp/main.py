# -*- coding: utf-8 -*-
"""
FoodApp - Система управления общепитом
Основное приложение FastAPI
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import os
import hashlib
import secrets
from functools import wraps

app = FastAPI(title="FoodApp API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
DATABASE = "foodapp.db"
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Модели данных

class User(BaseModel):
    id: int
    username: str
    email: str
    role: str  # admin, manager, client, production
    full_name: Optional[str] = None
    assigned_clients: Optional[str] = None  # для менеджеров
    assigned_production: Optional[str] = None  # для менеджеров
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str
    full_name: Optional[str] = None
    assigned_clients: Optional[str] = None
    assigned_production: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class Client(BaseModel):
    id: int
    name: str
    official_name: str
    inn: str
    director: str
    phone: str
    email: str
    address: str
    manager_id: int
    contract_type: str  # daily, weekly, seasonal
    price: float
    delay_days: int
    discount: float
    status: str

class Production(BaseModel):
    id: int
    name: str
    product_type: str
    volume: float
    exclusions: str
    contacts: str
    address: str
    price: float
    status: str

class Dish(BaseModel):
    id: int
    name: str
    weight: int
    composition: str
    allergens: str
    category: str
    cost: float
    price: float

class MenuItem(BaseModel):
    id: int
    date: str
    day: str
    meal_type: str  # breakfast, lunch, dinner, snack
    dish_id: int
    client_id: int
    weight: int
    price: float
    status: str

class Order(BaseModel):
    id: int
    date: str
    client_id: int
    dish_id: int
    quantity: int
    price: float
    total: float
    cost: float
    profit: float
    manager_id: int
    payment_status: str

class Message(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    timestamp: str
    is_read: bool

class FileRecord(BaseModel):
    id: int
    filename: str
    file_path: str
    owner_id: int
    recipient_id: int
    uploaded_at: str

class Feedback(BaseModel):
    id: int
    user_id: int
    content: str
    timestamp: str
    is_resolved: bool


# База данных

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация БД"""
    conn = get_db()
    c = conn.cursor()
    
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT,
        assigned_clients TEXT,
        assigned_production TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Клиенты
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        official_name TEXT,
        inn TEXT,
        director TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        manager_id INTEGER,
        contract_type TEXT,
        price REAL DEFAULT 0,
        delay_days INTEGER DEFAULT 0,
        discount REAL DEFAULT 0,
        status TEXT DEFAULT 'Активен',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Производство
    c.execute('''CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        product_type TEXT,
        volume REAL DEFAULT 0,
        exclusions TEXT,
        contacts TEXT,
        address TEXT,
        price REAL DEFAULT 0,
        status TEXT DEFAULT 'Активен',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Блюда
    c.execute('''CREATE TABLE IF NOT EXISTS dishes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        weight INTEGER DEFAULT 0,
        composition TEXT,
        allergens TEXT,
        category TEXT,
        cost REAL DEFAULT 0,
        price REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Меню
    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        day TEXT,
        meal_type TEXT,
        dish_id INTEGER,
        client_id INTEGER,
        weight INTEGER DEFAULT 0,
        price REAL DEFAULT 0,
        status TEXT DEFAULT 'Активно',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Заказы
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        client_id INTEGER,
        dish_id INTEGER,
        quantity INTEGER DEFAULT 0,
        price REAL DEFAULT 0,
        total REAL DEFAULT 0,
        cost REAL DEFAULT 0,
        profit REAL DEFAULT 0,
        manager_id INTEGER,
        payment_status TEXT DEFAULT 'Ожидает',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Сообщения
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_read INTEGER DEFAULT 0
    )''')
    
    # Файлы
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        owner_id INTEGER NOT NULL,
        recipient_id INTEGER,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Обратная связь
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_resolved INTEGER DEFAULT 0
    )''')
    
    # Логи
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Создаём админа по умолчанию
    c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if c.fetchone()[0] == 0:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, email, role, full_name) VALUES (?, ?, ?, ?, ?)",
                  ("admin", admin_hash, "admin@foodapp.ru", "admin", "Администратор"))
    
    conn.commit()
    conn.close()

# Хелперы

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return secrets.token_urlsafe(32)

def log_action(user_id: int, action: str, details: str = "", ip: str = ""):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
              (user_id, action, details, ip))
    conn.commit()
    conn.close()

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Упрощённая проверка токена
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (token[:20],))
    user = c.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return User(**dict(user))

def require_role(*roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: User = Depends(get_current_user), **kwargs):
            if user.role not in roles:
                raise HTTPException(status_code=403, detail="Нет доступа")
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

# API Эндпоинты

@app.get("/")
async def root():
    return {"message": "FoodApp API", "version": "1.0.0"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (form_data.username,))
    user = c.fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    log_action(user["id"], "login", f"User {user['username']} logged in")
    return {"access_token": access_token, "token_type": "bearer"}

# Дашборд админа
@app.get("/api/admin/dashboard")
@require_role("admin")
async def admin_dashboard(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    
    # Статистика
    c.execute("SELECT COUNT(*) as count FROM users WHERE role='manager'")
    managers_count = c.fetchone()["count"]
    
    c.execute("SELECT COUNT(*) as count FROM clients")
    clients_count = c.fetchone()["count"]
    
    c.execute("SELECT COUNT(*) as count FROM production")
    production_count = c.fetchone()["count"]
    
    c.execute("SELECT COUNT(*) as count FROM orders WHERE date = date('now')")
    today_orders = c.fetchone()["count"]
    
    c.execute("SELECT SUM(profit) as total FROM orders WHERE date = date('now')")
    today_profit = c.fetchone()["total"] or 0
    
    # Активность пользователей
    c.execute('''SELECT u.username, u.role, COUNT(l.id) as actions 
                 FROM users u 
                 LEFT JOIN logs l ON u.id = l.user_id AND l.timestamp > datetime('now', '-24 hours')
                 GROUP BY u.id''')
    user_activity = [dict(row) for row in c.fetchall()]
    
    # Последние заказы
    c.execute('''SELECT o.*, c.name as client_name, d.name as dish_name 
                 FROM orders o 
                 JOIN clients c ON o.client_id = c.id 
                 JOIN dishes d ON o.dish_id = d.id
                 ORDER BY o.created_at DESC LIMIT 10''')
    recent_orders = [dict(row) for row in c.fetchall()]
    
    # Непрочитанные сообщения
    c.execute("SELECT COUNT(*) as count FROM messages WHERE recipient_id = ? AND is_read = 0", (user.id,))
    unread_messages = c.fetchone()["count"]
    
    conn.close()
    
    return {
        "managers_count": managers_count,
        "clients_count": clients_count,
        "production_count": production_count,
        "today_orders": today_orders,
        "today_profit": today_profit,
        "user_activity": user_activity,
        "recent_orders": recent_orders,
        "unread_messages": unread_messages
    }

# Дашборд менеджера
@app.get("/api/manager/dashboard")
@require_role("manager")
async def manager_dashboard(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    
    # Получаем ID менеджера
    c.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    manager = c.fetchone()
    manager_id = manager["id"]
    
    # Свои клиенты
    c.execute("SELECT COUNT(*) as count FROM clients WHERE manager_id = ?", (manager_id,))
    my_clients = c.fetchone()["count"]
    
    # Свои заказы за сегодня
    c.execute("SELECT COUNT(*) as count FROM orders WHERE manager_id = ? AND date = date('now')", (manager_id,))
    my_today_orders = c.fetchone()["count"]
    
    # Прибыль за сегодня
    c.execute("SELECT SUM(profit) as total FROM orders WHERE manager_id = ? AND date = date('now')", (manager_id,))
    my_today_profit = c.fetchone()["total"] or 0
    
    # Непрочитанные сообщения
    c.execute("SELECT COUNT(*) as count FROM messages WHERE recipient_id = ? AND is_read = 0", (manager_id,))
    unread_messages = c.fetchone()["count"]
    
    # Мои последние заказы
    c.execute('''SELECT o.*, c.name as client_name, d.name as dish_name 
                 FROM orders o 
                 JOIN clients c ON o.client_id = c.id 
                 JOIN dishes d ON o.dish_id = d.id
                 WHERE o.manager_id = ?
                 ORDER BY o.created_at DESC LIMIT 10''', (manager_id,))
    my_orders = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {
        "my_clients": my_clients,
        "my_today_orders": my_today_orders,
        "my_today_profit": my_today_profit,
        "unread_messages": unread_messages,
        "my_orders": my_orders
    }

# Клиенты (только админ и менеджер)
@app.get("/api/clients")
@require_role("admin", "manager")
async def get_clients(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    
    if user.role == "manager":
        c.execute("SELECT id FROM users WHERE username = ?", (user.username,))
        manager = c.fetchone()
        c.execute("SELECT * FROM clients WHERE manager_id = ?", (manager["id"],))
    else:
        c.execute("SELECT * FROM clients")
    
    clients = [dict(row) for row in c.fetchall()]
    conn.close()
    return clients

@app.post("/api/clients")
@require_role("admin")
async def create_client(client: Client, user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO clients (name, official_name, inn, director, phone, email, address, manager_id, contract_type, price, delay_days, discount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (client.name, client.official_name, client.inn, client.director, client.phone, client.email, client.address, 
               client.manager_id, client.contract_type, client.price, client.delay_days, client.discount, client.status))
    conn.commit()
    client_id = c.lastrowid
    conn.close()
    log_action(user.id, "create_client", f"Created client {client.name}")
    return {"id": client_id, "status": "created"}

# Производство (только админ)
@app.get("/api/production")
@require_role("admin", "manager")
async def get_production(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM production")
    production = [dict(row) for row in c.fetchall()]
    conn.close()
    return production

# Сообщения
@app.get("/api/messages")
async def get_messages(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE recipient_id = ? ORDER BY timestamp DESC", (user.id,))
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    return messages

@app.post("/api/messages")
async def send_message(recipient_id: int, content: str, user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
              (user.id, recipient_id, content))
    conn.commit()
    conn.close()
    log_action(user.id, "send_message", f"To user {recipient_id}")
    return {"status": "sent"}

# Обратная связь
@app.post("/api/feedback")
async def submit_feedback(content: str, user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, content) VALUES (?, ?)", (user.id, content))
    conn.commit()
    conn.close()
    log_action(user.id, "feedback", content[:50])
    return {"status": "submitted"}

# Файлы
@app.get("/api/files")
async def get_files(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE owner_id = ? OR recipient_id = ? ORDER BY uploaded_at DESC",
              (user.id, user.id))
    files = [dict(row) for row in c.fetchall()]
    conn.close()
    return files

# Логи
@app.get("/api/logs")
@require_role("admin")
async def get_logs(limit: int = 100, user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT * FROM logs ORDER BY timestamp DESC LIMIT {limit}")
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return logs

# Заказы
@app.get("/api/orders")
async def get_orders(user: User = Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    
    if user.role == "admin":
        c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    elif user.role == "manager":
        c.execute("SELECT id FROM users WHERE username = ?", (user.username,))
        manager = c.fetchone()
        c.execute("SELECT * FROM orders WHERE manager_id = ? ORDER BY created_at DESC", (manager["id"],))
    else:
        c.execute("SELECT * FROM orders WHERE client_id = ? ORDER BY created_at DESC", (user.id,))
    
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    return orders

if __name__ == "__main__":
    if not os.path.exists(DATABASE):
        init_db()
        print(f"База данных {DATABASE} создана")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
