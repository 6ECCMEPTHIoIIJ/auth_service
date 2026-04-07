from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import engine, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(title="auth-service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
