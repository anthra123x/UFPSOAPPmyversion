import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import engine, Base
from app.routers import auth, schedule, tasks, campus
import app.models # Ensure all models are registered with Base.metadata

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa las tablas en Neon PostgreSQL SIN bloquear el arranque del servidor.
    Si la base de datos está momentáneamente inalcanzable (serverless cold start,
    caída de red), el API arranca igualmente y reintenta de forma perezosa en el
    primer request real que use la base de datos.
    """
    try:
        await asyncio.wait_for(
            _create_tables(),
            timeout=10,
        )
        logger.info("Database connected and tables ensured on startup.")
    except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001 - arranque resiliente
        logger.warning("Database not reachable at startup (%s). API will start anyway.", type(e).__name__)
    yield
    await engine.dispose()

async def _create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

@app.middleware("http")
async def no_cache_api_responses(request: Request, call_next):
    """
    Evita que el WebView Android (o cualquier proxy/cliente) cachee respuestas de la API.
    Sin esta cabecera, GET /api/* pueden servirse de la caché HTTP del WebView y
    los cambios en tiempo real (nuevo PDF, tareas, horario) no se reflejan.
    Los estáticos del frontend (css/js) SÍ conservan revalidación ETag.
    """
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response

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

@app.get("/api/config", tags=["General"])
async def api_config(request: Request):
    """
    Contrato de descubrimiento dinámico para clientes (APK Android / Web).

    Permite que la app obtenga la URL correcta del backend sin IPs hardcodeadas
    y ajuste su comportamiento de caché/tiempo real según el servidor.
    """
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    server_origin = f"{scheme}://{host}"
    return {
        "app": "UFPSO Horarios & Gestión Académica API",
        "status": "online",
        "version": "1.0.0",
        "api_base": "/api/v1",
        "server_origin": server_origin,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "cache": {
            "today_ttl_seconds": 30,
            "week_ttl_seconds": 60,
        },
        "cors": settings.CORS_ORIGINS,
        "docs": "/docs",
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
