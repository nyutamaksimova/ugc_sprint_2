# UGC API

FastAPI-сервис пользовательского контента: оценки, закладки, рецензии и
голоса за рецензии. Исследование MongoDB/PostgreSQL с замерами расположено в
[research/README.md](../research/README.md).

## Запуск

```powershell
cd ugc_service
Copy-Item .env.example .env
# В .env задайте JWT_SECRET, совпадающий с сервисом авторизации.
docker compose up --build
```

API: `http://localhost:8002`; OpenAPI: `http://localhost:8002/api/openapi`.
Все маршруты кроме `/health` требуют `Authorization: Bearer <JWT>`.
MongoDB API-сервиса доступна для локальной отладки на `localhost:27018`;
порт `27017` остаётся за исследовательским стендом.

| Ресурс | Маршруты |
| --- | --- |
| Оценки | `PUT/DELETE /api/v1/films/{film_id}/ratings/me`, `GET /api/v1/films/{film_id}/ratings/summary` |
| Закладки | `PUT/DELETE /api/v1/users/me/bookmarks/{film_id}`, `GET /api/v1/users/me/bookmarks` |
| Рецензии | `POST/GET /api/v1/films/{film_id}/reviews`, `PATCH/DELETE /api/v1/reviews/{review_id}` |
| Голоса | `PUT/DELETE /api/v1/reviews/{review_id}/votes/me` |
