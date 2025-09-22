from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend for Therapy Compliance Analyzer"}

# Placeholder for future analysis endpoint
@app.post("/analyze")
async def analyze_document(text: str):
    # In the future, this will call the new AI model pipeline
    return {"message": "Analysis endpoint placeholder", "received_text_length": len(text)}
