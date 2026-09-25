import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import auth, home, party, jewelry, custom, dashboard, history, web

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pocketsmart")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting PocketSmart AI server...")
    try:
        init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    yield
    logger.info("Shutting down PocketSmart AI server...")

app = FastAPI(
    title=settings.APP_NAME,
    description="PocketSmart AI - Smart Budget & Recommendation Assistant powered by Google Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Friendly Error Handling (Prevent exposing raw stacktraces)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    # Check if this is an API request or HTML request
    if request.url.path.startswith("/api/") or request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Unable to process recommendation request right now. Please try again later."}
        )
    # Otherwise let FastAPI render standard response or fallback
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please refresh the page or try again."}
    )

# Health Check & Startup Endpoints
@app.get("/api/health", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    from app.services.gemini_service import gemini_service
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "gemini_live": gemini_service.is_live_available,
        "mode": "live_gemini" if gemini_service.is_live_available else "mock_ai"
    }

# Register API Routers
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(party.router)
app.include_router(jewelry.router)
app.include_router(custom.router)
app.include_router(dashboard.router)
app.include_router(history.router)

# Register Web UI Router (must be included so / routes are served)
app.include_router(web.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
