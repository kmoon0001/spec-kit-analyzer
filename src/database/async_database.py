"""
Async database operations for improved I/O performance.
Uses connection pooling and non-blocking operations.
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from contextlib import asynccontextmanager
from .models import Report

logger = logging.getLogger(__name__)

class AsyncDatabaseService:
    """High-performance async database service with connection pooling."""
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./compliance.db"):
        try:
            from ..core.performance_manager import get_performance_config
            self.config = get_performance_config()
            pool_size = self.config.connection_pool_size
        except ImportError:
            pool_size = 10  # Default fallback
        
        self.database_url = database_url
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=pool_size * 2,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(f"Async database initialized with pool size: {pool_size}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper cleanup."""
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def create_report(self, document_name: str, compliance_score: float, 
                           analysis_result: Dict[str, Any], document_type: Optional[str] = None) -> int:
        """Create a new analysis report."""
        async with self.get_session() as session:
            report = Report(
                document_name=document_name,
                compliance_score=compliance_score,
                analysis_result=analysis_result,
                document_type=document_type
            )
            
            session.add(report)
            await session.commit()
            await session.refresh(report)
            
            logger.info(f"Created report {report.id} for document: {document_name}")
            return int(report.id)
    
    async def get_reports_with_pagination(self, skip: int = 0, limit: int = 100,
                                        document_type: Optional[str] = None,
                                        min_score: Optional[float] = None) -> List[Report]:
        """Get reports with efficient pagination and filtering."""
        async with self.get_session() as session:
            query = select(Report).options(selectinload(Report.findings))
            
            if document_type:
                query = query.where(Report.document_type == document_type)
            if min_score is not None:
                query = query.where(Report.compliance_score >= min_score)
            
            query = query.order_by(Report.analysis_date.desc()).offset(skip).limit(limit)
            
            result = await session.execute(query)
            reports = result.scalars().all()
            
            return list(reports)
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")

# Global async database service
async_db_service = AsyncDatabaseService()