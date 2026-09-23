"""
Tests herméticos (sin dependencia de Neon PostgreSQL) para:
- Endpoint de descubrimiento dinámico GET /api/config
- Cabeceras Cache-Control no-store en rutas /api/*
- Servido del frontend estático (crítico para el WebView del APK)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_root_serves_frontend_html():
    """La raíz debe servir index.html para que el WebView del APK cargue el front."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")
        body = res.text
        assert "UFPSO Horarios" in body
        assert "/js/app.js" in body


@pytest.mark.asyncio
async def test_static_frontend_is_cacheable_with_revalidation():
    """Los assets estáticos SÍ pueden cachearse (ETag/Last-Modified) pero no con no-store."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_js = await ac.get("/js/api.js")
        assert res_js.status_code == 200
        assert res_js.headers.get("cache-control") != "no-store"
        assert res_js.headers.get("etag") or res_js.headers.get("last-modified")


@pytest.mark.asyncio
async def test_api_config_discovery():
    """GET /api/config permite a la app descubrir la URL del backend sin hardcodear IPs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/config")
        assert res.status_code == 200
        data = res.json()
        assert data["app"] == "UFPSO Horarios & Gestión Académica API"
        assert data["api_base"] == "/api/v1"
        assert data["status"] == "online"
        assert "server_time" in data
        # TTLs acotados para que los cambios se propaguen en tiempo real
        assert data["cache"]["today_ttl_seconds"] <= 30
        assert data["cache"]["week_ttl_seconds"] <= 60
        assert isinstance(data["cors"], list)


@pytest.mark.asyncio
async def test_api_config_not_cached():
    """Los clientes no deben cachear /api/config (tiempo real)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/config")
        assert res.status_code == 200
        assert res.headers.get("cache-control") == "no-store"


@pytest.mark.asyncio
async def test_api_routes_have_no_store_header():
    """Todas las respuestas bajo /api/* deben llevar Cache-Control: no-store sin tocar DB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Ruta que no toca DB (404 genérico del router inexistente) igual lleva la cabecera
        res_unknown = await ac.get("/api/v1/does-not-exist")
        assert res_unknown.status_code == 404
        assert res_unknown.headers.get("cache-control") == "no-store"

        # Endpoint público de info (sin DB)
        res_info = await ac.get("/api/info")
        assert res_info.status_code == 200
        assert res_info.headers.get("cache-control") == "no-store"

        # Endpoint de configuración
        res_config = await ac.get("/api/config")
        assert res_config.headers.get("cache-control") == "no-store"