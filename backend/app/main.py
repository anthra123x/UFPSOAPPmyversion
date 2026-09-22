import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import engine, Base
from app.routers import auth, schedule, tasks, campus
import app.models # Ensure all models are registered with Base.metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos creando las tablas necesarias en Neon PostgreSQL."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="UFPSO Horarios & Gestión Académica API",
    description=(
        "Backend de alto rendimiento para la aplicación móvil y web estudiantil de la "
        "Universidad Francisco de Paula Santander Seccional Ocaña (UFPSO). "
        "Permite la importación y parseo inteligente del PDF de horario del SIA, "
        "cálculo de clases del día en tiempo real, enriquecimiento de salones/bloques, "
        "gestión de tareas y seguimiento de cortes académicos."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de routers bajo el prefijo unificado /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(campus.router, prefix="/api/v1")

@app.get("/health", tags=["General"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected (Neon PostgreSQL)"
    }

@app.get("/api/info", tags=["General"])
async def api_info():
    return {
        "app": "UFPSO Horarios & Gestión Académica API",
        "institution": "Universidad Francisco de Paula Santander Seccional Ocaña",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Servir Frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.isdir(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    
    if os.path.isdir(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.isdir(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
        
    @app.get("/", tags=["Frontend"])
    async def serve_root():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return await api_info()
else:
    @app.get("/", tags=["General"])
    async def root():
        return await api_info()
