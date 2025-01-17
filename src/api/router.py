import requests
from fastapi import APIRouter, HTTPException

from src.api.utils import load_transactions_from_dump

import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
)

dump_base_url = "https://gz.blockchair.com/ethereum/transactions/"


@router.post("/load-transactions")
async def load_transactions():
    try:
        await load_transactions_from_dump(dump_base_url)
        return {"message": "Transactions loaded successfully"}
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Сервис недоступен. Проверьте подключение к сети или доступность ресурса."
        )
    except Exception as e:
        logger.error("Ошибка при загрузке транзакций", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))
