#!/usr/bin/env python3
"""
WorkTable - Скрипт синхронизации меню из Google Таблицы в Supabase

Настройка:
1. Создайте Google Таблицу с листами "5/2" и "7/0"
2. Сделайте её общедоступной (Файл -> Опубликовать в интернете)
3. Настройте CRON для запуска скрипта

Формат таблицы:
| Дата     | Завтрак | Обед   | Ужин   |
|----------|---------|--------|--------|
| 2026-04-01| Каша   | Борщ  | Рыба   |
"""

import os
import sys
from datetime import datetime
from google.auth import default
from googleapiclient.discovery import build
from supabase import create_client

SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def get_google_sheets():
    credentials, _ = default()
    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

def get_menu_data(sheets, mode='5/2'):
    try:
        result = sheets.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{mode}!A2:D100"
        ).execute()
        
        values = result.get('values', [])
        menus = []
        
        for row in values:
            if len(row) >= 4 and row[0]:
                try:
                    date = datetime.strptime(row[0], '%Y-%m-%d').date()
                    menus.append({
                        'date': str(date),
                        'breakfast': row[1] if len(row) > 1 else '',
                        'lunch': row[2] if len(row) > 2 else '',
                        'dinner': row[3] if len(row) > 3 else '',
                        'mode': mode
                    })
                except ValueError:
                    continue
        
        return menus
    except Exception as e:
        print(f"Ошибка получения данных {mode}: {e}")
        return []

def sync_to_supabase(menus, mode):
    if not menus:
        return
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for menu in menus:
        supabase.table('menus').upsert(menu, on_conflict='date').execute()
    
    print(f"Синхронизировано {len(menus)} записей ({mode})")

def main():
    print(f"[{datetime.now()}] Начало синхронизации меню...")
    
    if not SPREADSHEET_ID:
        print("Ошибка: GOOGLE_SHEET_ID не задан")
        sys.exit(1)
    
    try:
        sheets = get_google_sheets()
        
        for mode in ['5/2', '7/0']:
            menus = get_menu_data(sheets, mode)
            sync_to_supabase(menus, mode)
        
        print(f"[{datetime.now()}] Синхронизация завершена!")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()