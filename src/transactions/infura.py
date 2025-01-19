import requests
from fastapi import HTTPException

from src.api.utils import logger
from src.config import settings


class INFURA:
    def __init__(self, project_id, network='mainnet'):
        self.project_id = project_id
        self.url = f'https://{network}.infura.io/v3/{self.project_id}'

    def api_call(self, method, params: list):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url, json=payload, headers=headers)

        logger.info("Загрузка данных с infura: %s", response.json())

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error connecting to Ethereum node")

        return response.json().get("result")


infura_client = INFURA(settings.infura_key)
