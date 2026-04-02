# WorkTable — Система управления питанием

Веб-приложение для управления питанием в общепите с интеграцией Telegram бота.

## Быстрый старт

### 1. Настройка Supabase
1. Создайте проект на [supabase.com](https://supabase.com)
2. Создайте таблицы:
```sql
-- Таблица пользователей
create table users (
  id uuid primary key references auth.users,
  email text,
  name text,
  role text default 'partner',
  is_active boolean default false,
  created_at timestamp with time zone default now()
);

-- Таблица меню
create table menus (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  day_type text,
  breakfast text,
  lunch text,
  dinner text,
  mode text default '5/2'
);

-- Таблица заказов
create table orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  start_date date not null,
  end_date date not null,
  person_count integer,
  mode text,
  status text default 'pending',
  created_at timestamp with time zone default now()
);

-- Включить RLS
alter table users enable row level security;
alter table menus enable row level security;
alter table orders enable row level security;

-- Политики
create policy "Users can read own data" on users for select using (auth.uid() = id);
create policy "Users can read menus" on menus for select using (true);
create policy "Users can create orders" on orders for insert with check (auth.uid() = user_id);
create policy "Users can read own orders" on orders for select using (auth.uid() = user_id);
```

### 2. Настройка приложения
```bash
npm install
```

Скопируйте `.env.example` в `.env` и заполните:
```
VITE_SUPABASE_URL=ваш-url
VITE_SUPABASE_ANON_KEY=ваш-anon-key
```

### 3. Деплой на Netlify
1. Подключите репозиторий к Netlify
2. Добавьте переменные окружения
3. Деплой произойдёт автоматически

## Функционал

### Партнёры
- Регистрация и вход
- Просмотр меню на неделю
- Создание заказов
- История заказов

### Администратор
- Активация партнёров
- Подтверждение заказов
- Отправка в Telegram

## Технологии
- React + Vite
- Supabase (база данных)
- Netlify (хостинг)
- Telegram Bot API