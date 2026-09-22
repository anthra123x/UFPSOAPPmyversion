from typing import List
from fastapi import APIRouter
from app.schemas.schemas import ClassroomInfoOut
from app.services.classroom_catalog import resolve_classroom, get_all_known_classrooms

router = APIRouter(prefix="/campus", tags=["Campus y Salones UFPSO"])

@router.get("/classrooms", response_model=List[ClassroomInfoOut])
async def list_known_classrooms():
    """Lista los espacios y salones destacados del campus El Algodonal de la UFPSO."""
    return get_all_known_classrooms()

@router.get("/resolve/{classroom_code}", response_model=ClassroomInfoOut)
async def get_classroom_details(classroom_code: str):
    """
    Enriquece y desglosa cualquier código de aula de la UFPSO
    (ej. 'I106' -> Bloque I Salón 106 Piso 1, 'SCIS' -> Sala Cómputo Sistemas).
    """
    return resolve_classroom(classroom_code)
