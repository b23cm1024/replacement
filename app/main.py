from fastapi import FastAPI

app = FastAPI(title="AI Search Backend")

@app.get("/")
def root():
    return {"status": "ok", "message": "AI Search Backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
