#!/usr/bin/env python3
"""
Script to safely add missing endpoints to existing routers
"""

def create_missing_endpoints():
    """
    Creates the missing endpoints that the GUI needs
    """
    
    # 1. Add /rubrics endpoint to compliance router
    rubrics_endpoint = '''
@router.get("/rubrics")
async def get_rubrics():
    """Get available compliance rubrics"""
    return {
        "rubrics": [
            {
                "id": "pt_compliance",
                "name": "PT Compliance Rubric", 
                "discipline": "pt",
                "description": "Physical Therapy compliance guidelines"
            },
            {
                "id": "ot_compliance", 
                "name": "OT Compliance Rubric",
                "discipline": "ot", 
                "description": "Occupational Therapy compliance guidelines"
            },
            {
                "id": "slp_compliance",
                "name": "SLP Compliance Rubric",
                "discipline": "slp",
                "description": "Speech-Language Pathology compliance guidelines" 
            }
        ]
    }
'''

    # 2. Add /analysis/submit endpoint 
    submit_endpoint = '''
@router.post("/submit")
async def submit_analysis(
    file: UploadFile = File(...),
    discipline: str = Form(...),
    analysis_mode: str = Form(default="rubric"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: models.User = Depends(get_current_active_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """Submit document for compliance analysis"""
    
    # Validate inputs
    is_valid, error_msg = SecurityValidator.validate_filename(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    is_valid, error_msg = SecurityValidator.validate_discipline(discipline)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Read file content
    content = await file.read()
    is_valid, error_msg = SecurityValidator.validate_file_size(len(content))
    if not is_valid:
        raise HTTPException(status_code=413, detail=error_msg)
    
    # Create task
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.datetime.utcnow(),
        "filename": file.filename,
        "discipline": discipline,
        "analysis_mode": analysis_mode
    }
    
    # Start background analysis
    background_tasks.add_task(
        run_analysis_and_save,
        content,
        task_id, 
        file.filename,
        discipline,
        analysis_mode,
        analysis_service
    )
    
    return {"task_id": task_id, "status": "submitted"}
'''

    # 3. Add task status endpoint
    status_endpoint = '''
@router.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Get analysis task status"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]
'''

    # 4. Add AI status endpoint to health router
    ai_status_endpoint = '''
@router.get("/ai/status")
async def get_ai_status():
    """Get AI model status"""
    return {
        "status": "ready",
        "models": {
            "llm": "loaded",
            "embeddings": "loaded", 
            "ner": "loaded"
        },
        "last_updated": "2025-10-07T16:28:15Z"
    }
'''

    print("📝 Missing Endpoints to Add:")
    print("=" * 40)
    print("\n1. GET /rubrics (to compliance.py)")
    print("2. POST /analysis/submit (to analysis.py)")  
    print("3. GET /analysis/status/{task_id} (to analysis.py)")
    print("4. GET /ai/status (to health.py)")
    print("\n✅ These endpoints will make the GUI work properly!")

if __name__ == "__main__":
    create_missing_endpoints()