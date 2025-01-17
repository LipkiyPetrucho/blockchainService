from dotenv import load_dotenv
import requests
from fastapi import HTTPException, APIRouter

from src.config import settings

load_dotenv()

INFURA_URL = settings.infura_url

router = APIRouter(
    prefix="/transaction_by_hash_infura",
)


@router.get("/transaction/{tx_hash}")
async def get_transaction_by_hash_infura(tx_hash: str):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByHash",
        "params": [tx_hash],
        "id": 1
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(INFURA_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error connecting to Ethereum node")

    result = response.json().get("result")
    if not result:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return result
