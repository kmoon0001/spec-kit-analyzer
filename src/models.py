from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(Text)

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String, index=True)
    analysis_date = Column(DateTime, default=datetime.datetime.utcnow)
    compliance_score = Column(Integer)

    findings = relationship("Finding", back_populates="report")

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    rule_id = Column(String)
    risk = Column(String)
    personalized_tip = Column(Text)
    problematic_text = Column(Text)

    report = relationship("Report", back_populates="findings")
