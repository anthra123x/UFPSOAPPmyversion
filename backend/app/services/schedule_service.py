from datetime import datetime, timezone, time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models.models import (
    Student, AcademicPeriod, Professor, Subject, Enrollment, ScheduleSlot
)
from app.schemas.schemas import (
    TodayClassItem, TodayScheduleOut, DayScheduleGroup, WeekScheduleOut, EnrollmentOut, ScheduleSlotOut
)
from app.services.cache_service import cache

# Paleta de colores atractiva para distinguir materias en la app móvil
PALETTE_COLORS = [
    "#E53935", # Rojo UFPSO
    "#1E88E5", # Azul ingeniería
    "#43A047", # Verde
    "#FB8C00", # Naranja
    "#8E24AA", # Púrpura
    "#00ACC1", # Cian
    "#3949AB", # Índigo
    "#D81B60", # Rosa
    "#00897B", # Turquesa
]

DAY_NAMES_ES = {
    0: "LUNES",
    1: "MARTES",
    2: "MIÉRCOLES",
    3: "JUEVES",
    4: "VIERNES",
    5: "SÁBADO",
    6: "DOMINGO"
}

async def save_parsed_schedule(
    db: AsyncSession,
    parsed_data: Dict[str, Any],
    authenticated_student: Optional[Student] = None
) -> Dict[str, Any]:
    """
    Persiste en base de datos el resultado del parseo de PDF de SIA optimizado con consultas por lotes:
    - Reduce de 28 viajes de red a solo 3 consultas masivas.
    - Invalida la micro-caché para refresco instantáneo.
    """
    header = parsed_data["student"]
    courses = parsed_data["courses"]
    
    student_code = header.get("student_code")
    student_name = header.get("student_name")
    career = header.get("career")
    pensum = header.get("pensum")
    period_name = header.get("academic_period") or "Segundo semestre de 2026"
    
    # 1. Resolver Estudiante
    student = None
    if authenticated_student:
        student = authenticated_student
        if student_name and not student.name:
            student.name = student_name
        if career:
            student.career = career
        if pensum:
            student.pensum = pensum
    elif student_code:
        result = await db.execute(select(Student).where(Student.code == student_code))
        student = result.scalar_one_or_none()
        if not student:
            student = Student(
                code=student_code,
                name=student_name or f"Estudiante {student_code}",
                career=career,
                pensum=pensum,
                is_active=True
            )
            db.add(student)
            await db.flush()
        else:
            if student_name:
                student.name = student_name
            if career:
                student.career = career
            if pensum:
                student.pensum = pensum
    else:
        raise ValueError("No se encontró código de estudiante válido en el PDF.")

    # 2. Resolver Periodo Académico
    res_period = await db.execute(select(AcademicPeriod).where(AcademicPeriod.name == period_name))
    period = res_period.scalar_one_or_none()
    if not period:
        period = AcademicPeriod(name=period_name, is_active=True)
        db.add(period)
        await db.flush()

    # 3. BATCH LOOKUPS: Consultas agrupadas para máxima velocidad
    subject_codes = [c["subject_code"] for c in courses]
    existing_subjects_res = await db.execute(select(Subject).where(Subject.code.in_(subject_codes)))
    subjects_by_code = {s.code: s for s in existing_subjects_res.scalars().all()}

    prof_names = [c["professor"] for c in courses if c.get("professor")]
    existing_profs_res = await db.execute(select(Professor).where(Professor.name.in_(prof_names)))
    profs_by_name = {p.name: p for p in existing_profs_res.scalars().all()}

    full_codes = [c["full_code"] for c in courses]
    existing_enrollments_res = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.period_id == period.id,
            Enrollment.full_code.in_(full_codes)
        )
    )
    enrollments_by_code = {e.full_code: e for e in existing_enrollments_res.scalars().all()}

    slots_created_count = 0
    professors_linked_count = 0
    enrolled_courses = []

    for idx, c_data in enumerate(courses):
        full_code = c_data["full_code"]
        subject_code = c_data["subject_code"]
        subject_name = c_data["name"]
        group = c_data.get("group") or "A"
        quota_id = c_data.get("quota_id")
        professor_name = c_data.get("professor")
        color_hex = PALETTE_COLORS[idx % len(PALETTE_COLORS)]

        # Asignatura
        subject = subjects_by_code.get(subject_code)
        if not subject:
            subject = Subject(code=subject_code, name=subject_name, career=career)
            db.add(subject)
            await db.flush()
            subjects_by_code[subject_code] = subject
        else:
            if len(subject_name) > len(subject.name):
                subject.name = subject_name

        # Docente
        professor = None
        if professor_name:
            professor = profs_by_name.get(professor_name)
            if not professor:
                professor = Professor(name=professor_name)
                db.add(professor)
                await db.flush()
                profs_by_name[professor_name] = professor
            professors_linked_count += 1

        # Inscripción del estudiante
        enrollment = enrollments_by_code.get(full_code)
        if not enrollment:
            enrollment = Enrollment(
                student_id=student.id,
                subject_id=subject.id,
                period_id=period.id,
                professor_id=professor.id if professor else None,
                group=group,
                full_code=full_code,
                quota_id=quota_id,
                raw_subject_name=c_data.get("raw_name"),
                color_hex=color_hex
            )
            db.add(enrollment)
            await db.flush()
            enrollments_by_code[full_code] = enrollment
        else:
            enrollment.professor_id = professor.id if professor else enrollment.professor_id
            enrollment.quota_id = quota_id or enrollment.quota_id
            enrollment.color_hex = color_hex

        # Limpiar franjas anteriores si existen para reemplazarlas de manera idempotente
        await db.execute(delete(ScheduleSlot).where(ScheduleSlot.enrollment_id == enrollment.id))

        # Insertar franjas de horario
        for slot in c_data.get("slots", []):
            db_slot = ScheduleSlot(
                enrollment_id=enrollment.id,
                day_of_week=slot["day_of_week"],
                day_number=slot["day_number"],
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                classroom_code=slot["classroom_code"],
                classroom_name=slot.get("classroom_name"),
                building=slot.get("building"),
                floor=slot.get("floor"),
                campus=slot.get("campus")
            )
            db.add(db_slot)
            slots_created_count += 1

        enrolled_courses.append(enrollment)

    await db.commit()
    
    # Invalidar caché en memoria del estudiante
    cache.delete_prefix(f"schedule:{student.id}")
    
    return {
        "student": student,
        "period": period,
        "courses_count": len(courses),
        "slots_count": slots_created_count,
        "professors_count": professors_linked_count
    }

async def get_student_enrollments(
    db: AsyncSession,
    student_id: int,
    period_id: Optional[int] = None
) -> List[Enrollment]:
    """Devuelve las inscripciones de un estudiante con asignatura, docente y franjas cargadas."""
    query = (
        select(Enrollment)
        .options(
            selectinload(Enrollment.subject),
            selectinload(Enrollment.professor),
            selectinload(Enrollment.slots),
            selectinload(Enrollment.period)
        )
        .where(Enrollment.student_id == student_id)
    )
    if period_id:
        query = query.where(Enrollment.period_id == period_id)
        
    result = await db.execute(query)
    return result.scalars().all()

async def get_today_schedule(
    db: AsyncSession,
    student_id: int,
    custom_weekday: Optional[int] = None,
    custom_time_str: Optional[str] = None
) -> TodayScheduleOut:
    """Calcula la agenda de clases de hoy, clase activa y próxima clase con micro-caché."""
    now = datetime.now()
    day_idx = custom_weekday if custom_weekday is not None else now.weekday()
    model_day_number = day_idx + 1
    day_name = DAY_NAMES_ES.get(day_idx, "DESCONOCIDO")
    current_time_str = custom_time_str or now.strftime("%H:%M")

    # Clave de micro-caché
    cache_key = f"schedule:{student_id}:today:{day_idx}:{current_time_str}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    enrollments = await get_student_enrollments(db, student_id)
    today_items: List[TodayClassItem] = []
    
    for enr in enrollments:
        for slot in enr.slots:
            if slot.day_number == model_day_number:
                status, minutes_until, minutes_rem = _calculate_slot_timing(
                    slot.start_time, slot.end_time, current_time_str
                )
                
                today_items.append(TodayClassItem(
                    enrollment_id=enr.id,
                    full_code=enr.full_code,
                    subject_name=enr.subject.name,
                    group=enr.group,
                    professor_name=enr.professor.name if enr.professor else "Sin asignar",
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    classroom_code=slot.classroom_code,
                    classroom_name=slot.classroom_name,
                    building=slot.building,
                    floor=slot.floor,
                    campus=slot.campus,
                    status=status,
                    minutes_until_start=minutes_until,
                    minutes_remaining=minutes_rem
                ))

    # Ordenar cronológicamente por hora de inicio
    today_items.sort(key=lambda x: x.start_time)
    
    active_class = next((item for item in today_items if item.status == "EN_CURSO"), None)
    next_class = next((item for item in today_items if item.status == "PROXIMA"), None)
    if not next_class:
        next_class = next((item for item in today_items if item.status == "POR_VENIR"), None)
        
    result_out = TodayScheduleOut(
        day_name=day_name,
        day_number=model_day_number,
        current_time=current_time_str,
        total_classes=len(today_items),
        active_class=active_class,
        next_class=next_class,
        classes=today_items
    )
    
    # Guardar en micro-caché por 30 segundos
    cache.set(cache_key, result_out, ttl_seconds=30)
    return result_out

async def get_week_schedule(
    db: AsyncSession,
    student_id: int
) -> WeekScheduleOut:
    """Devuelve la matriz semanal estructurada para la vista de cuadrícula con micro-caché."""
    cache_key = f"schedule:{student_id}:week"
    cached_week = cache.get(cache_key)
    if cached_week is not None:
        return cached_week

    enrollments = await get_student_enrollments(db, student_id)
    
    days_dict: Dict[int, List[TodayClassItem]] = {
        1: [], 2: [], 3: [], 4: [], 5: [], 6: []
    }
    
    day_labels = {
        1: "LUNES",
        2: "MARTES",
        3: "MIÉRCOLES",
        4: "JUEVES",
        5: "VIERNES",
        6: "SÁBADO"
    }
    
    total_minutes = 0
    period_name = "Semestre Vigente"
    
    for enr in enrollments:
        if enr.period and enr.period.name:
            period_name = enr.period.name
        for slot in enr.slots:
            d_num = slot.day_number
            if d_num in days_dict:
                dur = _time_to_minutes(slot.end_time) - _time_to_minutes(slot.start_time)
                if dur > 0:
                    total_minutes += dur
                    
                days_dict[d_num].append(TodayClassItem(
                    enrollment_id=enr.id,
                    full_code=enr.full_code,
                    subject_name=enr.subject.name,
                    group=enr.group,
                    professor_name=enr.professor.name if enr.professor else "Sin asignar",
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    classroom_code=slot.classroom_code,
                    classroom_name=slot.classroom_name,
                    building=slot.building,
                    floor=slot.floor,
                    campus=slot.campus,
                    status="PROGRAMADA"
                ))

    days_list = []
    for d_num in range(1, 7):
        slots_list = days_dict[d_num]
        slots_list.sort(key=lambda x: x.start_time)
        days_list.append(DayScheduleGroup(
            day_name=day_labels[d_num],
            day_number=d_num,
            slots=slots_list
        ))
        
    week_out = WeekScheduleOut(
        period_name=period_name,
        total_subjects=len(enrollments),
        total_weekly_hours=round(total_minutes / 60.0, 1),
        days=days_list
    )
    
    # Guardar en micro-caché por 60 segundos (antes 300s) para que los cambios
    # en el horario (nuevo PDF SIA, ediciones desde otro dispositivo) se reflejen
    # en la app en tiempo real sin esperar 5 minutos.
    cache.set(cache_key, week_out, ttl_seconds=60)
    return week_out

def _time_to_minutes(t_str: str) -> int:
    parts = t_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def _calculate_slot_timing(start_str: str, end_str: str, current_str: str):
    start_m = _time_to_minutes(start_str)
    end_m = _time_to_minutes(end_str)
    curr_m = _time_to_minutes(current_str)
    
    if curr_m < start_m:
        diff = start_m - curr_m
        status = "PROXIMA" if diff <= 30 else "POR_VENIR"
        return status, diff, None
    elif start_m <= curr_m < end_m:
        rem = end_m - curr_m
        return "EN_CURSO", None, rem
    else:
        return "FINALIZADA", None, None
