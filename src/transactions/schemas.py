from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    hash: str = Field(..., description="Хеш транзакции, уникальный идентификатор, предоставляется клиентом")
    sender: str = Field(..., description="Адрес отправителя")
    receiver: str = Field(..., description="Адрес получателя")
    value: float = Field(..., description="Сумма транзакции")
    gas_price: float = Field(..., description="Цена газа")
    gas_used: int = Field(..., description="Использованное количество газа")


class TransactionResponse(TransactionCreate):
    # Наследуемся от TransactionCreate, так как структура ответа совпадает
    pass
