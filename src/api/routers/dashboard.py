from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import get_current_active_user
from ...database import crud, models, schemas
from ...database import get_async_db
from ...core.report_generator import ReportGenerator

router = APIRouter()
report_generator = ReportGenerator()


@router.get("/reports", response_model=List[schemas.Report])
async def read_reports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return await crud.get_reports(db, skip=skip, limit=limit)


@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def read_report(
    report_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    db_report = await crud.get_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    report_html = report_generator.generate_html_report(
        analysis_result=db_report.analysis_result,
        doc_name=db_report.document_name,
        analysis_mode="rubric",
    )
    return HTMLResponse(content=report_html)


@router.get("/findings-summary", response_model=List[schemas.FindingSummary])
async def read_findings_summary(
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    if hasattr(crud, "get_findings_summary"):
        return await crud.get_findings_summary(db)
    return []
