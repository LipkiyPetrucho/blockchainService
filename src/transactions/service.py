from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config import logger
from src.transactions.models import Transaction
from src.transactions.schemas import TransactionCreate, TransactionResponse


async def save_transaction(db: AsyncSession, data: TransactionCreate) -> TransactionResponse:
    transaction = Transaction(**data.dict())
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


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
):
    # Формируем базовый запрос
    query = select(Transaction)

    # Добавляем фильтры
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

    # Добавляем пагинацию
    query = query.offset(skip).limit(limit)

    # Выполняем запрос
    result = await db.execute(query)
    return result.scalars().all()


async def get_transaction_by_hash(db: AsyncSession, transaction_hash: str):
    result = await db.execute(select(Transaction).where(Transaction.hash == transaction_hash))
    return result.scalar_one_or_none()
