# microshop

Учебный проект по микросервисам: FastAPI, Postgres, Docker Compose.

| Сервис | Порт на маке | База (порт на маке) |
|---|---|---|
| orders | http://localhost:8101/docs | orders-db (5401) |
| users  | http://localhost:8102/docs | users-db (5402) |

## Запуск

Все команды из корня проекта (где `docker-compose.yml`):

```bash
docker compose up -d            # поднять всё
docker compose ps               # что работает
docker compose logs -f users    # логи сервиса (Ctrl+C — выйти из логов)
docker compose down             # остановить всё (данные баз сохраняются)
```

Код подключён в контейнеры, uvicorn запущен с `--reload`: правки в `.py`
подхватываются сами, пересобирать не нужно.

Пересборка (`docker compose up --build -d`) нужна только после изменения
зависимостей (`uv add ...`) или Dockerfile.

## Миграции

```bash
# создать миграцию: на маке, из папки сервиса (файл должен попасть в git)
cd users && uv run alembic revision --autogenerate -m "..."

# применить: из корня
docker compose exec users alembic upgrade head
```
