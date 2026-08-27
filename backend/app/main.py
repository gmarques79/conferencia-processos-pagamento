import os
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config.settings import settings
from app.routers import processes
from app.services.ocr_service import ocr_service

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API stateless para conferência de processos de pagamento de fornecedores.",
)

# CORS Middleware (Local development support)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint (used by Railway health check)
@app.get("/api/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ocr_available": ocr_service.is_available,
    }

# Include API Routers
app.include_router(processes.router, prefix=settings.API_V1_STR)

# Determine static frontend dist location
# Checks: 1. /app/frontend/dist (Docker standard) 2. ../frontend/dist (Local build) 3. custom STATIC_DIR
potential_static_dirs = [
    Path("/app/frontend/dist"),
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent.parent / "frontend_dist",
    settings.STATIC_DIR,
]

static_dist_path: Path | None = None
for p in potential_static_dirs:
    if p.exists() and (p / "index.html").is_file():
        static_dist_path = p
        break

if static_dist_path:
    # Mount assets folder if exists
    assets_path = static_dist_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    # SPA Fallback for all non-api routes
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Prevent intercepting /api routes
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Endpoint não encontrado"},
            )

        # Check if specific static file exists (e.g. vite.svg, favicon.ico)
        file_path = static_dist_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Default fallback to index.html
        return FileResponse(static_dist_path / "index.html")

else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "app": settings.APP_NAME,
            "status": "online",
            "message": "Backend FastAPI em execução. Frontend servido separadamente em modo de desenvolvimento.",
            "health_check": "/api/health",
            "docs": "/docs",
        }

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Ocorreu um erro interno ao processar sua solicitação: {str(exc)}"
        },
    )
