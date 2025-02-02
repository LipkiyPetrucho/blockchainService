from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config import logger
from src.transactions import models, schemas
# from src.config import logger TODO: need to add logging
from src.transactions.models import Transaction
from src.transactions.schemas import TransactionCreate, TransactionResponse


async def create_transaction(db: AsyncSession, tx_data: TransactionCreate):
    """Создание транзакции на основе данных Infura"""
    try:
        # Проверяем, существует ли транзакция с таким хешем
        existing_transaction = await db.execute(
            select(Transaction).where(Transaction.hash == tx_data.hash)
        )
        existing_transaction = existing_transaction.scalars().first()
        if existing_transaction:
            logger.warning(f"Транзакция с хешем {tx_data.hash} уже существует в базе данных.")
            return existing_transaction  # Возвращаем существующую транзакцию

        transaction = Transaction(
            hash=tx_data.hash,
            sender=tx_data.sender,
            receiver=tx_data.receiver,
            value=tx_data.value,
            gas_price=tx_data.gas_price,
            gas_used=tx_data.gas_used,
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction
    except Exception as e:
        await db.rollback()
        raise e


async def get_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    hash: str | None = None,
    sender: str | None = None,
    receiver: str | None = None,
    value_min: float | None = None,
    value_max: float | None = None,
    gas_price_min: float | None = None,
    gas_price_max: float | None = None,
) -> List[models.Transaction]:

    query = select(Transaction)

    # фильтры
    filters = []
    if hash:
        filters.append(Transaction.hash == hash)
    if sender:
        filters.append(Transaction.sender == sender)
    if receiver:
        filters.append(Transaction.receiver == receiver)
    if value_min is not None:
        filters.append(Transaction.value >= value_min)
    if value_max is not None:
        filters.append(Transaction.value <= value_max)
    if gas_price_min is not None:
        filters.append(Transaction.gas_price >= gas_price_min)
    if gas_price_max is not None:
        filters.append(Transaction.gas_price <= gas_price_max)

    if filters:
        query = query.where(and_(*filters))

    # пагинация
    query = query.offset(skip).limit(limit)

    # запрос
    result = await db.execute(query)
    return result.scalars().all()


async def get_transaction_statistics(db: AsyncSession) -> schemas.TransactionStatistics:
    query = select(
        func.count(Transaction.id).label("total_transactions"),
        func.avg(Transaction.gas_price).label("avg_gas_price"),
        func.avg(Transaction.value).label("avg_transaction_value"),
        func.sum(Transaction.value).label("total_value"),
    )

    result = await db.execute(query)
    stats = result.one()
    return {
        "total_transactions": stats.total_transactions,
        "avg_gas_price": stats.avg_gas_price,
        "avg_transaction_value": stats.avg_transaction_value,
        "total_value": stats.total_value,
    }


async def get_transaction_by_hash(db: AsyncSession, tx_hash: str) -> Optional[models.Transaction]:
    """
        Получить информацию о транзакции по её хэшу.

        :param db: Сессия базы данных.
        :param tx_hash: Хэш транзакции.
        :return: Объект Transaction или None, если не найдено.
        """
    try:
        result = await db.execute(select(Transaction).where(Transaction.hash == tx_hash))
        transaction = result.scalar_one_or_none()
        return transaction
    except NoResultFound:
        return None
