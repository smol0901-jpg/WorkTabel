# WorkTabel API — описание для интеграций

(…предыдущий текст…)

---

## Примеры ошибок API

### 1. Ошибка авторизации
```
HTTP/1.1 401 Unauthorized
{
  "error": "Unauthorized",
  "message": "Invalid or missing token"
}
```

### 2. Нет доступа (недостаточно прав)
```
HTTP/1.1 403 Forbidden
{
  "error": "Forbidden",
  "message": "You do not have permission to perform this action"
}
```

### 3. Не найдено
```
HTTP/1.1 404 Not Found
{
  "error": "Not Found",
  "message": "Employee not found"
}
```

### 4. Ошибка валидации данных
```
HTTP/1.1 400 Bad Request
{
  "error": "Validation Error",
  "message": "Field 'email' is required"
}
```

### 5. Ошибка сервера
```
HTTP/1.1 500 Internal Server Error
{
  "error": "Internal Server Error",
  "message": "Unexpected error occurred"
}
```

---

**Документация будет дополняться по мере реализации.**
