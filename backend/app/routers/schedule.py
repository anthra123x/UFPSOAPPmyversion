from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.models import Student
from app.schemas.schemas import (
    ParsedScheduleResult, ScheduleUploadSummary, EnrollmentOut, TodayScheduleOut, WeekScheduleOut, StudentOut
)
from app.services.pdf_parser import parse_sia_schedule_pdf
from app.services.schedule_service import (
    save_parsed_schedule, get_student_enrollments, get_today_schedule, get_week_schedule
)
from app.services.auth_service import get_current_student, get_required_student

router = APIRouter(prefix="/schedule", tags=["Horarios"])

@router.post("/parse-preview", response_model=ParsedScheduleResult)
async def parse_schedule_preview(file: UploadFile = File(...)):
    """
    Parsea el PDF del SIA y retorna los datos extraídos en JSON sin guardarlos en base de datos.
    Ideal para que la app Android muestre una pantalla de vista previa y confirmación.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un documento PDF válido de SIA."
        )
    try:
        content = await file.read()
        parsed = parse_sia_schedule_pdf(content)
        return ParsedScheduleResult.model_validate(parsed)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al procesar el PDF del SIA: {str(e)}"
        )

@router.post("/upload-pdf", response_model=ScheduleUploadSummary)
async def upload_schedule_pdf(
    file: UploadFile = File(...),
    current_student: Optional[Student] = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Sube el PDF descargado del SIA, extrae la carga académica y la almacena en base de datos.
    Si se incluye token de autenticación, se asocia a la cuenta activa;
    si no, se identifica y vincula automáticamente por el código del estudiante presente en el PDF.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo adjunto debe ser un documento PDF de SIA."
        )
    try:
        content = await file.read()
        parsed = parse_sia_schedule_pdf(content)
        
        # Guardar en base de datos
        result = await save_parsed_schedule(db, parsed, current_student)
        student = result["student"]
        
        # Obtener lista completa de inscripciones actualizadas
        enrollments = await get_student_enrollments(db, student.id)
        
        enrollments_out = []
        for enr in enrollments:
            enrollments_out.append(EnrollmentOut(
                id=enr.id,
                full_code=enr.full_code,
                subject_code=enr.subject.code,
                subject_name=enr.subject.name,
                group=enr.group,
                quota_id=enr.quota_id,
                professor_name=enr.professor.name if enr.professor else "Sin asignar",
                credits=enr.subject.credits,
                color_hex=enr.color_hex,
                slots=[s for s in enr.slots]
            ))
            
        # Generar token JWT automático para que la app quede autenticada inmediatamente
        from app.services.auth_service import create_access_token
        from app.services.cache_service import cache
        token = create_access_token({"sub": student.code, "id": student.id})
        
        # Invalidar caché previa de este estudiante
        cache.delete_prefix(f"schedule:{student.id}")
        
        return ScheduleUploadSummary(
            student=StudentOut.model_validate(student),
            academic_period=result["period"].name,
            courses_enrolled=result["courses_count"],
            slots_created=result["slots_count"],
            professors_linked=result["professors_count"],
            courses=enrollments_out,
            access_token=token,
            token_type="bearer",
            message="Horario del SIA importado y sincronizado exitosamente con salones enriquecidos."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No fue posible importar el horario: {str(e)}"
        )

@router.get("/current", response_model=List[EnrollmentOut])
async def get_current_schedule(
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene la lista de todas las asignaturas inscritas con sus franjas y profesores."""
    enrollments = await get_student_enrollments(db, student.id)
    output = []
    for enr in enrollments:
        output.append(EnrollmentOut(
            id=enr.id,
            full_code=enr.full_code,
            subject_code=enr.subject.code,
            subject_name=enr.subject.name,
            group=enr.group,
            quota_id=enr.quota_id,
            professor_name=enr.professor.name if enr.professor else "Sin asignar",
            credits=enr.subject.credits,
            color_hex=enr.color_hex,
            slots=[s for s in enr.slots]
        ))
    return output

@router.get("/today", response_model=TodayScheduleOut)
async def get_today(
    weekday: Optional[int] = Query(None, ge=0, le=6, description="0=Lunes, ..., 6=Domingo (para simulación/testing)"),
    time_sim: Optional[str] = Query(None, pattern=r"^\d{2}:\d{2}$", description="Hora simulada 'HH:MM'"),
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve la agenda de clases para el día de hoy, indicando si hay alguna clase en curso,
    cuál es la siguiente y los minutos restantes para comenzar.
    """
    return await get_today_schedule(db, student.id, weekday, time_sim)

@router.get("/week", response_model=WeekScheduleOut)
async def get_week(
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Devuelve la cuadrícula semanal completa de lunes a sábado organizada por días."""
    return await get_week_schedule(db, student.id)

@router.get("/professors")
async def get_my_professors(
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Devuelve el directorio de profesores del semestre con sus asignaturas asignadas."""
    enrollments = await get_student_enrollments(db, student.id)
    profs = []
    for enr in enrollments:
        if enr.professor:
            profs.append({
                "professor_id": enr.professor.id,
                "name": enr.professor.name,
                "email": enr.professor.email,
                "subject": enr.subject.name,
                "subject_code": enr.full_code,
                "group": enr.group
            })
    return profs
