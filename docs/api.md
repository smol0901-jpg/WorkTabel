# WorkTabel API — описание для интеграций

## Общие принципы
- REST API (JSON)
- Авторизация через JWT-токен
- Все методы доступны только авторизованным пользователям с нужными правами

## Основные эндпоинты

### 1. Аутентификация и пользователи
- `POST /api/auth/register` — регистрация пользователя
- `POST /api/auth/login` — вход в систему
- `GET /api/users/me` — информация о текущем пользователе
- `GET /api/users` — список пользователей (для админа)

### 2. Компании, точки, сотрудники
- `GET /api/companies` — список компаний
- `POST /api/companies` — создать компанию
- `GET /api/branches` — список точек
- `POST /api/branches` — создать точку
- `GET /api/employees` — список сотрудников
- `POST /api/employees` — добавить сотрудника

### 3. График работы
- `GET /api/schedule` — получить график
- `POST /api/schedule` — создать/обновить график
- `POST /api/schedule/import` — импорт графика по шаблону

### 4. Выручка и ФОТ
- `GET /api/revenue` — получить выручку
- `POST /api/revenue` — добавить выручку
- `GET /api/payroll` — расчёт ФОТ

### 5. Внутренний чат и задачи
- `GET /api/chat` — список чатов/тем
- `POST /api/chat` — создать чат/тему
- `GET /api/messages` — сообщения в чате
- `POST /api/messages` — отправить сообщение
- `POST /api/tasks` — создать внутреннюю задачу
- `GET /api/tasks` — список задач

### 6. Интеграции и уведомления
- `POST /api/integrations/telegram` — подключить Telegram-канал
- `POST /api/integrations/ai` — подключить нейросеть (GigaChat, ChatGPT)
- `POST /api/notifications` — отправить уведомление

### 7. Экспорт/импорт
- `GET /api/reports/pdf` — экспорт отчёта в PDF
- `GET /api/reports/html` — экспорт отчёта в HTML
- `POST /api/schedule/import` — импорт графика (Excel/CSV)

---

## Пример запроса
```
POST /api/schedule
Authorization: Bearer <jwt-token>
Content-Type: application/json
{
  "employee_id": 123,
  "date": "2026-03-10",
  "shift": "day"
}
```

---

**Документация будет дополняться по мере реализации.**
