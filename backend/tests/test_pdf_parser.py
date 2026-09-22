import os
import pytest
from app.services.pdf_parser import parse_sia_schedule_pdf

SAMPLE_PDF_PATH = "/home/omicron/Descargas/descarga.pdf"

def test_parse_real_sia_pdf():
    assert os.path.exists(SAMPLE_PDF_PATH), f"El archivo de prueba {SAMPLE_PDF_PATH} debe existir."
    
    with open(SAMPLE_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
        
    result = parse_sia_schedule_pdf(pdf_bytes)
    
    # 1. Verificar Metadatos de Cabecera
    student = result["student"]
    assert student["student_code"] == "0192977"
    assert "Martinez Vanegas Andres" in student["student_name"]
    assert "Sistemas" in student["career"]
    assert student["pensum"] == "03"
    assert "Segundo semestre de 2026" in student["academic_period"]
    
    # 2. Verificar Materias
    assert result["courses_count"] == 7
    assert result["professors_found"] == 7
    
    courses = result["courses"]
    courses_by_code = {c["full_code"]: c for c in courses}
    
    # Ajedrez
    assert "0000462A" in courses_by_code
    ajedrez = courses_by_code["0000462A"]
    assert ajedrez["name"] == "AJEDREZ"
    assert ajedrez["quota_id"] == "5"
    assert ajedrez["professor"] == "Correa Pineda William"
    assert len(ajedrez["slots"]) == 1
    assert ajedrez["slots"][0]["day_of_week"] == "JUEVES"
    assert ajedrez["slots"][0]["classroom_code"] == "CDPU"
    
    # Fundamentos de programación (múltiples franjas el jueves + sábado)
    assert "0193101D" in courses_by_code
    fp = courses_by_code["0193101D"]
    assert fp["name"] == "FUNDAMENTOS DE PROGRAMACIÓN"
    assert fp["group"] == "D"
    assert fp["quota_id"] == "29"
    assert fp["professor"] == "Torrado Umaña Edinson"
    assert len(fp["slots"]) == 3
    # Debe tener franja jueves 06:00-07:00 en I102
    thursday_slots = [s for s in fp["slots"] if s["day_of_week"] == "JUEVES"]
    assert len(thursday_slots) == 2
    assert any(s["start_time"] == "06:00" and s["classroom_code"] == "I102" for s in thursday_slots)
    assert any(s["start_time"] == "12:00" and s["classroom_code"] == "SCGR3" for s in thursday_slots)
    
    # Reconciliación de nombre truncado: Introducción a la Ingeniería de Sistemas
    intro = courses_by_code["0193103B"]
    assert intro["raw_name"] == "INTRODUCCIÓN A LA INGENIERIA DE SI"
    assert intro["name"] == "INTRODUCCIÓN A LA INGENIERIA DE SISTEMAS"
    assert intro["professor"] == "Meza Navarro Yessika Johanna"
    assert intro["slots"][0]["day_of_week"] == "MIÉRCOLES"
    assert intro["slots"][0]["classroom_code"] == "SD1"
