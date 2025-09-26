37

38 
# 2. Check for a semantically similar report in the cache (database)
39 
cached_report = crud.find_similar_report(db, new_embedding)
40

41 if cached_report:
42 # --- CACHE HIT ---
43 logger.info(f"Semantic cache hit for document: {doc_name}. Using cached report ID: {cached_report.id}")
44 analysis_result = cached_report.analysis_result
45 else:
46 # --- CACHE MISS ---
47 logger.info(f"Semantic cache miss for document: {doc_name}. Performing full analysis.")
48 # Perform the full analysis to get the structured data
49 analysis_result = analysis_service.analyzer.analyze_document(
50 document_text=document_text,
51 discipline=discipline,
52 doc_type="Unknown" # This will be replaced by the classifier
53             )
54
55 # Save the new analysis result and its embedding to the database
56 report_data = {
57 "document_name": doc_name,
58 "compliance_score": "N/A", # Scoring service was removed
59 "analysis_result": analysis_result,
60 "document_embedding": embedding_bytes
61             }
62 crud.create_report_and_findings(db, report_data, analysis_result.get("findings", []))
63
64 # 3. Generate the HTML report (either from cached or new data)
65 report_html = analysis_service.report_generator.generate_html_report(
66 analysis_result=analysis_result,
67 doc_name=doc_name,
68 analysis_mode=analysis_mode
69         )
70
71 tasks[task_id] = {"status": "completed", "result": report_html}
72
73 except Exception as e:
74 logger.error(f"Error in analysis background task: {e}", exc_info=True)
75 tasks[task_id] = {"status": "failed", "error": str(e)}
76 finally:
77 db.close()
78 if os.path.exists(file_path):
79 os.remove(file_path)
80
81@router.post("/analyze", response_model=schemas.AnalysisResult, status_code=202)
82async def analyze_document(
83 background_tasks: BackgroundTasks,
84 file: UploadFile = File(...),
85 discipline: str = Form("All"),
86 analysis_mode: str = Form("rubric"),
87 current_user: models.User = Depends(get_current_active_user),
88 analysis_service: AnalysisService = Depends(get_analysis_service),
89):
90 task_id = str(uuid.uuid4())
91 # Ensure filename is not None, providing a default if it is.
92 filename = file.filename if file.filename else "uploaded_document.tmp"
93 temp_file_path = f"temp_{task_id}_{filename}"
94
95 with open(temp_file_path, "wb") as buffer:
96 shutil.copyfileobj(file.file, buffer)
97
98 background_tasks.add_task(
99 run_analysis_and_save, temp_file_path, task_id, filename, discipline, analysis_mode, analysis_service