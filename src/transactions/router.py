from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db_session
from src.transactions.schemas import TransactionResponse
from src.transactions.service import get_transactions

router = APIRouter(
    prefix="/transactions",
)

load_dotenv()

INFURA_URL = settings.infura_url


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
        skip: int = 0,
        limit: int = 10,
        db: AsyncSession = Depends(get_db_session)
):
    max_limit = 20
    limit = min(limit, max_limit)
    return await get_transactions(db, skip, limit)


# @router.get("/{transaction_hash}", response_model=TransactionResponse)
# async def get_transaction(transaction_hash: str, db: AsyncSession = Depends(get_db)):
#     return await get_transaction_by_hash(db, transaction_hash)
