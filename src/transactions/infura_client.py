from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from src.config import settings, logger
from src.database import get_db_session
from src.transactions.infura import infura_client
from src.transactions.schemas import TransactionBase, TransactionCreate
from src.transactions.service import create_transaction

load_dotenv()

INFURA_URL = settings.infura_url

router = APIRouter(
    prefix="/info_by_infura",
)


@router.get("/transaction_config/{tx_hash}")
async def get_transaction_by_hash_infura_config(tx_hash: str):
    """Обработка хеша транзакции: получение данных и запись в БД"""
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash

    # Запрашиваем информацию о транзакции через Infura API
    try:
        tx_data = await infura_client.api_call("eth_getTransactionByHash", [tx_hash])
        if not tx_data:
            logger.warning(f"Транзакция {tx_hash} не найдена.")
            return
        logger.info(f"Данные транзакции: {tx_data}")

        # Преобразуем данные в экземпляр модели TransactionCreate.
        tx_model = TransactionCreate(
            hash=tx_data.get("hash"),
            sender=tx_data.get("from"),
            receiver=tx_data.get("to"),
            value=int(tx_data.get("value", "0"), 16) if tx_data.get("value") else 0,
            gas_price=int(tx_data.get("gasPrice", "0"), 16) if tx_data.get("gasPrice") else 0,
            gas_used=int(tx_data.get("gas", "0"), 16) if tx_data.get("gas") else 0,
        )

        # Сохраняем транзакцию в базе данных
        async with get_db_session() as db:
            await create_transaction(db, tx_model)
        return tx_data

    except Exception as e:
        logger.error(f"Ошибка при обработке транзакции {tx_hash}: {e}")


@router.get("/block_number")
async def get_block_number():
    result = await infura_client.api_call("eth_blockNumber", [])
    if not result:
        raise HTTPException(status_code=404, detail="block not found")
    return {"block_number": int(result, 16)}


@router.get("/block_by_number")
async def get_block_by_number(blk_num: int, tx_flag: bool = False):
    hex_blk_num = hex(blk_num)
    result = await infura_client.api_call("eth_getBlockByNumber", [hex_blk_num, tx_flag])
    if not result:
        raise HTTPException(status_code=404, detail="block not found")
    return result


@router.get("/block_by_hash/{block_hash}")
async def get_block_by_hash(block_hash: str, block_flag: bool = False):
    if not block_hash.startswith("0x"):
        block_hash = "0x" + block_hash
    try:
        result = await infura_client.api_call("eth_getBlockByHash", [block_hash, block_flag])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Block not found")
    return result
