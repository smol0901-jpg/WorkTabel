-- WorkTable Database Migration
-- Выполните этот скрипт в SQL Editor Supabase

-- 1. Создаём таблицу users
create table if not exists public.users (
  id uuid not null primary key references auth.users(id) on delete cascade,
  email text not null,
  name text,
  role text default 'partner' check (role in ('partner', 'admin')),
  is_active boolean default false,
  created_at timestamp with time zone default now()
);

-- 2. Создаём таблицу menus
create table if not exists public.menus (
  id uuid default gen_random_uuid() primary key,
  date date not null unique,
  day_type text,
  breakfast text,
  lunch text,
  dinner text,
  mode text default '5/2' check (mode in ('5/2', '7/0')),
  created_at timestamp with time zone default now()
);

-- 3. Создаём таблицу orders
create table if not exists public.orders (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade,
  start_date date not null,
  end_date date not null,
  person_count integer not null default 1,
  mode text default '5/2',
  status text default 'pending' check (status in ('pending', 'confirmed', 'sent')),
  created_at timestamp with time zone default now()
);

-- 4. Включаем RLS
alter table public.users enable row level security;
alter table public.menus enable row level security;
alter table public.orders enable row level security;

-- 5. Политики для users
create policy "Users can read own profile" on public.users for select using (auth.uid() = id);
create policy "Users can update own profile" on public.users for update using (auth.uid() = id);
create policy "Admins can manage all users" on public.users for all using (
  exists (select 1 from public.users where id = auth.uid() and role = 'admin')
);

-- 6. Политики для menus
create policy "Anyone can read menus" on public.menus for select using (true);
create policy "Admins can manage menus" on public.menus for all using (
  exists (select 1 from public.users where id = auth.uid() and role = 'admin')
);

-- 7. Политики для orders
create policy "Users can create orders" on public.orders for insert with check (auth.uid() = user_id);
create policy "Users can read own orders" on public.orders for select using (auth.uid() = user_id);
create policy "Users can update own orders" on public.orders for update using (auth.uid() = user_id);
create policy "Admins can manage all orders" on public.orders for all using (
  exists (select 1 from public.users where id = auth.uid() and role = 'admin')
);

-- 8. Функция для автоматического создания пользователя
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, name, role, is_active)
  values (new.id, new.email, new.raw_user_meta_data->>'name', 'partner', false);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 9. Индексы
create index idx_menus_date on public.menus(date);
create index idx_menus_mode on public.menus(mode);
create index idx_orders_user_id on public.orders(user_id);
create index idx_orders_status on public.orders(status);
create index idx_users_role on public.users(role);