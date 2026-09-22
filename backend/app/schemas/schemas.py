from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- AUTH SCHEMAS ---
class StudentLogin(BaseModel):
    code: str = Field(..., description="Código universitario UFPSO (ej. 0192977)")
    password: Optional[str] = Field(None, description="Contraseña o PIN (opcional)")

class StudentRegister(BaseModel):
    code: str = Field(..., description="Código universitario UFPSO (ej. 0192977)")
    name: str = Field(..., description="Nombre completo del estudiante")
    email: Optional[str] = None
    password: Optional[str] = None
    career: Optional[str] = None
    pensum: Optional[str] = None

class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    email: Optional[str] = None
    career: Optional[str] = None
    pensum: Optional[str] = None
    current_semester: Optional[int] = None
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentOut

# --- SCHEDULE & CLASS SLOTS ---
class ScheduleSlotBase(BaseModel):
    day_of_week: str
    day_number: int
    start_time: str # "08:00"
    end_time: str   # "10:00"
    classroom_code: str # "I106"
    classroom_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    campus: Optional[str] = None

class ScheduleSlotOut(ScheduleSlotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_code: str # "0193101D"
    subject_code: str # "0193101"
    subject_name: str # "FUNDAMENTOS DE PROGRAMACIÓN"
    group: str # "D"
    quota_id: Optional[str] = None # "29"
    professor_name: Optional[str] = None
    credits: int = 3
    color_hex: Optional[str] = None
    slots: List[ScheduleSlotOut] = []

# --- TODAY SCHEDULE & SMART CALCULATIONS ---
class TodayClassItem(BaseModel):
    enrollment_id: int
    full_code: str
    subject_name: str
    group: str
    professor_name: Optional[str] = None
    start_time: str
    end_time: str
    classroom_code: str
    classroom_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    campus: Optional[str] = None
    status: str # "EN_CURSO", "PROXIMA", "FINALIZADA", "POR_VENIR", "PROGRAMADA"
    minutes_until_start: Optional[int] = None
    minutes_remaining: Optional[int] = None

class TodayScheduleOut(BaseModel):
    day_name: str
    day_number: int
    current_time: str
    total_classes: int
    active_class: Optional[TodayClassItem] = None
    next_class: Optional[TodayClassItem] = None
    classes: List[TodayClassItem] = []

class DayScheduleGroup(BaseModel):
    day_name: str
    day_number: int
    slots: List[TodayClassItem] = []

class WeekScheduleOut(BaseModel):
    period_name: str
    total_subjects: int
    total_weekly_hours: float
    days: List[DayScheduleGroup] = []

# --- PDF IMPORT SCHEMAS ---
class ParsedSlot(BaseModel):
    day_of_week: str
    day_number: int
    start_time: str
    end_time: str
    classroom_code: str
    classroom_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    campus: Optional[str] = None

class ParsedCourse(BaseModel):
    full_code: str
    subject_code: str
    group: Optional[str] = None
    raw_name: str
    name: str
    quota_id: Optional[str] = None
    professor: Optional[str] = None
    slots: List[ParsedSlot] = []

class ParsedStudentHeader(BaseModel):
    career: Optional[str] = None
    generated_date: Optional[str] = None
    academic_period: Optional[str] = None
    student_name: Optional[str] = None
    student_code: Optional[str] = None
    pensum: Optional[str] = None

class ParsedScheduleResult(BaseModel):
    student: ParsedStudentHeader
    professors_found: int
    courses_count: int
    courses: List[ParsedCourse]

class ScheduleUploadSummary(BaseModel):
    student: StudentOut
    academic_period: str
    courses_enrolled: int
    slots_created: int
    professors_linked: int
    courses: List[EnrollmentOut]
    access_token: Optional[str] = None
    token_type: str = "bearer"
    message: str

# --- TASK SCHEMAS ---
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    enrollment_id: Optional[int] = None
    due_date: Optional[datetime] = None
    task_type: str = "TAREA" # PARCIAL, QUIZ, TALLER, PROYECTO, TAREA
    corte: Optional[int] = None # 1, 2, 3

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    task_type: Optional[str] = None
    corte: Optional[int] = None
    is_completed: Optional[bool] = None

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str] = None
    enrollment_id: Optional[int] = None
    subject_name: Optional[str] = None
    due_date: Optional[datetime] = None
    task_type: str
    corte: Optional[int] = None
    is_completed: bool
    created_at: datetime

# --- CAMPUS SCHEMAS ---
class ClassroomInfoOut(BaseModel):
    code: str
    name: str
    building: str
    floor: str
    campus: str
    category: str # "AULA", "SALA_COMPUTO", "DEPORTIVO", "LABORATORIO", "AUDITORIO"
    description: Optional[str] = None
