

## Состав проекта

| Каталог | Назначение |
| --- | --- |
| [`ugc_service`](ugc_service/README.md) | FastAPI-сервис оценок, закладок, рецензий и голосов за рецензии. Использует MongoDB. |
| [`analytics_service`](analytics_service/README.md) | Flask-сервис, принимающий пользовательские события и публикующий их в Kafka. |
| [`research`](research/README.md) | Стенд и результаты сравнения MongoDB и PostgreSQL для сценариев чтения UGC. |
| [`elk`](elk/README.md) | Конфигурация централизованного сбора и просмотра логов в ELK. |
| [`sentry`](sentry/docker-compose.yml) | Docker Compose-конфигурация Sentry для локального мониторинга ошибок. |

