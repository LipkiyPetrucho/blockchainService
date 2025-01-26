from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db_session
from src.transactions.schemas import TransactionResponse
from src.transactions.service import get_transactions, get_transaction_statistics, get_transaction_by_hash

router = APIRouter(
    prefix="/transactions",
)

load_dotenv()

INFURA_URL = settings.infura_url


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(10, ge=1, le=100, description="Сколько записей вернуть"),
    hash: str | None = Query(None, description="Фильтр по хешу транзакции"),
    sender: str | None = Query(None, description="Фильтр по отправителю"),
    receiver: str | None = Query(None, description="Фильтр по получателю"),
    value_min: float | None = Query(None, description="Минимальная сумма транзакции"),
    value_max: float | None = Query(None, description="Максимальная сумма транзакции"),
    gas_price_min: float | None = Query(None, description="Минимальная цена газа"),
    gas_price_max: float | None = Query(None, description="Максимальная цена газа"),
    db: AsyncSession = Depends(get_db_session),
):
    transactions = await get_transactions(
        db=db,
        skip=skip,
        limit=limit,
        hash=hash,
        sender=sender,
        receiver=receiver,
        value_min=value_min,
        value_max=value_max,
        gas_price_min=gas_price_min,
        gas_price_max=gas_price_max,
    )
    return transactions


@router.get("/statistics", summary="Получить статистику по транзакциям")
async def get_statistics(db: AsyncSession = Depends(get_db_session)):
    """
        Возвращает статистику по транзакциям, включая:
        - Общее количество транзакций
        - Среднюю стоимость газа
        - Среднюю сумму транзакции
        - Общую сумму всех транзакций
        """
    stats = await get_transaction_statistics(db)
    return stats


@router.get("/{transaction_hash}", response_model=TransactionResponse, summary="Получить транзакцию по хэшу")
async def get_transaction(transaction_hash: str, db: AsyncSession = Depends(get_db_session)):
    """
        Получить информацию о транзакции по её хэшу.

        :param transaction_hash: Хэш транзакции.
        :param db: Сессия базы данных.
        :return: Объект TransactionResponse.
        """
    transaction = await get_transaction_by_hash(db, transaction_hash)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
