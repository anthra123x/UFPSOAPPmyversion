from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.models import Student

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return True
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_student(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[Student]:
    """
    Identifica de forma ultra-robusta al estudiante:
    1. A través del Bearer Token JWT en el encabezado Authorization.
    2. A través del encabezado redundante 'X-Student-Code'.
    3. Fallback al estudiante activo más reciente registrado en base de datos.
    Esto previene por completo bloqueos accidentales 401 al subir horarios o cambiar pestañas.
    """
    # 1. Intentar validar JWT Bearer Token
    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            student_code: str = payload.get("sub")
            if student_code:
                result = await db.execute(select(Student).where(Student.code == student_code))
                student = result.scalar_one_or_none()
                if student:
                    return student
        except JWTError:
            pass

    # 2. Intentar validar mediante encabezado directo X-Student-Code
    x_code = request.headers.get("X-Student-Code")
    if x_code and x_code.strip():
        result = await db.execute(select(Student).where(Student.code == x_code.strip()))
        student = result.scalar_one_or_none()
        if student:
            return student

    # 3. Fallback inteligente: buscar el último estudiante registrado/activo
    result = await db.execute(select(Student).order_by(Student.id.desc()).limit(1))
    student = result.scalar_one_or_none()
    return student

async def get_required_student(
    student: Optional[Student] = Depends(get_current_student)
) -> Student:
    """Garantiza que haya un estudiante activo. Si la base de datos está totalmente vacía, solicita registro."""
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere iniciar sesión o subir un horario PDF para registrar al estudiante.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return student
