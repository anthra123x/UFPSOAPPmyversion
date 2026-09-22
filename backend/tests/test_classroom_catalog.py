from app.services.classroom_catalog import resolve_classroom

def test_resolve_explicit_classrooms():
    scis = resolve_classroom("SCIS")
    assert scis["category"] == "SALA_COMPUTO"
    assert "Sistemas" in scis["name"]
    assert scis["campus"] == "Sede Central El Algodonal"

    cdpu = resolve_classroom("CDPU")
    assert cdpu["category"] == "DEPORTIVO"
    assert "Polideportivo" in cdpu["name"]

    sd1 = resolve_classroom("SD1")
    assert sd1["category"] == "LABORATORIO"
    assert "Dibujo" in sd1["name"]

def test_resolve_pattern_classrooms():
    i106 = resolve_classroom("I106")
    assert i106["building"] == "Bloque I (Aulas e Ingeniería de Sistemas)"
    assert i106["floor"] == "Piso 1"
    assert "Salón 106" in i106["name"]

    c104 = resolve_classroom("C104")
    assert c104["building"] == "Bloque C (Ciencias Básicas y Matemáticas)"
    assert c104["floor"] == "Piso 1"

    i207 = resolve_classroom("I207")
    assert i207["floor"] == "Piso 2"
