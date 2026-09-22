import re
from typing import Dict, Any, Optional

# Catálogo explícito de espacios conocidos en UFPSO
EXPLICIT_CLASSROOMS: Dict[str, Dict[str, str]] = {
    "SCIS": {
        "name": "Sala de Cómputo de Ingeniería de Sistemas",
        "building": "Bloque I (Ingeniería de Sistemas)",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "SALA_COMPUTO",
        "description": "Sala especializada para prácticas de software, redes y programación de Ingeniería de Sistemas."
    },
    "SCGR1": {
        "name": "Sala de Cómputo Gráfico 1",
        "building": "Bloque I (Ingenierías)",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "SALA_COMPUTO",
        "description": "Sala de cómputo con estaciones de trabajo para diseño, modelado y programación."
    },
    "SCGR2": {
        "name": "Sala de Cómputo Gráfico 2",
        "building": "Bloque I (Ingenierías)",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "SALA_COMPUTO",
        "description": "Sala de cómputo para prácticas estudiantiles."
    },
    "SCGR3": {
        "name": "Sala de Cómputo Gráfico 3",
        "building": "Bloque I (Ingenierías)",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "SALA_COMPUTO",
        "description": "Sala de cómputo para prácticas de ingeniería y laboratorios de software."
    },
    "CDPU": {
        "name": "Complejo Deportivo y Polideportivo Universitario",
        "building": "Área Deportiva UFPSO",
        "floor": "Planta Principal",
        "campus": "Sede Central El Algodonal",
        "category": "DEPORTIVO",
        "description": "Canchas múltiples, salón de ajedrez, gimnasio y actividades de bienestar universitario."
    },
    "SD1": {
        "name": "Sala de Dibujo 1",
        "building": "Bloque D / Artes y Diseño",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "LABORATORIO",
        "description": "Sala equipada con mesas de dibujo técnico y arquitectura."
    },
    "SD2": {
        "name": "Sala de Dibujo 2",
        "building": "Bloque D / Artes y Diseño",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "LABORATORIO",
        "description": "Sala equipada para dibujo técnico e ingeniería."
    },
    "AUD1": {
        "name": "Auditorio Principal Fabio Amaya",
        "building": "Edificio Administrativo / Auditorios",
        "floor": "Piso 1",
        "campus": "Sede Central El Algodonal",
        "category": "AUDITORIO",
        "description": "Auditorio institucional para ponencias y eventos magnos."
    }
}

def resolve_classroom(code: str) -> Dict[str, str]:
    """
    Resuelve y enriquece cualquier código de salón de la UFPSO
    (ej. 'I106', 'C104', 'SCGR3', 'CDPU', 'B201').
    """
    clean_code = code.strip().upper()
    
    # 1. Búsqueda directa en catálogo explícito
    if clean_code in EXPLICIT_CLASSROOMS:
        item = EXPLICIT_CLASSROOMS[clean_code].copy()
        item["code"] = clean_code
        return item
    
    # 2. Reconocimiento de patrones regulares de bloques y salones (ej: I106, C104, B205)
    # Formato común UFPSO: Letra de bloque + número de 3 o 4 dígitos
    match = re.match(r"^([A-Z])(\d)(\d{2})$", clean_code)
    if match:
        block_letter = match.group(1)
        floor_digit = match.group(2)
        room_number = match.group(3)
        
        block_names = {
            "A": "Bloque A (Administrativo y Aulas)",
            "B": "Bloque B (Aulas Generales)",
            "C": "Bloque C (Ciencias Básicas y Matemáticas)",
            "D": "Bloque D (Ingeniería y Diseño)",
            "E": "Bloque E (Aulas de Postgrados y Seminarios)",
            "F": "Bloque F (Ciencias Agrarias y Ambientales)",
            "G": "Bloque G (Laboratorios de Ingeniería)",
            "H": "Bloque H (Aulas Generales)",
            "I": "Bloque I (Aulas e Ingeniería de Sistemas)",
            "J": "Bloque J (Aulas Nuevas)",
            "L": "Bloque L (Laboratorios Integrados)"
        }
        
        building = block_names.get(block_letter, f"Bloque {block_letter}")
        floor = f"Piso {floor_digit}"
        classroom_name = f"Salón {floor_digit}{room_number}"
        
        return {
            "code": clean_code,
            "name": f"{classroom_name} ({building})",
            "building": building,
            "floor": floor,
            "campus": "Sede Central El Algodonal",
            "category": "AULA",
            "description": f"Aula de clase situada en el {floor} del {building}."
        }
    
    # 3. Salas de cómputo con nombres abreviados (ej. SC1, SC2, LAB1)
    if clean_code.startswith("SC"):
        return {
            "code": clean_code,
            "name": f"Sala de Cómputo {clean_code}",
            "building": "Bloque I (Sistemas)",
            "floor": "Piso 1",
            "campus": "Sede Central El Algodonal",
            "category": "SALA_COMPUTO",
            "description": "Sala de cómputo académica UFPSO."
        }
    
    if clean_code.startswith("LAB"):
        return {
            "code": clean_code,
            "name": f"Laboratorio {clean_code}",
            "building": "Bloque de Laboratorios",
            "floor": "Piso 1",
            "campus": "Sede Central El Algodonal",
            "category": "LABORATORIO",
            "description": "Laboratorio académico de prácticas."
        }
    
    # Fallback genérico bien formateado
    return {
        "code": clean_code,
        "name": f"Espacio {clean_code}",
        "building": "Campus UFPSO",
        "floor": "N/A",
        "campus": "Sede Central El Algodonal",
        "category": "OTRO",
        "description": f"Espacio académico asignado ({clean_code})."
    }

def get_all_known_classrooms() -> list:
    """Devuelve la lista de espacios físicos registrados explícitamente."""
    res = []
    for code, info in EXPLICIT_CLASSROOMS.items():
        copy_info = info.copy()
        copy_info["code"] = code
        res.append(copy_info)
    return res
