import requests
import json

from dotenv import load_dotenv

from src.config import settings

load_dotenv()

INFURA_URL = settings.infura_url

payload = {
  "jsonrpc": "2.0",
  "method": "eth_blockNumber",
  "params": [],
  "id": 1
}

headers = {'content-type': 'application/json'}

response = requests.post(INFURA_URL, data=json.dumps(payload), headers=headers).json()

print(response)