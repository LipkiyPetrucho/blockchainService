import asyncio
import gzip
import os
from io import BytesIO
from urllib.parse import urljoin

import aiofiles
import aiohttp
import pandas
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import logger, DOWNLOAD_LOG_FILE
from src.database import async_session_maker
from src.transactions.models import Transaction


# Функция для загрузки уже загруженных файлов из локального хранилища
async def get_downloaded_files():
    if not os.path.exists(DOWNLOAD_LOG_FILE):
        return set()
    async with aiofiles.open(DOWNLOAD_LOG_FILE, "r") as file:
        content = await file.read()
        return set(content.splitlines())


async def download_file_in_chunks(session, url, chunk_size=10 * 1024 * 1024):  # 10 MB
    """Скачивает файл по частям, используя заголовок Range."""
    downloaded_content = BytesIO()
    headers = {}
    total_size = 0

    while True:
        headers['Range'] = f"bytes={total_size}-{total_size + chunk_size - 1}"
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                chunk = await response.read()
                if not chunk:
                    break  # Все части загружены
                downloaded_content.write(chunk)
                total_size += len(chunk)
        except aiohttp.ClientError as e:
            logger.error("Ошибка загрузки части файла: %s", e)
            break
        except asyncio.TimeoutError:
            logger.error("Превышен таймаут при загрузке части файла: %s", url)
            break

    return downloaded_content


async def load_transactions_from_dump(dump_base_url: str):
    timeout = aiohttp.ClientTimeout(total=300, connect=10, sock_read=120, sock_connect=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
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

        # Сортируем файлы по дате в имени файла и берем последние 5
        file_list.sort(reverse=True)
        latest_files = file_list[:5]

        downloaded_files = get_downloaded_files()

        # Фильтруем файлы, которые еще не загружены
        files_to_download = [
            file_name for file_name in latest_files if file_name not in downloaded_files
        ]

        if not files_to_download:
            logger.info("Все файлы уже были загружены.")
            return

        for file_name in files_to_download:
            dump_url = urljoin(dump_base_url, file_name)
            logger.info("Загрузка дампа из URL: %s", dump_url)

            try:
                downloaded_content = await download_file_in_chunks(session, dump_url)
                if downloaded_content is None:
                    logger.error("Не удалось загрузить файл по частям: %s", dump_url)
                    continue
            except Exception as e:
                logger.error("Ошибка загрузки файла: %s", e)
                continue

                # Считывание gzipped TSV-файла в DataFrame
            try:
                downloaded_content.seek(0)
                with gzip.open(downloaded_content, 'rt') as f:
                    df = pandas.read_csv(f, sep='\t')
            except Exception as e:
                logger.error("Ошибка при чтении TSV-файла: %s", e)
                continue

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


async def insert_transactions(session: AsyncSession, df: pandas.DataFrame):
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
