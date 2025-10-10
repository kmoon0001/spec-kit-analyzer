"""
Database models for the Therapy Compliance Analyzer.

This module defines SQLAlchemy ORM models for users, compliance rubrics,
analysis reports, and findings using modern SQLAlchemy 2.0 syntax.
"""

import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
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
    license_key: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Habit tracking relationships
    habit_goals: Mapped[list["HabitGoal"]] = relationship(
        "HabitGoal", back_populates="user", cascade="all, delete-orphan"
    )
    habit_achievements: Mapped[list["HabitAchievement"]] = relationship(
        "HabitAchievement", back_populates="user", cascade="all, delete-orphan"
    )
    habit_progress_snapshots: Mapped[list["HabitProgressSnapshot"]] = relationship(
        "HabitProgressSnapshot", back_populates="user", cascade="all, delete-orphan"
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
    category: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
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
    document_type: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )
    discipline: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    analysis_result: Mapped[dict] = mapped_column(JSON)
    document_embedding: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )

    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="report", cascade="all, delete-orphan"
    )


class Finding(Base):
    """Finding model for storing individual compliance issues found in documents."""

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reports.id"), index=True
    )
    rule_id: Mapped[str] = mapped_column(String, index=True)
    risk: Mapped[str] = mapped_column(String, index=True)  # High, Medium, Low
    personalized_tip: Mapped[str] = mapped_column(Text)
    problematic_text: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    report: Mapped["AnalysisReport"] = relationship(
        "AnalysisReport", back_populates="findings"
    )


class FeedbackAnnotation(Base):
    """Model for storing human-in-the-loop feedback on AI-generated findings."""

    __tablename__ = "feedback_annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    finding_id: Mapped[int] = mapped_column(Integer, ForeignKey("findings.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    user_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_type: Mapped[str] = mapped_column(String, default="finding_accuracy")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    finding: Mapped["Finding"] = relationship("Finding")
    user: Mapped["User"] = relationship("User")


# Backward compatibility aliases
Rubric = ComplianceRubric
Report = AnalysisReport


class HabitGoal(Base):
    """User's personal habit goals."""

    __tablename__ = "habit_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    habit_number: Mapped[int | None] = mapped_column(Integer)  # 1-7 for habits
    target_value: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float, default=0.0)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100 percentage
    status: Mapped[str] = mapped_column(String(20), default="active")
    target_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="habit_goals")


class HabitAchievement(Base):
    """User's habit achievements and badges."""

    __tablename__ = "habit_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    achievement_id: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(10), default="🏆")
    category: Mapped[str] = mapped_column(String(50))
    earned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="habit_achievements")


class HabitProgressSnapshot(Base):
    """Periodic snapshots of user's habit progression for trend analysis."""

    __tablename__ = "habit_progress_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    snapshot_date: Mapped[datetime.date] = mapped_column(Date, index=True)

    # Habit breakdown percentages
    habit_1_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    habit_2_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    habit_3_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    habit_4_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    habit_5_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    habit_6_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    habit_7_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Overall metrics
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    overall_progress_score: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    improvement_rate: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="habit_progress_snapshots"
    )
