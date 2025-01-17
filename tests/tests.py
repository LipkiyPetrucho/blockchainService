import pytest
import httpx
import pandas as pd
import gzip
from unittest.mock import patch

from src.database import async_session_maker

from src.api.utils import load_transactions_from_dump, insert_transactions


@pytest.fixture
async def mock_http_response():
    def mock_get(*args, **kwargs):
        if args[0].endswith('20150730.tsv.gz'):
            content = b"hash\tsender\treceiver\tvalue\tgas_price\tgas_used\n"
            content += b"0x1\t0xsender1\t0xreceiver1\t10\t20\t21000\n"
            return httpx.Response(200, content=gzip.compress(content))
        elif args[0] == "https://gz.blockchair.com/ethereum/":
            html_content = "File1"
            return httpx.Response(200, content=html_content)
        return httpx.Response(404)

    with patch('httpx.get', new=mock_get):
        yield


@pytest.mark.asyncio
async def test_load_transactions_from_dump(mock_http_response):
    dump_base_url = "https://gz.blockchair.com/ethereum/"
    await load_transactions_from_dump(dump_base_url)

    # Check if data was inserted into the database
    async with async_session_maker() as session:
        result = await session.execute("SELECT * FROM transactions")
        transactions = result.fetchall()
        assert len(transactions) == 1
        assert transactions[0].hash == '0x1'
        assert transactions[0].sender == '0xsender1'
        assert transactions[0].receiver == '0xreceiver1'
        assert transactions[0].value == 10
        assert transactions[0].gas_price == 20
        assert transactions[0].gas_used == 21000


@pytest.mark.asyncio
async def test_insert_transactions():
    df = pd.DataFrame({
        'hash': ['0x1'],
        'sender': ['0xsender1'],
        'receiver': ['0xreceiver1'],
        'value': [10],
        'gas_price': [20],
        'gas_used': [21000]
    })
    async with async_session_maker() as session:
        await insert_transactions(session, df)
        result = await session.execute("SELECT * FROM transactions")
        transactions = result.fetchall()
        assert len(transactions) == 1
        assert transactions[0].hash == '0x1'
        assert transactions[0].sender == '0xsender1'
        assert transactions[0].receiver == '0xreceiver1'
        assert transactions[0].value == 10
        assert transactions[0].gas_price == 20
        assert transactions[0].gas_used == 21000
