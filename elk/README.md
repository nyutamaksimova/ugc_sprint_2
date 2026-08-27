# ELK: централизованные логи сервисов

Стек получает Docker stdout/stderr всех запущенных контейнеров через Filebeat,
нормализует их в Logstash и сохраняет в Elasticsearch.

## Запуск

```powershell
cd elk
docker compose up -d
```

Kibana: `http://localhost:5601`. Elasticsearch: `http://localhost:9200`.
