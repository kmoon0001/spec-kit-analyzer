import os
import shutil
import uuid
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    BackgroundTasks,
    HTTPException,
    Depends,
    Form,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from src.core.analysis_service import AnalysisService
from src.auth import auth_service
from src.models import User, Token
from src.database import get_db, SessionLocal

app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

analysis_service = AnalysisService()
tasks = {}


class TaskStatus(BaseModel):
    task_id: str
    status: str
    error: str | None = None


class AnalysisResult(BaseModel):
    task_id: str
    status: str


def run_analysis(
    file_path: str,
    task_id: str,
    rubric_id: int | None,
    discipline: str | None,
    analysis_mode: str,
):
    try:
        report_html = analysis_service.analyze_document(
            file_path,
            rubric_id=rubric_id,
            discipline=discipline,
            analysis_mode=analysis_mode,
        )
        tasks[task_id] = {"status": "completed", "result": report_html}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)
):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user


@app.post("/analyze", response_model=AnalysisResult, status_code=202)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    discipline: str = Form("All"),
    rubric_id: int = Form(None),
    analysis_mode: str = Form("rubric"),
    token: str = Depends(oauth2_scheme),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if file.content_type not in ["text/plain", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    task_id = str(uuid.uuid4())
    temp_file_path = f"temp_{task_id}_{file.filename}"

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail="Could not save file")

    background_tasks.add_task(
        run_analysis, temp_file_path, task_id, rubric_id, discipline, analysis_mode
    )
    tasks[task_id] = {"status": "processing"}

    return {"task_id": task_id, "status": "processing"}


@app.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    responses={200: {"content": {"text/html": {}}}},
)
async def get_task_status(task_id: str, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        return HTMLResponse(content=task["result"])
    else:
        return JSONResponse(content=task)
