from fastapi import FastAPI

from app.presentation.api import jobs_router

app = FastAPI(title="Grounded Transcription Agent")
app.include_router(jobs_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
