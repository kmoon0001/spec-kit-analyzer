import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Text,
    ForeignKey,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from src.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    license_key = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reports = relationship("AnalysisReport", back_populates="owner")


class ComplianceRubric(Base):
    __tablename__ = "compliance_rubrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    rules = Column(JSON) # Storing rules as a JSON blob for simplicity
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String, index=True)
    compliance_score = Column(Float, nullable=False)
    summary = Column(Text)
    findings = Column(JSON) # Detailed findings from the AI analysis
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="reports")

    rubric_id = Column(Integer, ForeignKey("compliance_rubrics.id"))
    rubric = relationship("ComplianceRubric")