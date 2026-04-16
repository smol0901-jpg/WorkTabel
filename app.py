from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime, timedelta
import sqlite3
import os
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Конфигурация
DATABASE = 'foodapp.db'

# Подключение к БД
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
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
    
    # Создаём админа
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

def log_action(user_id: int, action: str, details: str = "", ip: str = ""):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
              (user_id, action, details, ip))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session.get('role') not in roles:
                flash('Нет доступа', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Маршруты

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and verify_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            log_action(user['id'], 'login', f'User {username} logged in')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_action(user_id, 'logout', 'User logged out')
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    
    user_role = session.get('role')
    user_id = session.get('user_id')
    
    if user_role == 'admin':
        # Статистика
        c.execute("SELECT COUNT(*) as c FROM users WHERE role='manager'")
        managers = c.fetchone()['c']
        
        c.execute("SELECT COUNT(*) as c FROM clients")
        clients = c.fetchone()['c']
        
        c.execute("SELECT COUNT(*) as c FROM production")
        production = c.fetchone()['c']
        
        c.execute("SELECT COUNT(*) as c FROM orders WHERE date = date('now')")
        today_orders = c.fetchone()['c']
        
        c.execute("SELECT SUM(profit) as t FROM orders WHERE date = date('now')")
        today_profit = c.fetchone()['t'] or 0
        
        # Активность
        c.execute('''SELECT u.username, u.role, COUNT(l.id) as a 
                     FROM users u 
                     LEFT JOIN logs l ON u.id = l.user_id AND l.timestamp > datetime('now', '-24 hours')
                     GROUP BY u.id''')
        activity = c.fetchall()
        
        # Заказы
        c.execute('''SELECT o.*, c.name as cn, d.name as dn 
                     FROM orders o 
                     JOIN clients c ON o.client_id = c.id 
                     JOIN dishes d ON o.dish_id = d.id
                     ORDER BY o.created_at DESC LIMIT 10''')
        orders = c.fetchall()
        
        data = {
            'managers': managers,
            'clients': clients,
            'production': production,
            'today_orders': today_orders,
            'today_profit': today_profit,
            'activity': activity,
            'orders': orders
        }
    else:  # manager
        c.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
        manager = c.fetchone()
        manager_id = manager['id']
        
        c.execute("SELECT COUNT(*) as c FROM clients WHERE manager_id = ?", (manager_id,))
        my_clients = c.fetchone()['c']
        
        c.execute("SELECT COUNT(*) as c FROM orders WHERE manager_id = ? AND date = date('now')", (manager_id,))
        my_orders = c.fetchone()['c']
        
        c.execute("SELECT SUM(profit) as t FROM orders WHERE manager_id = ? AND date = date('now')", (manager_id,))
        my_profit = c.fetchone()['t'] or 0
        
        c.execute("SELECT COUNT(*) as c FROM messages WHERE recipient_id = ? AND is_read = 0", (manager_id,))
        unread = c.fetchone()['c']
        
        c.execute('''SELECT o.*, c.name as cn, d.name as dn 
                     FROM orders o 
                     JOIN clients c ON o.client_id = c.id 
                     JOIN dishes d ON o.dish_id = d.id
                     WHERE o.manager_id = ?
                     ORDER BY o.created_at DESC LIMIT 10''', (manager_id,))
        my_orders_list = c.fetchall()
        
        data = {
            'my_clients': my_clients,
            'my_orders': my_orders,
            'my_profit': my_profit,
            'unread': unread,
            'orders': my_orders_list
        }
    
    conn.close()
    return render_template('dashboard.html', data=data, role=user_role)

@app.route('/clients')
@login_required
@role_required(['admin', 'manager'])
def clients():
    conn = get_db()
    c = conn.cursor()
    
    if session.get('role') == 'manager':
        c.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
        manager = c.fetchone()
        c.execute("SELECT * FROM clients WHERE manager_id = ?", (manager['id'],))
    else:
        c.execute("SELECT * FROM clients")
    
    clients_list = c.fetchall()
    conn.close()
    return render_template('clients.html', clients=clients_list)

@app.route('/production')
@login_required
@role_required(['admin', 'manager'])
def production():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM production")
    production_list = c.fetchall()
    conn.close()
    return render_template('production.html', production=production_list)

@app.route('/orders')
@login_required
def orders():
    conn = get_db()
    c = conn.cursor()
    
    if session.get('role') == 'admin':
        c.execute('''SELECT o.*, c.name as cn, d.name as dn, u.username as mn
                     FROM orders o 
                     JOIN clients c ON o.client_id = c.id 
                     JOIN dishes d ON o.dish_id = d.id
                     JOIN users u ON o.manager_id = u.id
                     ORDER BY o.created_at DESC''')
    elif session.get('role') == 'manager':
        c.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
        manager = c.fetchone()
        c.execute('''SELECT o.*, c.name as cn, d.name as dn
                     FROM orders o 
                     JOIN clients c ON o.client_id = c.id 
                     JOIN dishes d ON o.dish_id = d.id
                     WHERE o.manager_id = ?
                     ORDER BY o.created_at DESC''', (manager['id'],))
    else:
        c.execute('''SELECT o.*, c.name as cn, d.name as dn
                     FROM orders o 
                     JOIN clients c ON o.client_id = c.id 
                     JOIN dishes d ON o.dish_id = d.id
                     ORDER BY o.created_at DESC''')
    
    orders_list = c.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders_list)

@app.route('/messages')
@login_required
def messages():
    conn = get_db()
    c = conn.cursor()
    
    user_id = session.get('user_id')
    
    # Полученные
    c.execute('''SELECT m.*, u.username as sender_name, u.full_name as sender_full
                FROM messages m 
                JOIN users u ON m.sender_id = u.id
                WHERE m.recipient_id = ?
                ORDER BY m.timestamp DESC''', (user_id,))
    received = c.fetchall()
    
    # Отправленные
    c.execute('''SELECT m.*, u.username as recipient_name, u.full_name as recipient_full
                FROM messages m 
                JOIN users u ON m.recipient_id = u.id
                WHERE m.sender_id = ?
                ORDER BY m.timestamp DESC''', (user_id,))
    sent = c.fetchall()
    
    # Все пользователи для отправки
    c.execute("SELECT id, username, full_name, role FROM users WHERE id != ?", (user_id,))
    users = c.fetchall()
    
    conn.close()
    return render_template('messages.html', received=received, sent=sent, users=users)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    content = request.form.get('content')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
              (session['user_id'], recipient_id, content))
    conn.commit()
    conn.close()
    
    log_action(session['user_id'], 'send_message', f'To user {recipient_id}')
    flash('Сообщение отправлено', 'success')
    return redirect(url_for('messages'))

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        content = request.form.get('content')
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO feedback (user_id, content) VALUES (?, ?)",
                  (session['user_id'], content))
        conn.commit()
        conn.close()
        log_action(session['user_id'], 'feedback', content[:50])
        flash('Обратная связь отправлена', 'success')
        return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@app.route('/logs')
@login_required
@role_required(['admin'])
def logs():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT l.*, u.username FROM logs l JOIN users u ON l.user_id = u.id ORDER BY l.timestamp DESC LIMIT 100")
    logs_list = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs_list)


# API эндпоинты для AJAX

@app.route('/api/stats')
@login_required
def api_stats():
    conn = get_db()
    c = conn.cursor()
    
    if session.get('role') == 'admin':
        c.execute("SELECT COUNT(*) as c FROM orders WHERE date = date('now')")
        orders = c.fetchone()['c']
        c.execute("SELECT SUM(profit) as p FROM orders WHERE date = date('now')")
        profit = c.fetchone()['p'] or 0
    else:
        c.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
        manager = c.fetchone()
        c.execute("SELECT COUNT(*) as c FROM orders WHERE manager_id = ? AND date = date('now')", (manager['id'],))
        orders = c.fetchone()['c']
        c.execute("SELECT SUM(profit) as p FROM orders WHERE manager_id = ? AND date = date('now')", (manager['id'],))
        profit = c.fetchone()['p'] or 0
    
    conn.close()
    return jsonify({'orders': orders, 'profit': profit})

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
        print(f"База данных {DATABASE} создана")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
