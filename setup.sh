#!/bin/bash
#
# TimeTrack Pro - Установщик для ленивых
# Запусти этот скрипт и всё установится само!
#

set -e

echo "🚀 Установка TimeTrack Pro..."
echo "================================="

# Проверка Python
echo "📌 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python не найден! Установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Создаём виртуальное окружение
echo "📌 Создание виртуального окружения..."
python3 -m venv venv

# Активируем окружение
echo "📌 Активация окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📌 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Запускаем приложение
echo ""
echo "================================="
echo "✅ Установка завершена!"
echo "================================="
echo ""
echo "Запускаю TimeTrack Pro..."
echo "Открой в браузере: http://localhost:5000"
echo "PIN для входа: 1234"
echo ""

python3 app.py
