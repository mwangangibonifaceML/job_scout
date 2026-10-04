from fastapi import FastAPI

app = FastAPI(
    title="Job Scout API",
    description="API for searching and managing job listings",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
