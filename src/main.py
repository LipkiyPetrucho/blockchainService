from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import settings
from src.transactions.infura_client import router as info_by_infura
from src.transactions.router import router as transactions_router
from src.api.router import router as api_router

from src.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Print database configuration
    print(f"Connecting to database at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"Database name: {settings.POSTGRES_DB}, User: {settings.POSTGRES_USER}")
    yield
    print("Выключение")


app = FastAPI(title="Blockchain Transaction Service", lifespan=lifespan)

# Подключение роутов
app.include_router(transactions_router, tags=["Transactions"])
app.include_router(api_router, tags=["API"])
app.include_router(info_by_infura, tags=["TransactionsByHash"])


# Инициализация базы данных
@app.on_event("startup")
async def startup_event():
    await init_db()


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
