from sqlalchemy import select

from src.database import async_session_maker
from src.transactions.models import Transaction


class TransactionRepository:
    @classmethod
    async def add_one(cls, data: Transaction):
        async with async_session_maker() as session:
            transaction_dict = data.model_dump()
            transaction = Transaction(**transaction_dict)
            session.add(transaction)
            await session.flush()
            await session.commit()
            return transaction.hash

    @classmethod
    async def find_all(cls):
        async with async_session_maker() as session:
            query = select(Transaction)
            result = await session.execute(query)
            transaction_models = result.scalars().all()
            return transaction_models
