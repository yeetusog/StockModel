import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.routers.signal import router
from app.config import settings

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(title="Stock Signal App — NVIDIA NIM", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

if Path("frontend").exists():
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/")
    def dashboard():
        return FileResponse("frontend/dashboard.html")

@app.get("/health")
def health():
    return {"status": "ok", "ticker": settings.ticker,
            "nim_model": settings.nvidia_nim_model,
            "nim_key_set": bool(settings.nvidia_api_key)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)