27 logger.warning(error_message)
28 return [{'sentence': error_message, 'source': 'parser'}]
29
30 # 2. Try to open and parse the file
31 try:
32 chunks = []
33 if file_ext == '.pdf':
34 with pdfplumber.open(file_path) as pdf:
35 for i, page in enumerate(pdf.pages, start=1):
36 page_text = page.extract_text() or ""
37 metadata = {'source_document': file_path, 'page': i}
38 page_chunks = sentence_window_chunker(page_text, metadata=metadata)
39 chunks.extend(page_chunks)
40 elif ext == ".docx":
41 try:
42 docx_doc = Document(file_path)
43 except Exception:
44 return [{'sentence': "Error: python-docx not available.", 'window': '', 'metadata': {'source': 'DOCX Parser'}}]
45 full_text = "\n".join([para.text for para in docx_doc.paragraphs])
46 metadata = {'source_document': file_path}
47 doc_chunks = sentence_window_chunker(full_text, metadata=metadata)
48 chunks.extend(doc_chunks)
49 elif ext in [".xlsx", ".xls", ".csv"]:
50 try:
51 if ext in [".xlsx", ".xls"]:
52 df = pd.read_excel(file_path)
53 if isinstance(df, dict):
54 df = next(iter(df.values()))
55 else:
56 df = pd.read_csv(file_path)
57 content = df.to_string(index=False)
58 metadata = {'source_document': file_path}
59 data_chunks = sentence_window_chunker(content, metadata=metadata)
60 chunks.extend(data_chunks)
61 except Exception as e:
62 return [{'sentence': f"Error: Failed to read tabular file: {e}", 'window': '', 'metadata': {'source': 'Data Parser'}}]
63 elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
64 if not Image or not pytesseract:
65 return [{'sentence': "Error: OCR dependencies not available.", 'window': '', 'metadata': {'source': 'OCR Parser'}}]
66 try:
67 img = Image.open(file_path)
68 if img.mode not in ("RGB", "L"):
69 img = img.convert("RGB")  # type: ignore[assignment]
70 txt = pytesseract.image_to_string(img)
71 metadata = {'source_document': file_path}
72 ocr_chunks = sentence_window_chunker(txt or "", metadata=metadata)
73 chunks.extend(ocr_chunks)
74 except Image.UnidentifiedImageError as e:
75 return [{'sentence': f"Error: Unidentified image: {e}", 'window': '', 'metadata': {'source': 'OCR Parser'}}]
76 elif ext == ".txt":
77 with open(file_path, "r", encoding="utf-8") as f:
78 txt = f.read()
79 metadata = {'source_document': file_path}
80 txt_chunks = sentence_window_chunker(txt, metadata=metadata)
81 chunks.extend(txt_chunks)
82 else:
83 return [{'sentence': f"Error: Unsupported file type: {ext}", 'window': '', 'metadata': {'source': 'File Handler'}}]