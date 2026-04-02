-- WorkTable Database Migration
-- Создание таблиц для системы управления питанием

-- Таблица пользователей (партнёров)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    role TEXT DEFAULT 'partner' CHECK (role IN ('partner', 'admin')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица меню
CREATE TABLE IF NOT EXISTS menus (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    breakfast TEXT,
    lunch TEXT,
    dinner TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица заказов
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    person_count INTEGER NOT NULL DEFAULT 1,
    mode TEXT NOT NULL DEFAULT '5/2' CHECK (mode IN ('5/2', '7/0')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'sent', 'rejected')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_menus_date ON menus(date);
CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);

-- RLS политики (безопасность)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE menus ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Полики для users
CREATE POLICY "Anyone can read users" ON users FOR SELECT USING (true);
CREATE POLICY "Anyone can insert users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update users" ON users FOR UPDATE USING (true);

-- Полики для menus
CREATE POLICY "Anyone can read menus" ON menus FOR SELECT USING (true);
CREATE POLICY "Anyone can insert menus" ON menus FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update menus" ON menus FOR UPDATE USING (true);

-- Полики для orders
CREATE POLICY "Anyone can read orders" ON orders FOR SELECT USING (true);
CREATE POLICY "Anyone can insert orders" ON orders FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update orders" ON orders FOR UPDATE USING (true);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_menus_updated_at BEFORE UPDATE ON menus
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Тестовые данные
INSERT INTO users (telegram_id, name, email, role, is_active) 
VALUES 
    (123456789, 'Тестовый партнёр', 'test@example.com', 'partner', true),
    (987654321, 'Администратор', 'admin@worktable.ru', 'admin', true)
ON CONFLICT (telegram_id) DO NOTHING;

INSERT INTO menus (date, breakfast, lunch, dinner) 
VALUES 
    (CURRENT_DATE, 'Каша овсяная, чай', 'Борщ, салат, компот', 'Рыба на пару, овощи'),
    (CURRENT_DATE + 1, 'Яичница, хлеб', 'Суп куриный, второе', 'Котлеты, картофель')
ON CONFLICT (date) DO NOTHING;

INSERT INTO orders (user_id, start_date, end_date, person_count, mode, status)
SELECT 
    (SELECT id FROM users WHERE role = 'partner' LIMIT 1),
    CURRENT_DATE,
    CURRENT_DATE + 6,
    5,
    '5/2',
    'pending'
WHERE EXISTS (SELECT 1 FROM users WHERE role = 'partner');