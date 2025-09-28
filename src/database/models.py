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
    content = Column(Text, nullable=False)
    category = Column(String, index=True, nullable=True)


class RubricCreate(BaseModel):
    name: str
    content: str
    category: str | None = None


class RubricSchema(RubricCreate):
    id: int

    class Config:
        from_attributes = True


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String, index=True)
    analysis_date = Column(DateTime, default=datetime.datetime.utcnow)
    compliance_score = Column(Float)  # Stored as float
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
    report_id = Column(Integer, ForeignKey("reports.id"))
    rule_id = Column(String)
    risk = Column(String)
    personalized_tip = Column(Text)
    problematic_text = Column(Text)

    report = relationship("Report", back_populates="findings")
