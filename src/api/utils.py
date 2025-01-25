# import asyncio
# import os
#
# import aiohttp
# import pandas as pd
# import gzip
#
# from sqlalchemy.dialects.postgresql import insert
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src.config import logger, DOWNLOAD_LOG_FILE
# from src.transactions.models import Transaction
# from src.database import async_session_maker
# from bs4 import BeautifulSoup
#
#
# # Функция для загрузки уже загруженных файлов из локального хранилища
# def get_downloaded_files():
#     if not os.path.exists(DOWNLOAD_LOG_FILE):
#         return set()
#     with open(DOWNLOAD_LOG_FILE, "r") as file:
#         return set(file.read().splitlines())
#
#
# # Функция для добавления нового файла в локальное хранилище
# def add_to_downloaded_files(file_name):
#     with open(DOWNLOAD_LOG_FILE, "a") as file:
#         file.write(file_name + "\n")
#
#
# async def load_transactions_from_dump(dump_base_url: str):
#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.get(dump_base_url) as response:
#                 response.raise_for_status()
#                 html_content = await response.text()
#         except aiohttp.ClientError as e:
#             logger.error("Ошибка соединения: проверьте доступность ресурса.")
#             raise e
#
#         # Разбор HTML для извлечения ссылок на файлы
#         soup = BeautifulSoup(html_content, 'html.parser')
#         file_list = [
#             a['href'] for a in soup.find_all('a', href=True)
#             if a['href'].endswith('.tsv.gz')
#         ]
#
#         logger.info("Список извлеченных файлов: %s... (и еще %d)",
#                     file_list[:3] + (['...'] if len(file_list) > 6 else []) + file_list[-3:],
#                     len(file_list) - 3 * 2)
#
#         # Сортируем файлы по дате в имени файла и берем последние 5
#         file_list.sort(reverse=True)
#         latest_files = file_list[:5]
#
#         downloaded_files = get_downloaded_files()
#
#         # Фильтруем файлы, которые еще не загружены
#         files_to_download = [
#             file_name for file_name in latest_files if file_name not in downloaded_files
#         ]
#
#         if not files_to_download:
#             logger.info("Все файлы уже были загружены.")
#             return
#
#         # Параллельная загрузка всех файлов
#         tasks = [
#             download_large_file_parallel(f"{dump_base_url}/{file_name}", "/save/files")
#             for file_name in files_to_download
#         ]
#         downloaded_files_paths = await asyncio.gather(*tasks)
#
#         # Обработка загруженных файлов
#         for file_name, downloaded_file_path in zip(files_to_download, downloaded_files_paths):
#             logger.info("Чтение данных из файла: %s", file_name)
#
#             # Чтение загруженного файла
#             with gzip.open(downloaded_file_path, 'rt') as f:
#                 df = pd.read_csv(f, sep='\t')
#
#             logger.debug("Колонки в DataFrame: %s", df.columns)
#             logger.info("Загрузка данных из файла: %s", file_name)
#             logger.debug("Предварительный просмотр данных:\n%s", pd.concat([df.head(3), df.tail(3)]))
#
#             required_columns = ['hash', 'sender', 'recipient', 'value', 'gas_price', 'gas_used']
#             missing_columns = [col for col in required_columns if col not in df.columns]
#             if missing_columns:
#                 logger.error("Отсутствуют следующие колонки в данных: %s", missing_columns)
#                 continue
#
#             logger.info("Все необходимые колонки присутствуют в файле: %s", file_name)
#
#             # Извлечение соответствующих данных из DataFrame и вставка в БД
#             async with async_session_maker() as db_session:
#                 await insert_transactions(db_session, df)
#
#                 # Добавление файла в список загруженных
#                 add_to_downloaded_files(file_name)
#
#
# async def insert_transactions(session: AsyncSession, df: pd.DataFrame):
#     transactions = [
#         {
#             "hash": row['hash'],
#             "sender": row['sender'],
#             "receiver": row['recipient'],
#             "value": float(row['value']),
#             "gas_price": float(row['gas_price']),
#             "gas_used": int(row['gas_used']),
#         }
#         for index, row in df.iterrows()
#     ]
#
#     stmt = insert(Transaction).values(transactions)
#     stmt = stmt.on_conflict_do_nothing(
#         index_elements=['hash', 'recipient']
#     )
#
#     await session.execute(stmt)
#     await session.commit()
#
#
# # Функция для загрузки больших файлов по частям:
# async def download_large_file_parallel(url, dest_folder, chunk_size=8192*8192):
#     if not os.path.exists(dest_folder):
#         os.makedirs(dest_folder)
#
#     file_name = os.path.basename(url)
#     dest_path = os.path.join(dest_folder, file_name)
#
#     async with aiohttp.ClientSession() as session:
#         # Получаем размер файла
#         async with session.head(url) as response:
#             response.raise_for_status()
#             file_size = int(response.headers.get('Content-Length', 0))
#
#         # Генерируем диапазоны для параллельной загрузки
#         ranges = [(i, min(i + chunk_size - 1, file_size - 1)) for i in range(0, file_size, chunk_size)]
#
#         async def download_chunk(start, end):
#             headers = {'Range': f'bytes={start}-{end}'}
#             async with session.get(url, headers=headers) as chunk_response:
#                 if chunk_response.status == 402:
#                     raise Exception(f"Payment required for file: {url}")
#                 chunk_response.raise_for_status()
#                 return await chunk_response.content.read()
#
#         tasks = [download_chunk(start, end) for start, end in ranges]
#
#         # Асинхронно скачиваем все части
#         chunks = await asyncio.gather(*tasks, return_exceptions=True)
#
#         # Собираем все части в один файл
#         with open(dest_path, 'wb') as f:
#             for chunk in chunks:
#                 if isinstance(chunk, Exception):
#                     logger.error("Ошибка при загрузке части файла: %s", chunk)
#                     continue  # Пропускаем эту часть и продолжаем обработку остальных
#                 f.write(chunk)
#
#     # Проверяем, что файл был полностью загружен
#     if os.path.getsize(dest_path) != file_size:
#         logger.error("Файл %s не был полностью загружен, попробуйте еще раз.", file_name)
#         return None
#
#     return dest_path
