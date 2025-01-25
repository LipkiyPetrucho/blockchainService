import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from src.config import settings

# URL страницы с ссылками на файлы
INFURA_URL = settings.infura_url

# Директория для сохранения загруженных файлов
download_dir = 'downloads'
os.makedirs(download_dir, exist_ok=True)
print(f'Директория для загрузки: {download_dir}')


def fetch_links(page_url):
    """Извлекает все ссылки на файлы с указанной веб-страницы."""
    print(f'Получение ссылок с {page_url}')
    response = requests.get(page_url)
    response.raise_for_status()  # Проверка успешности запроса
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.tsv.gz')]
    print(f'Найдено {len(links)} ссылок на файлы.')
    return links


def download_file(file_url):
    """Скачивает файл по указанному URL и сохраняет его в заданную директорию."""
    local_filename = os.path.join(download_dir, os.path.basename(file_url))
    print(f'Начало загрузки: {file_url}')
    try:
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f'Успешно загружен: {local_filename}')
    except requests.exceptions.RequestException as e:
        print(f'Ошибка при загрузке {file_url}: {e}')


def main():
    # Получаем список всех ссылок на файлы
    file_links = fetch_links(INFURA_URL)
    print(f'Начало загрузки {len(file_links)} файлов...')

    # Скачиваем файлы с использованием многопоточности
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_file, file_links)

    print('Загрузка завершена.')


if __name__ == '__main__':
    main()
