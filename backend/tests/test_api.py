import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine, Base

SAMPLE_PDF_PATH = "/home/omicron/Descargas/descarga.pdf"

@pytest.fixture(autouse=True)
async def prepare_database():
    """Garantiza que las tablas estén creadas antes de ejecutar los tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_root_and_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_auth_login_and_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login o auto-registro inicial
        res = await ac.post("/api/v1/auth/login", json={"code": "0192977"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        token = data["access_token"]
        assert data["student"]["code"] == "0192977"

        # Consulta de perfil /me
        headers = {"Authorization": f"Bearer {token}"}
        res_me = await ac.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["code"] == "0192977"

@pytest.mark.asyncio
async def test_upload_schedule_pdf_and_queries():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Iniciar sesión
        res_auth = await ac.post("/api/v1/auth/login", json={"code": "0192977"})
        token = res_auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Probar Preview
        with open(SAMPLE_PDF_PATH, "rb") as f:
            files = {"file": ("horario.pdf", f, "application/pdf")}
            res_preview = await ac.post("/api/v1/schedule/parse-preview", files=files)
        assert res_preview.status_code == 200
        preview_data = res_preview.json()
        assert preview_data["courses_count"] == 7
        assert preview_data["student"]["student_code"] == "0192977"

        # 2. Subir y guardar horario
        with open(SAMPLE_PDF_PATH, "rb") as f:
            files = {"file": ("horario.pdf", f, "application/pdf")}
            res_upload = await ac.post("/api/v1/schedule/upload-pdf", files=files, headers=headers)
        assert res_upload.status_code == 200
        upload_data = res_upload.json()
        assert upload_data["courses_enrolled"] == 7
        assert upload_data["slots_created"] > 0
        assert upload_data["student"]["code"] == "0192977"

        # 3. Consultar horario actual
        res_curr = await ac.get("/api/v1/schedule/current", headers=headers)
        assert res_curr.status_code == 200
        courses = res_curr.json()
        assert len(courses) == 7

        # 4. Consultar clases de hoy simulando Jueves a las 06:15 AM
        # Jueves = 3 en 0-indexed (Lunes=0, Martes=1, Miercoles=2, Jueves=3)
        res_today = await ac.get("/api/v1/schedule/today?weekday=3&time_sim=06:15", headers=headers)
        assert res_today.status_code == 200
        today_data = res_today.json()
        assert today_data["day_name"] == "JUEVES"
        assert today_data["total_classes"] >= 2
        # Fundamentos de programación de 06:00 a 07:00 debe estar EN_CURSO
        assert today_data["active_class"] is not None
        assert "PROGRAMACIÓN" in today_data["active_class"]["subject_name"]
        assert today_data["active_class"]["status"] == "EN_CURSO"

        # 5. Consultar cuadrícula semanal
        res_week = await ac.get("/api/v1/schedule/week", headers=headers)
        assert res_week.status_code == 200
        week_data = res_week.json()
        assert week_data["total_subjects"] == 7
        assert len(week_data["days"]) == 6

        # 6. Consultar directorio de profesores
        res_profs = await ac.get("/api/v1/schedule/professors", headers=headers)
        assert res_profs.status_code == 200
        profs_data = res_profs.json()
        assert len(profs_data) >= 7

@pytest.mark.asyncio
async def test_tasks_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_auth = await ac.post("/api/v1/auth/login", json={"code": "0192977"})
        token = res_auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Crear tarea / parcial
        task_payload = {
            "title": "Primer Parcial Cálculo Diferencial",
            "description": "Límites y continuidad, bloques I y C",
            "task_type": "PARCIAL",
            "corte": 1
        }
        res_create = await ac.post("/api/v1/tasks/", json=task_payload, headers=headers)
        assert res_create.status_code == 201
        created_task = res_create.json()
        assert created_task["title"] == "Primer Parcial Cálculo Diferencial"
        task_id = created_task["id"]

        # Listar tareas
        res_list = await ac.get("/api/v1/tasks/", headers=headers)
        assert res_list.status_code == 200
        assert any(t["id"] == task_id for t in res_list.json())

        # Actualizar tarea (completar)
        res_update = await ac.put(f"/api/v1/tasks/{task_id}", json={"is_completed": True}, headers=headers)
        assert res_update.status_code == 200
        assert res_update.json()["is_completed"] is True

        # Eliminar tarea
        res_del = await ac.delete(f"/api/v1/tasks/{task_id}", headers=headers)
        assert res_del.status_code == 204

@pytest.mark.asyncio
async def test_campus_classrooms():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/campus/resolve/I106")
        assert res.status_code == 200
        data = res.json()
        assert "Bloque I" in data["building"]
        assert data["floor"] == "Piso 1"
        assert data["category"] == "AULA"

        res_scis = await ac.get("/api/v1/campus/resolve/SCIS")
        assert res_scis.status_code == 200
        assert res_scis.json()["category"] == "SALA_COMPUTO"
