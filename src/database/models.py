"""
Database models for the Therapy Compliance Analyzer.

This module defines SQLAlchemy ORM models for users, compliance rubrics,
analysis reports, and findings using modern SQLAlchemy 2.0 syntax.
"""

import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    license_key: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class ComplianceRubric(Base):
    """Compliance rubric model for storing regulatory guidelines and rules."""
    
    __tablename__ = "rubrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    discipline: Mapped[str] = mapped_column(String, index=True)  # PT, OT, SLP
    regulation: Mapped[str] = mapped_column(Text)
    common_pitfalls: Mapped[str] = mapped_column(Text)
    best_practice: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class AnalysisReport(Base):
    """Analysis report model for storing document analysis results."""
    
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_name: Mapped[str] = mapped_column(String, index=True)
    analysis_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, index=True
    )
    compliance_score: Mapped[float] = mapped_column(Float, index=True)
    document_type: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    analysis_result: Mapped[dict] = mapped_column(JSON)
    document_embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    findings: Mapped[List["Finding"]] = relationship(
        "Finding", back_populates="report", cascade="all, delete-orphan"
    )


class Finding(Base):
    """Finding model for storing individual compliance issues found in documents."""
    
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("reports.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String, index=True)
    risk: Mapped[str] = mapped_column(String, index=True)  # High, Medium, Low
    personalized_tip: Mapped[str] = mapped_column(Text)
    problematic_text: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    report: Mapped["AnalysisReport"] = relationship("AnalysisReport", back_populates="findings")


# Backward compatibility aliases
Rubric = ComplianceRubric
Report = AnalysisReport
