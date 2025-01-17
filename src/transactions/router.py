from typing import Annotated

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.transactions.schemas import TransactionCreate, TransactionResponse
from src.transactions.service import save_transaction, get_transactions, get_transaction_by_hash

from src.repository import TransactionRepository

router = APIRouter(
    prefix="/transactions",
)

load_dotenv()

INFURA_URL = settings.infura_url


@router.post("", response_model=TransactionResponse)
async def create_transaction(
        data: Annotated[TransactionCreate, Depends()]
):
    await TransactionRepository.add_one(data)
    return await save_transaction(data)



#
# @router.get("", response_model=list[TransactionResponse])
# async def list_transactions(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
#     return await get_transactions(db, skip, limit)
#
#
# @router.get("/{transaction_hash}", response_model=TransactionResponse)
# async def get_transaction(transaction_hash: str, db: AsyncSession = Depends(get_db)):
#     return await get_transaction_by_hash(db, transaction_hash)
