from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    LargeBinary,
    Float,
)
from sqlalchemy.orm import relationship
from .database import Base
import datetime
from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    license_key = Column(String, unique=True, index=True, nullable=True)


class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    regulation = Column(Text, nullable=False)
    common_pitfalls = Column(Text, nullable=False)
    best_practice = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=True)


class RubricCreate(BaseModel):
    name: str
    regulation: str
    common_pitfalls: str
    best_practice: str
    category: str | None = None


class RubricSchema(RubricCreate):
    id: int

    class Config:
        from_attributes = True


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String, index=True)
    analysis_date = Column(DateTime, default=datetime.datetime.utcnow, index=True)  # Index for date queries
    compliance_score = Column(Float, index=True)  # Index for score filtering
    document_type = Column(String, index=True, nullable=True)  # Index for document type filtering
    analysis_result = Column(JSON)
    document_embedding = Column(
        LargeBinary, nullable=True
    )  # New column for semantic caching

    findings = relationship(
        "Finding", back_populates="report", cascade="all, delete-orphan"
    )


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True)  # Index for report lookups
    rule_id = Column(String, index=True)  # Index for rule-based queries
    risk = Column(String, index=True)  # Index for risk level filtering
    personalized_tip = Column(Text)
    problematic_text = Column(Text)

    report = relationship("Report", back_populates="findings")
