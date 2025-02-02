from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    hash: str = Field(..., description="Хеш транзакции")
    sender: str = Field(..., description="Адрес отправителя")
    receiver: str = Field(..., description="Адрес получателя")
    value: float = Field(..., description="Сумма транзакции")
    gas_price: float = Field(..., description="Цена газа")
    gas_used: int = Field(..., description="Использованное количество газа")


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionCreate):
    class Config:
        from_attributes = True


class TransactionStatistics(BaseModel):
    total_transactions: int
    avg_gas_price: float
    avg_transaction_value: float
    total_value: float
