from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, Column, DateTime, Integer, String, Text,
                        create_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    """Job listing database model."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String)
    company: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String)
    location: Mapped[Optional[str]] = mapped_column(String)
    scraped_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


def init_db():
    """Initialize SQLite database and create tables."""
    engine = create_engine("sqlite:///jobs.db", echo=True)
    Base.metadata.create_all(engine)
    return engine
