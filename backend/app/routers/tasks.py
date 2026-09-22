from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.models import Student, Task, Enrollment
from app.schemas.schemas import TaskCreate, TaskUpdate, TaskOut
from app.services.auth_service import get_required_student

router = APIRouter(prefix="/tasks", tags=["Tareas y Evaluaciones"])

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Crea un recordatorio, tarea o parcial asociado a una asignatura o corte."""
    subject_name = None
    if data.enrollment_id:
        res_enr = await db.execute(
            select(Enrollment).options(selectinload(Enrollment.subject))
            .where(Enrollment.id == data.enrollment_id, Enrollment.student_id == student.id)
        )
        enr = res_enr.scalar_one_or_none()
        if not enr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no encontrada.")
        subject_name = enr.subject.name

    new_task = Task(
        student_id=student.id,
        enrollment_id=data.enrollment_id,
        title=data.title.strip(),
        description=data.description.strip() if data.description else None,
        due_date=data.due_date,
        task_type=data.task_type.upper(),
        corte=data.corte,
        is_completed=False
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    return TaskOut(
        id=new_task.id,
        title=new_task.title,
        description=new_task.description,
        enrollment_id=new_task.enrollment_id,
        subject_name=subject_name,
        due_date=new_task.due_date,
        task_type=new_task.task_type,
        corte=new_task.corte,
        is_completed=new_task.is_completed,
        created_at=new_task.created_at
    )

@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    is_completed: Optional[bool] = Query(None, description="Filtrar por estado completado"),
    corte: Optional[int] = Query(None, ge=1, le=3, description="Filtrar por corte académico (1, 2, 3)"),
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene las tareas y evaluaciones del estudiante."""
    query = (
        select(Task)
        .options(selectinload(Task.enrollment).selectinload(Enrollment.subject))
        .where(Task.student_id == student.id)
        .order_by(Task.is_completed.asc(), Task.due_date.asc().nullslast())
    )
    if is_completed is not None:
        query = query.where(Task.is_completed == is_completed)
    if corte is not None:
        query = query.where(Task.corte == corte)
        
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    out = []
    for t in tasks:
        s_name = t.enrollment.subject.name if t.enrollment and t.enrollment.subject else None
        out.append(TaskOut(
            id=t.id,
            title=t.title,
            description=t.description,
            enrollment_id=t.enrollment_id,
            subject_name=s_name,
            due_date=t.due_date,
            task_type=t.task_type,
            corte=t.corte,
            is_completed=t.is_completed,
            created_at=t.created_at
        ))
    return out

@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza una tarea (marcar como completada, editar título, fecha o corte)."""
    res = await db.execute(
        select(Task)
        .options(selectinload(Task.enrollment).selectinload(Enrollment.subject))
        .where(Task.id == task_id, Task.student_id == student.id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada.")
        
    if data.title is not None:
        task.title = data.title.strip()
    if data.description is not None:
        task.description = data.description.strip()
    if data.due_date is not None:
        task.due_date = data.due_date
    if data.task_type is not None:
        task.task_type = data.task_type.upper()
    if data.corte is not None:
        task.corte = data.corte
    if data.is_completed is not None:
        task.is_completed = data.is_completed
        
    await db.commit()
    await db.refresh(task)
    
    s_name = task.enrollment.subject.name if task.enrollment and task.enrollment.subject else None
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        enrollment_id=task.enrollment_id,
        subject_name=s_name,
        due_date=task.due_date,
        task_type=task.task_type,
        corte=task.corte,
        is_completed=task.is_completed,
        created_at=task.created_at
    )

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    student: Student = Depends(get_required_student),
    db: AsyncSession = Depends(get_db)
):
    """Elimina una tarea."""
    res = await db.execute(select(Task).where(Task.id == task_id, Task.student_id == student.id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada.")
        
    await db.delete(task)
    await db.commit()
