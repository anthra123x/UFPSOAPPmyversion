from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Float, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False) # e.g. "0192977"
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    career = Column(String(150), nullable=True) # e.g. "Ingeniería De Sistemas - Ocaña"
    pensum = Column(String(10), nullable=True) # e.g. "03"
    current_semester = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="student", cascade="all, delete-orphan")

class AcademicPeriod(Base):
    __tablename__ = "academic_periods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # e.g. "Segundo semestre de 2026"
    code = Column(String(20), index=True, nullable=True) # e.g. "2026-2"
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    enrollments = relationship("Enrollment", back_populates="period")

class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(150), nullable=True)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    enrollments = relationship("Enrollment", back_populates="professor")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False) # e.g. "0193101"
    name = Column(String(150), nullable=False)
    credits = Column(Integer, default=3)
    career = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    enrollments = relationship("Enrollment", back_populates="subject")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    period_id = Column(Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False)
    professor_id = Column(Integer, ForeignKey("professors.id", ondelete="SET NULL"), nullable=True)
    
    group = Column(String(10), nullable=False, default="A") # e.g. "D"
    full_code = Column(String(30), nullable=False) # e.g. "0193101D"
    quota_id = Column(String(20), nullable=True) # e.g. "29"
    raw_subject_name = Column(String(150), nullable=True)
    color_hex = Column(String(10), nullable=True) # Optional custom badge color for mobile UI
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    __table_args__ = (
        UniqueConstraint("student_id", "period_id", "full_code", name="uq_student_period_course"),
    )

    student = relationship("Student", back_populates="enrollments")
    subject = relationship("Subject", back_populates="enrollments")
    period = relationship("AcademicPeriod", back_populates="enrollments")
    professor = relationship("Professor", back_populates="enrollments")
    slots = relationship("ScheduleSlot", back_populates="enrollment", cascade="all, delete-orphan", order_by="ScheduleSlot.day_number, ScheduleSlot.start_time")
    tasks = relationship("Task", back_populates="enrollment")
    grades = relationship("GradeRecord", back_populates="enrollment", uselist=False, cascade="all, delete-orphan")

class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(String(15), nullable=False) # LUNES, MARTES, MIÉRCOLES, JUEVES, VIERNES, SÁBADO
    day_number = Column(Integer, nullable=False) # 1=Lunes, ..., 6=Sábado
    start_time = Column(String(10), nullable=False) # "08:00"
    end_time = Column(String(10), nullable=False) # "10:00"
    classroom_code = Column(String(30), nullable=False) # "I106", "SCGR3", "CDPU"
    
    # Enriched classroom info
    classroom_name = Column(String(100), nullable=True)
    building = Column(String(100), nullable=True)
    floor = Column(String(50), nullable=True)
    campus = Column(String(100), nullable=True)

    enrollment = relationship("Enrollment", back_populates="slots")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    task_type = Column(String(30), default="TAREA") # PARCIAL, QUIZ, TALLER, PROYECTO, TAREA, OTRO
    corte = Column(Integer, nullable=True) # 1, 2, 3
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    student = relationship("Student", back_populates="tasks")
    enrollment = relationship("Enrollment", back_populates="tasks")

class GradeRecord(Base):
    __tablename__ = "grade_records"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), unique=True, nullable=False)
    corte_1 = Column(Float, nullable=True) # Weight: 35%
    corte_2 = Column(Float, nullable=True) # Weight: 35%
    corte_3 = Column(Float, nullable=True) # Weight: 30%
    final_grade = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    enrollment = relationship("Enrollment", back_populates="grades")
