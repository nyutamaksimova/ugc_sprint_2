# Analytics service

Flask-сервис принимает действия авторизованных пользователей и публикует их в Kafka.

## Запуск

```powershell
Copy-Item .env.example .env
docker compose up --build
```

API доступен на `http://localhost:8001`.

## API

- `GET /health`
- `POST /api/v1/events` — одно событие
- `POST /api/v1/events/batch` — от 1 до 100 событий


Поддерживаемые Kafka-топики: `click-events`, `page-view-events`, `video-events`, `search-events`.
При `503` клиент повторяет тот же запрос с тем же `event_id`. Длительность страницы вычисляет Kafka-потребитель по паре `page_opened` и `page_closed` с одинаковым `session_id`.
