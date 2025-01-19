from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, int_pk


class Transaction(Base):
    id: Mapped[int_pk]
    # block_id: Mapped[int] = mapped_column(Integer())
    hash: Mapped[str] = mapped_column(String())
    sender: Mapped[str] = mapped_column(String())
    receiver: Mapped[str] = mapped_column(String())
    value: Mapped[float] = mapped_column(Float())
    gas_price: Mapped[float] = mapped_column(Float())
    gas_used: Mapped[int] = mapped_column(Integer())

    def __str__(self):
        return f"Transaction(hash={self.hash}, sender={self.sender}, receiver={self.receiver}, value={self.value})"

    def __repr__(self):
        return (f"<Transaction(hash={self.hash}, sender={self.sender}, "
                f"receiver={self.receiver}, value={self.value}, gas_price={self.gas_price}, gas_used={self.gas_used})>")
