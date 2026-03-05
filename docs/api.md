# WorkTabel API — описание для интеграций

(…предыдущий текст…)

---

## Примеры запросов

### Регистрация пользователя
```
POST /api/auth/register
Content-Type: application/json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "manager"
}
```

### Вход в систему
```
POST /api/auth/login
Content-Type: application/json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Получение списка сотрудников
```
GET /api/employees
Authorization: Bearer <jwt-token>
```

### Создание графика работы
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

### Импорт графика по шаблону
```
POST /api/schedule/import
Authorization: Bearer <jwt-token>
Content-Type: multipart/form-data
file: schedule_template.xlsx
```

### Экспорт отчёта в PDF
```
GET /api/reports/pdf?period=2026-03
Authorization: Bearer <jwt-token>
```

### Отправка сообщения в чат
```
POST /api/messages
Authorization: Bearer <jwt-token>
Content-Type: application/json
{
  "chat_id": 5,
  "text": "Проверьте инвентаризацию на точке №2"
}
```

### Подключение Telegram-канала
```
POST /api/integrations/telegram
Authorization: Bearer <jwt-token>
Content-Type: application/json
{
  "channel_id": "@worktabel_channel"
}
```

---

**Документация будет дополняться по мере реализации.**
