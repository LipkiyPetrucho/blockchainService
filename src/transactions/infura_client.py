from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter
from src.config import settings
from src.transactions.infura import infura_client

load_dotenv()

INFURA_URL = settings.infura_url

router = APIRouter(
    prefix="/transaction_by_hash_infura",
)


@router.get("/transaction_config/{tx_hash}")
async def get_transaction_by_hash_infura_config(tx_hash: str):
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash

    result = infura_client.api_call("eth_getTransactionByHash", [tx_hash])
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result


@router.get("/block_number")
async def get_block_number():
    result = infura_client.api_call("eth_blockNumber", [])
    if not result:
        raise HTTPException(status_code=404, detail="block not found")
    return {"block_number": int(result, 16)}


@router.get("/block_by_number")
async def get_block_by_number(blk_num: int, tx_flag: bool = False):
    hex_blk_num = hex(blk_num)
    result = infura_client.api_call("eth_getBlockByNumber", [hex_blk_num, tx_flag])
    if not result:
        raise HTTPException(status_code=404, detail="block not found")
    return result


@router.get("/block_by_hash/{block_hash}")
async def get_block_by_hash(block_hash: str, block_flag: bool = False):
    if not block_hash.startswith("0x"):
        block_hash = "0x" + block_hash
    try:
        result = infura_client.api_call("eth_getBlockByHash", [block_hash, block_flag])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Block not found")
    return result
