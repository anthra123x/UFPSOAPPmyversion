from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Student
from app.schemas.schemas import StudentLogin, StudentRegister, StudentOut, TokenResponse
from app.services.auth_service import (
    verify_password, get_password_hash, create_access_token, get_required_student
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: StudentRegister, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo estudiante en la plataforma con su código universitario."""
    res = await db.execute(select(Student).where(Student.code == data.code.strip()))
    existing = res.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El estudiante con código {data.code} ya está registrado."
        )
        
    hashed_pwd = get_password_hash(data.password) if data.password else None
    new_student = Student(
        code=data.code.strip(),
        name=data.name.strip(),
        email=data.email.strip() if data.email else None,
        hashed_password=hashed_pwd,
        career=data.career,
        pensum=data.pensum
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    
    token = create_access_token({"sub": new_student.code, "id": new_student.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        student=StudentOut.model_validate(new_student)
    )

@router.post("/login", response_model=TokenResponse)
async def login(data: StudentLogin, db: AsyncSession = Depends(get_db)):
    """
    Inicia sesión con el código universitario.
    Si el estudiante aún no existe en base de datos, se auto-registra provisionalmente
    para permitir la posterior carga inmediata del PDF de SIA.
    """
    code_clean = data.code.strip()
    res = await db.execute(select(Student).where(Student.code == code_clean))
    student = res.scalar_one_or_none()
    
    if not student:
        # Auto-registro rápido para estudiantes que inician por primera vez
        student = Student(
            code=code_clean,
            name=f"Estudiante {code_clean}",
            hashed_password=get_password_hash(data.password) if data.password else None
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)
    else:
        if student.hashed_password and data.password:
            if not verify_password(data.password, student.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contraseña o PIN incorrecto."
                )
                
    token = create_access_token({"sub": student.code, "id": student.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        student=StudentOut.model_validate(student)
    )

@router.get("/me", response_model=StudentOut)
async def get_me(student: Student = Depends(get_required_student)):
    """Obtiene el perfil del estudiante autenticado."""
    return StudentOut.model_validate(student)
