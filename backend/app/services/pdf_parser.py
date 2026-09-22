import io
import re
from typing import Dict, Any, List, Union
import pdfplumber
from app.services.classroom_catalog import resolve_classroom

DAY_MAP = {
    "LUNES": 1,
    "MARTES": 2,
    "MIÉRCOLES": 3,
    "MIERCOLES": 3,
    "JUEVES": 4,
    "VIERNES": 5,
    "SÁBADO": 6,
    "SABADO": 6
}

def parse_sia_schedule_pdf(pdf_source: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    Parsea el PDF oficial de horario emitido por el SIA de la UFPSO.
    Acepta una ruta de archivo (str), bytes en memoria o BytesIO.
    """
    file_obj = io.BytesIO(pdf_source) if isinstance(pdf_source, bytes) else pdf_source
    
    with pdfplumber.open(file_obj) as pdf:
        if not pdf.pages:
            raise ValueError("El archivo PDF del horario está vacío.")
            
        first_page = pdf.pages[0]
        full_text = first_page.extract_text() or ""
        
        # 1. Extracción de metadatos de cabecera
        header_data = _extract_header_metadata(full_text)
        
        # 2. Extracción de tablas estructuradas
        tables = first_page.extract_tables()
        if not tables or len(tables) == 0:
            raise ValueError("No se encontraron tablas de horario en el documento PDF.")
            
        schedule_table = tables[0]
        prof_tables = tables[1:] if len(tables) > 1 else []
        
        # 3. Mapeo de docentes y nombres completos de materias
        professors_map = _extract_professors_map(prof_tables)
        
        # 4. Procesamiento de filas de la tabla de horario
        courses = _parse_schedule_table(schedule_table, professors_map)
        
        return {
            "student": header_data,
            "professors_found": len(professors_map),
            "courses_count": len(courses),
            "courses": courses
        }

def _extract_header_metadata(text: str) -> Dict[str, Any]:
    """Extrae carrera, fecha, periodo académico, nombre, código y pensum."""
    header: Dict[str, Any] = {}
    
    career_match = re.search(r'Horario\s*\n\s*([^\n]+)', text)
    header["career"] = career_match.group(1).strip() if career_match else "Ingeniería De Sistemas - Ocaña"
    
    date_match = re.search(r'Fecha:\s*([\d/]+\s+[\d:]+\s+[AP]M)', text, re.IGNORECASE)
    header["generated_date"] = date_match.group(1).strip() if date_match else None
    
    period_match = re.search(r'(Primer|Segundo)\s+semestre\s+de\s+(\d{4})', text, re.IGNORECASE)
    header["academic_period"] = period_match.group(0).strip() if period_match else "Semestre Académico UFPSO"
    
    name_match = re.search(r'Nombre:\s*([^\n]+)', text)
    header["student_name"] = name_match.group(1).strip() if name_match else ""
    
    code_match = re.search(r'Código:\s*(\d+)', text)
    header["student_code"] = code_match.group(1).strip() if code_match else ""
    
    pensum_match = re.search(r'Pensum:\s*(\d+)', text)
    header["pensum"] = pensum_match.group(1).strip() if pensum_match else ""
    
    return header

def _extract_professors_map(prof_tables: List[List[List[str]]]) -> Dict[str, str]:
    """
    Construye un diccionario {NOMBRE_MATERIA_COMPLETO: NOMBRE_PROFESOR}
    a partir de las tablas de docentes del PDF.
    """
    professors: Dict[str, str] = {}
    for table in prof_tables:
        for row in table:
            if not row or len(row) < 2:
                continue
            # Ignorar encabezados
            materia_col = row[0] or ""
            profesor_col = row[1] or ""
            if "MATERIA" in materia_col.upper() or "PROFESOR" in profesor_col.upper():
                continue
                
            clean_subj = re.sub(r'\s+', ' ', materia_col.strip().upper())
            clean_prof = re.sub(r'\s+', ' ', profesor_col.strip())
            if clean_subj and clean_prof:
                professors[clean_subj] = clean_prof
                
    return professors

def _parse_schedule_table(schedule_table: List[List[str]], professors_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """Procesa las filas del horario y asocia clases, salones enriquecidos y docentes."""
    if not schedule_table or len(schedule_table) < 2:
        return []
        
    headers = [col.strip().upper() if col else "" for col in schedule_table[0]]
    
    # Identificar índices de columnas
    day_indices = []
    for idx, h in enumerate(headers):
        for day_name in DAY_MAP.keys():
            if day_name in h:
                day_indices.append((idx, day_name))
                break
                
    courses = []
    
    for row in schedule_table[1:]:
        if not row or len(row) < 2:
            continue
            
        full_code = (row[0] or "").strip()
        raw_materia = (row[1] or "").strip()
        
        if not full_code or not raw_materia:
            continue
            
        # Separar código de materia y grupo (ej. 0193101D -> 0193101 + D)
        if len(full_code) >= 2 and full_code[-1].isalpha():
            subject_code = full_code[:-1]
            group = full_code[-1].upper()
        else:
            subject_code = full_code
            group = "A"
            
        # Extraer cupo/oferta interna de SIA si está presente (ej. "AJEDREZ (5)")
        quota_match = re.search(r'\(([\d]+)\)$', raw_materia)
        quota_id = quota_match.group(1) if quota_match else None
        clean_materia = re.sub(r'\s*\([\d]+\)$', '', raw_materia).strip()
        
        # Reconciliar nombre completo y profesor
        full_name = clean_materia
        professor_name = None
        
        for p_subj, p_prof in professors_map.items():
            # Comparación por prefijo o coincidencia normalizada
            norm_clean = clean_materia.upper()
            if p_subj.startswith(norm_clean) or norm_clean.startswith(p_subj):
                full_name = p_subj
                professor_name = p_prof
                break
                
        # Extraer franjas horarias por día
        slots = []
        for col_idx, day_name in day_indices:
            if col_idx >= len(row):
                continue
            cell_content = (row[col_idx] or "").strip()
            if not cell_content:
                continue
                
            # Puede contener múltiples franjas separadas por coma
            # ej. "06:00 - 07:00 I102,12:00 - 14:00 SCGR3"
            parts = [p.strip() for p in cell_content.split(",") if p.strip()]
            for part in parts:
                slot_match = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s+([A-Za-z0-9_-]+)', part)
                if slot_match:
                    start_t = slot_match.group(1)
                    end_t = slot_match.group(2)
                    c_code = slot_match.group(3).upper()
                    
                    # Enriquecer salón
                    enriched = resolve_classroom(c_code)
                    
                    slots.append({
                        "day_of_week": day_name,
                        "day_number": DAY_MAP.get(day_name, 1),
                        "start_time": start_t,
                        "end_time": end_t,
                        "classroom_code": c_code,
                        "classroom_name": enriched.get("name"),
                        "building": enriched.get("building"),
                        "floor": enriched.get("floor"),
                        "campus": enriched.get("campus")
                    })
                    
        courses.append({
            "full_code": full_code,
            "subject_code": subject_code,
            "group": group,
            "raw_name": raw_materia,
            "name": full_name,
            "quota_id": quota_id,
            "professor": professor_name,
            "slots": slots
        })
        
    return courses
