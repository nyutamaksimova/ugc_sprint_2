from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from src.api.v1.ratings import router as ratings_router
from src.api.v1.ugc import router as ugc_router
from src.db.mongo import ensure_indexes
from src.core.sentry import init_sentry


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.core.config import settings

    client = AsyncIOMotorClient(settings.mongo_uri)
    app.state.mongo_client = client
    app.state.database = client[settings.mongo_database]
    await ensure_indexes(app.state.database)
    yield
    client.close()


def create_app() -> FastAPI:
    from src.core.config import settings

    init_sentry(dsn=settings.sentry_dsn, environment=settings.sentry_environment)
    app = FastAPI(title="UGC service", version="1.0.0", docs_url="/api/openapi", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(ratings_router, prefix="/api/v1")
    app.include_router(ugc_router, prefix="/api/v1")

    return app


app = create_app()
