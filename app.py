# -*- coding: utf-8 -*-
"""
TimeTrack Pro - Система учёта рабочего времени
Основное приложение на Flask
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime, timedelta
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Конфигурация
DATABASE = 'timetrack.db'
ADMIN_PIN = '1234'

# Подключение к БД
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db()
    c = conn.cursor()
    
    # Таблица сотрудников
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        position TEXT,
        hourly_rate REAL DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица записей времени
    c.execute('''CREATE TABLE IF NOT EXISTS time_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date DATE NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME,
        break_minutes INTEGER DEFAULT 0,
        task_description TEXT,
        project TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    )''')
    
    # Таблица проектов
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#3498db',
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица настроек
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Добавляем тестовые данные если БД пустая
    c.execute('SELECT COUNT(*) FROM employees')
    if c.fetchone()[0] == 0:
        # Добавляем сотрудников
        c.execute("INSERT INTO employees (name, position, hourly_rate) VALUES ('Иван Иванов', 'Менеджер', 500)")
        c.execute("INSERT INTO employees (name, position, hourly_rate) VALUES ('Петр Петров', 'Разработчик', 800)")
        c.execute("INSERT INTO employees (name, position, hourly_rate) VALUES ('Анна Сидорова', 'Дизайнер', 600)")
        
        # Добавляем проекты
        c.execute("INSERT INTO projects (name, color) VALUES ('Основной проект', '#3498db')")
        c.execute("INSERT INTO projects (name, color) VALUES ('Внутренние задачи', '#e74c3c')")
        c.execute("INSERT INTO projects (name, color) VALUES ('Встречи', '#2ecc71')")
        
        # Добавляем настройки
        c.execute("INSERT INTO settings (key, value) VALUES ('work_start', '09:00')")
        c.execute("INSERT INTO settings (key, value) VALUES ('work_end', '18:00')")
        c.execute("INSERT INTO settings (key, value) VALUES ('break_duration', '60')")
    
    conn.commit()
    conn.close()

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Маршруты

@app.route('/')
def index():
    """Главная страница"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if request.method == 'POST':
        pin = request.form.get('pin')
        if pin == ADMIN_PIN:
            session['user_id'] = 1
            session['is_admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный PIN', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Панель управления"""
    conn = get_db()
    c = conn.cursor()
    
    # Получаем сотрудников
    c.execute('SELECT * FROM employees WHERE active = 1')
    employees = c.fetchall()
    
    # Получаем проекты
    c.execute('SELECT * FROM projects WHERE active = 1')
    projects = c.fetchall()
    
    # Получаем сегодняшние записи
    today = datetime.now().date()
    c.execute('''SELECT te.*, e.name as employee_name 
                 FROM time_entries te 
                 JOIN employees e ON te.employee_id = e.id 
                 WHERE te.date = ? 
                 ORDER BY te.start_time DESC''', (today,))
    today_entries = c.fetchall()
    
    # Статистика за неделю
    week_start = today - timedelta(days=today.weekday())
    c.execute('''SELECT e.name, SUM(
        (julianday(te.end_time) - julianday(te.start_time)) * 24 * 60 - te.break_minutes
    ) as total_minutes
    FROM time_entries te
    JOIN employees e ON te.employee_id = e.id
    WHERE te.date >= ? AND te.date <= ? AND te.end_time IS NOT NULL
    GROUP BY e.id''', (week_start, today))
    week_stats = c.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         employees=employees,
                         projects=projects,
                         today_entries=today_entries,
                         week_stats=week_stats,
                         today=today)

@app.route('/employees')
@login_required
def employees():
    """Управление сотрудниками"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM employees ORDER BY name')
    employees = c.fetchall()
    conn.close()
    return render_template('employees.html', employees=employees)

@app.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    """Добавить сотрудника"""
    name = request.form.get('name')
    position = request.form.get('position')
    hourly_rate = request.form.get('hourly_rate', 0)
    
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO employees (name, position, hourly_rate) VALUES (?, ?, ?)',
              (name, position, hourly_rate))
    conn.commit()
    conn.close()
    
    flash('Сотрудник добавлен', 'success')
    return redirect(url_for('employees'))

@app.route('/employees/delete/<int:id>')
@login_required
def delete_employee(id):
    """Удалить сотрудника"""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE employees SET active = 0 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Сотрудник удалён', 'success')
    return redirect(url_for('employees'))

@app.route('/time/add', methods=['POST'])
@login_required
def add_time_entry():
    """Добавить запись времени"""
    employee_id = request.form.get('employee_id')
    date = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    break_minutes = request.form.get('break_minutes', 0)
    task_description = request.form.get('task_description')
    project = request.form.get('project')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO time_entries 
                 (employee_id, date, start_time, end_time, break_minutes, task_description, project)
                 VALUES (?, ?, ?, ?, ?, ?, ?)',
              (employee_id, date, start_time, end_time, break_minutes, task_description, project))
    conn.commit()
    conn.close()
    
    flash('Запись добавлена', 'success')
    return redirect(url_for('dashboard'))

@app.route('/time/stop/<int:id>')
@login_required
def stop_time_entry(id):
    """Остановить запись времени"""
    conn = get_db()
    c = conn.cursor()
    current_time = datetime.now().strftime('%H:%M')
    c.execute('UPDATE time_entries SET end_time = ? WHERE id = ? AND end_time IS NULL', 
              (current_time, id))
    conn.commit()
    conn.close()
    
    flash('Запись остановлена', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reports')
@login_required
def reports():
    """Отчёты"""
    conn = get_db()
    c = conn.cursor()
    
    # Получаем даты за последние 30 дней
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Записи за период
    c.execute('''SELECT te.*, e.name as employee_name, e.hourly_rate
                 FROM time_entries te 
                 JOIN employees e ON te.employee_id = e.id 
                 WHERE te.date >= ? AND te.date <= ?
                 ORDER BY te.date DESC, te.start_time DESC''', 
              (start_date, end_date))
    entries = c.fetchall()
    
    # Сводка по сотрудникам
    c.execute('''SELECT e.name, 
                 COUNT(*) as entries_count,
                 SUM(
                    (julianday(te.end_time) - julianday(te.start_time)) * 24 * 60 - COALESCE(te.break_minutes, 0)
                 ) as total_minutes,
                 SUM(e.hourly_rate * (
                    (julianday(te.end_time) - julianday(te.start_time)) * 24 - COALESCE(te.break_minutes, 0)/60
                 )) as total_cost
                 FROM time_entries te
                 JOIN employees e ON te.employee_id = e.id
                 WHERE te.date >= ? AND te.date <= ? AND te.end_time IS NOT NULL
                 GROUP BY e.id''', (start_date, end_date))
    summary = c.fetchall()
    
    conn.close()
    
    return render_template('reports.html', 
                         entries=entries,
                         summary=summary,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/api/stats')
@login_required
def api_stats():
    """API для статистики"""
    conn = get_db()
    c = conn.cursor()
    
    # Статистика за сегодня
    today = datetime.now().date()
    c.execute('''SELECT 
        COUNT(*) as entries_count,
        SUM((julianday(te.end_time) - julianday(te.start_time)) * 24 * 60 - COALESCE(te.break_minutes, 0)) as total_minutes
        FROM time_entries te
        WHERE te.date = ? AND te.end_time IS NOT NULL''', (today,))
    today_stats = c.fetchone()
    
    conn.close()
    
    return jsonify({
        'today_entries': today_stats['entries_count'] or 0,
        'today_minutes': int(today_stats['total_minutes'] or 0)
    })

@app.route('/settings')
@login_required
def settings():
    """Настройки"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM settings')
    settings = {row['key']: row['value'] for row in c.fetchall()}
    conn.close()
    return render_template('settings.html', settings=settings)

@app.route('/settings/save', methods=['POST'])
@login_required
def save_settings():
    """Сохранить настройки"""
    work_start = request.form.get('work_start')
    work_end = request.form.get('work_end')
    break_duration = request.form.get('break_duration')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('work_start', work_start))
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('work_end', work_end))
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('break_duration', break_duration))
    conn.commit()
    conn.close()
    
    flash('Настройки сохранены', 'success')
    return redirect(url_for('settings'))

if __name__ == '__main__':
    # Инициализируем БД при первом запуске
    if not os.path.exists(DATABASE):
        init_db()
        print(f"База данных {DATABASE} создана")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
