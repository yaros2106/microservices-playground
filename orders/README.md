# orders

Сервис заказов.

## Запуск локально

Из папки `orders`:

```bash
uv sync                                          # поставить зависимости (первый раз или после git pull)
uv run uvicorn main:app --reload --port 8101
```

- http://localhost:8101/healthcheck
- http://localhost:8101/docs — Swagger

## Зависимости

```bash
uv add <пакет>       # добавить
uv remove <пакет>    # удалить
```
