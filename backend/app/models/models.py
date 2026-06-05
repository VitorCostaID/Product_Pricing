"""
Database models.

Table relationships:
  User ──< Search ──< Result
  Result ──< PriceSnapshot   (for historical tracking / ML later)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(60), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    searches: Mapped[list["Search"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Search(Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    query: Mapped[str] = mapped_column(String(500), nullable=False)
    # Comma-separated marketplace names stored as string for simplicity.
    # Can be migrated to a proper ARRAY column later.
    marketplaces: Mapped[str] = mapped_column(String(500), nullable=False)
    max_results: Mapped[int] = mapped_column(Integer, default=20)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="searches")
    results: Mapped[list["Result"]] = relationship(back_populates="search", cascade="all, delete-orphan")

    @property
    def marketplace_list(self) -> list[str]:
        return [m.strip() for m in self.marketplaces.split(",") if m.strip()]

    def __repr__(self) -> str:
        return f"<Search id={self.id} query={self.query!r}>"


class Result(Base):
    """One scraped product item inside a Search."""
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True)

    marketplace: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="Unknown")
    link: Mapped[str] = mapped_column(Text, default="#")
    price_raw: Mapped[Optional[str]] = mapped_column(String(200))   # original string from scraper
    price_brl: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))  # parsed float for analytics
    rating: Mapped[Optional[str]] = mapped_column(String(50))
    condition: Mapped[str] = mapped_column(String(50), default="New")
    shipping: Mapped[str] = mapped_column(String(200), default="Not specified")
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    search: Mapped["Search"] = relationship(back_populates="results")
    snapshots: Mapped[list["PriceSnapshot"]] = relationship(back_populates="result", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Result id={self.id} title={self.title!r} price={self.price_brl}>"


class PriceSnapshot(Base):
    """
    Historical price record per result.
    Populated each time the same product is seen in a new search.
    This table will feed the ML price-trend model later.
    """
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("results.id", ondelete="CASCADE"), nullable=False, index=True)
    price_brl: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    marketplace: Mapped[str] = mapped_column(String(100), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    result: Mapped["Result"] = relationship(back_populates="snapshots")