import aiohttp
from fastapi import HTTPException

from src.api.utils import logger
from src.config import settings


class INFURA:
    def __init__(self, project_id, network='mainnet'):
        self.project_id = project_id
        self.url = f'https://{network}.infura.io/v3/{self.project_id}'

    async def api_call(self, method, params: list):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        headers = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=payload, headers=headers) as response:
                logger.info("Загрузка данных с infura: %s", await response.json())

                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Error connecting to Ethereum node")

                return (await response.json()).get("result")


# Инициализация клиента Infura с полученным ключом
infura_client = INFURA(settings.infura_key)
