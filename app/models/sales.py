# app/models/sales.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Date

class Base(DeclarativeBase):
    pass

class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    mpesa_transaction_id: Mapped[str | None] = mapped_column(String, nullable=True)
