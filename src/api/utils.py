import aiohttp
import pandas as pd
import gzip
from sqlalchemy.ext.asyncio import AsyncSession
from src.transactions.models import Transaction
from src.database import async_session_maker
from io import BytesIO
from bs4 import BeautifulSoup

import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_transactions_from_dump(dump_base_url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(dump_base_url) as response:
                response.raise_for_status()
                html_content = await response.text()
        except aiohttp.ClientError as e:
            logger.error("Ошибка соединения: проверьте доступность ресурса.")
            raise e

        # Разбор HTML для извлечения ссылок на файлы
        soup = BeautifulSoup(html_content, 'html.parser')
        file_list = [
            a['href'] for a in soup.find_all('a', href=True)
            if a['href'].endswith('.tsv.gz')
        ]

        logger.info("Список извлеченных файлов: %s... (и еще %d)",
                    file_list[:3] + ['...'] + file_list[-3:],
                    len(file_list) - 3 * 2)

        for file_name in file_list:
            dump_url = f"{dump_base_url}/{file_name}"
            logger.info("Загрузка дампа из URL: %s", dump_url)

            try:
                async with session.get(dump_url) as file_response:
                    file_response.raise_for_status()
                    content = await file_response.read()
            except aiohttp.ClientError as e:
                logger.error("Ошибка загрузки файла: %s", e)
                continue

            # Считывание gzipped TSV-файла в DataFrame
            with gzip.open(BytesIO(content), 'rt') as f:
                df = pd.read_csv(f, sep='\t')

            logger.debug("Колонки в DataFrame: %s", df.columns)
            logger.info("Загрузка данных из файла: %s", dump_url)
            logger.debug("Предварительный просмотр данных:\n%s", df.head())

            required_columns = ['hash', 'sender', 'recipient', 'value', 'gas_price', 'gas_used']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error("Отсутствуют следующие колонки в данных: %s", missing_columns)
                continue

            logger.info("Все необходимые колонки присутствуют в файле: %s", file_name)

            # Извлечение соответствующих данных из DataFrame и вставка в БД
            async with async_session_maker() as db_session:
                await insert_transactions(db_session, df)


async def insert_transactions(session: AsyncSession, df: pd.DataFrame):
    transactions = []
    for index, row in df.iterrows():
        transaction = Transaction(
            hash=row['hash'],
            sender=row['sender'],
            receiver=row['recipient'],
            value=float(row['value']),
            gas_price=float(row['gas_price']),
            gas_used=int(row['gas_used'])
        )
        transactions.append(transaction)
    session.add_all(transactions)
    await session.commit()
