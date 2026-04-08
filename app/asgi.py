from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.config import settings
from app.db.session import engine, init_db
from app.routes import auth_router
from app.services.jwt import JwtService
from app.services.redis_refresh import RefreshStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    redis = Redis.from_url(settings.redis_url, decode_responses=False)
    app.state.redis = redis
    app.state.jwt = JwtService(
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        access_ttl_seconds=settings.access_token_ttl_seconds,
    )
    app.state.refresh_store = RefreshStore(redis)
    yield
    await redis.aclose()
    await engine.dispose()


app = FastAPI(title="auth-service", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
