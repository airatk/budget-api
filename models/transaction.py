from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    String,
    Time
)
from sqlalchemy.orm import RelationshipProperty, relationship

from .utilities.base import BaseModel
from .utilities.callables import persist_enumeration_values
from .utilities.types import TransactionType


class Transaction(BaseModel):
    id: Column = Column(BigInteger, primary_key=True)

    account_id: Column = Column(BigInteger, ForeignKey("account.id", ondelete="CASCADE"), nullable=False)
    category_id: Column = Column(BigInteger, ForeignKey("category.id", ondelete="SET NULL"))

    account: RelationshipProperty = relationship("Account", back_populates="transactions")
    category: RelationshipProperty = relationship("Category", back_populates="transactions")

    type: Column = Column(Enum(TransactionType, values_callable=persist_enumeration_values), nullable=False)
    due_date: Column = Column(Date, nullable=False)
    due_time: Column = Column(Time, nullable=False)
    amount: Column = Column(Float, nullable=False)
    note: Column = Column(String, default="", nullable=False)

    def __repr__(self) -> str:
        return "{0.__class__.__name__}(id={0.id}, amount={0.amount})".format(self)