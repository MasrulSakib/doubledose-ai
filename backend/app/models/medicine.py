
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime
from sqlalchemy import DateTime

class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    brand_name: Mapped[str] = mapped_column(
        String(200),
        index=True,
    )
    generic_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )
    dosage_form: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    rxnorm_rxcui: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )    

    ingredients: Mapped[list["MedicineIngredient"]] = relationship(
        back_populates="medicine",
        cascade="all, delete-orphan",
    )


class ActiveIngredient(Base):
    __tablename__ = "active_ingredients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
    )

    rxnorm_rxcui: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )

    medicines: Mapped[list["MedicineIngredient"]] = relationship(
        back_populates="ingredient",
    )


class MedicineIngredient(Base):
    __tablename__ = "medicine_ingredients"

    __table_args__ = (
        UniqueConstraint(
            "medicine_id",
            "ingredient_id",
            name="uq_medicine_ingredient",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("active_ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    unit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    source_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    source_record_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    medicine: Mapped["Medicine"] = relationship(
        back_populates="ingredients",
    )
    ingredient: Mapped["ActiveIngredient"] = relationship(
        back_populates="medicines",
    )
