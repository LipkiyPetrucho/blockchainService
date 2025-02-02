import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket

from src.config import settings, logger
from src.transactions.infura_client import router as info_by_infura
from src.transactions.router import router as transactions_router
from src.api.router import router as api_router

from src.database import init_db
from src.transactions.subscribe import subscribe_pending_transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Connecting to database at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"Database name: {settings.POSTGRES_DB}, User: {settings.POSTGRES_USER}")
    try:
        await init_db()
        logger.info("База данных инициализирована.")
        asyncio.create_task(subscribe_pending_transactions())
        logger.info("Запущена подписка на WebSocket.")
    except Exception as e:
        logger.error(f"Ошибка во время старта приложения: {e}")
    yield
    print("Выключение")


app = FastAPI(title="Blockchain Transaction Service", lifespan=lifespan)

# Подключение роутов
app.include_router(transactions_router, tags=["Transactions"])
app.include_router(api_router, tags=["API"])
app.include_router(info_by_infura, tags=["TransactionsByHash"])


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Запускаем задачу для получения данных с внешнего API
    await subscribe_pending_transactions(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
