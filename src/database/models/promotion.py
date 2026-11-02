from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base
from src.database.models.product import Product


class Promotion(Base):
    """Store promotions and discounts."""

    __tablename__ = "promotions"

    promotion_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"), nullable=False
    )
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, default=1)

    product: Mapped["Product"] = relationship(back_populates="promotions")
