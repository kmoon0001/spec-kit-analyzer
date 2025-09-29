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
    role = Column(String, default="therapist", index=True)  # New role field
    license_key = Column(String, unique=True, index=True, nullable=True)

    reviews_as_reviewer = relationship("Review", foreign_keys="[Review.reviewer_id]", back_populates="reviewer")
    reviews_as_author = relationship("Review", foreign_keys="[Review.author_id]", back_populates="author")
    comments = relationship("Comment", back_populates="commenter")


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
    review = relationship("Review", uselist=False, back_populates="report", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), index=True)
    rule_id = Column(String, index=True)
    risk = Column(String, index=True)
    personalized_tip = Column(Text)
    problematic_text = Column(Text)

    report = relationship("Report", back_populates="findings")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, unique=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    report = relationship("Report", back_populates="review")
    author = relationship("User", foreign_keys=[author_id], back_populates="reviews_as_author")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_as_reviewer")
    comments = relationship("Comment", back_populates="review", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)
    commenter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review = relationship("Review", back_populates="comments")
    commenter = relationship("User", back_populates="comments")
