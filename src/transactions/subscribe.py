import asyncio
import json
from typing import Optional

from fastapi import WebSocket

from web3 import Web3
import websockets

from src.config import logger, settings
from src.transactions.infura_client import get_transaction_by_hash_infura_config

web3 = Web3(Web3.HTTPProvider())

MAX_RETRIES = 5


async def subscribe_pending_transactions(websocket: Optional[WebSocket] = None):
    """Подписка на события новых неподтверждённых транзакций"""
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            async with websockets.connect(str(settings.infura_url_ws)) as ws:
                logger.info("Подключение к WebSocket успешно.")
                # Подписываемся на события новых транзакций
                await ws.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newPendingTransactions"]
                }))
                subscription_response = await ws.recv()
                logger.info(f"Подписка активирована: {subscription_response}")

                # Обрабатываем новые события
                while True:
                    try:
                        # Ждём сообщения о новых транзакциях
                        message = await asyncio.wait_for(ws.recv(), timeout=15)
                        response = json.loads(message)

                        # Получаем хеш транзакции
                        tx_hash = response.get("params", {}).get("result")
                        if tx_hash:
                            logger.info(f"Получен новый хеш транзакции: {tx_hash}")
                            await get_transaction_by_hash_infura_config(tx_hash)
                    except asyncio.TimeoutError:
                        logger.warning("Таймаут при ожидании сообщений WebSocket. Продолжаем...")
                        continue
                    except Exception as e:
                        logger.error(f"Ошибка при обработке WebSocket: {e}")
                        break
        except Exception as e:
            logger.error(f"Ошибка WebSocket: {e}. Переподключение через 5 секунд...")
            retry_count += 1
            await asyncio.sleep(5)
    logger.error("Превышено максимальное количество попыток подключения.")
