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


async def get_transactions(db: AsyncSession, skip: int, limit: int):
    try:
        logger.info(f"Fetching transactions with skip={skip}, limit={limit}")
        result = await db.execute(select(Transaction).offset(skip).limit(limit))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return []


async def get_transaction_by_hash(db: AsyncSession, transaction_hash: str):
    result = await db.execute(select(Transaction).where(Transaction.hash == transaction_hash))
    return result.scalar_one_or_none()
