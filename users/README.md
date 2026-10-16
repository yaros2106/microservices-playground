# users

Сервис пользователей.

## Запуск локально

Из папки `users` (база должна быть запущена: `docker compose up -d users-db`):

```bash
uv sync                                          # поставить зависимости (первый раз или после git pull)
uv run uvicorn main:app --reload --port 8102
```

- http://localhost:8102/healthcheck
- http://localhost:8102/docs — Swagger
