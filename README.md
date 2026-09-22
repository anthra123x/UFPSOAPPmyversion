# 🎓 UFPSO Horarios & Gestión Académica

[![Descargar APK](https://img.shields.io/badge/Descargar%20APK-Android%20v1.0.0-dc2626?style=for-the-badge&logo=android&logoColor=white)](https://github.com/anthra123x/UFPSOAPPmyversion/releases/latest/download/ufpso-horarios.apk)
[![GitHub Release](https://img.shields.io/github/v/release/anthra123x/UFPSOAPPmyversion?color=10b981&style=for-the-badge)](https://github.com/anthra123x/UFPSOAPPmyversion/releases)
[![Build Status](https://img.shields.io/github/actions/workflow/status/anthra123x/UFPSOAPPmyversion/build-apk.yml?branch=main&style=for-the-badge&label=APK%20Build)](https://github.com/anthra123x/UFPSOAPPmyversion/actions)

Aplicación móvil y web moderna y minimalista para estudiantes de la **Universidad Francisco de Paula Santander Seccional Ocaña (UFPSO)**.

---

## 📱 Descargar e Instalar la App en Android (APK)

Puedes descargar la aplicación directamente a tu teléfono móvil Android:

👉 **[📥 DESCARGAR APK DIRECTO (ufpso-horarios.apk)](https://github.com/anthra123x/UFPSOAPPmyversion/releases/latest/download/ufpso-horarios.apk)**

O explora los paquetes disponibles en **[GitHub Releases](https://github.com/anthra123x/UFPSOAPPmyversion/releases)**.

### 📲 Pasos para instalar en tu celular Android:
1. Abre este enlace desde tu teléfono o descarga el archivo `ufpso-horarios.apk`.
2. Al abrirlo, si el sistema lo solicita, activa el permiso de **"Instalar aplicaciones desconocidas"** para tu navegador (Chrome, Firefox o Descargas).
3. Presiona **Instalar** y ¡listo! Ya puedes acceder a tu horario y salones sin fricción.

---

## 🌟 Características de la Aplicación

### 🖥️ Interfaz Moderna & Minimalista
- **Diseño sin saturación**: Cero tarjetas infladas, sin gradientes morados chillones ni widgets de relleno. Tipografía *Inter* de alta legibilidad con números tabulares (`tabular-nums`).
- **Vista Hoy**: Muestra la clase en curso o la próxima con cuenta regresiva en minutos (`Termina en 45 min` / `Empieza en 20 min`), profesor y ubicación física enriquecida (`Bloque I · Salón 102 · Piso 1`).
- **Vista Semana**: Cuadrícula horaria completa de Lunes a Sábado (06:00 a 22:00) y vista en lista organizada por días.
- **Seguimiento de Cortes UFPSO**: Control de parciales, talleres y quizzes organizados por los 3 cortes académicos (35%, 35%, 30%) con casillas de marcado instantáneo.
- **Directorio de Campus El Algodonal**: Buscador en vivo de salones, salas de cómputo, laboratorios y auditorios con resolución automática de códigos (ej. `I102`, `SCIS`, `CDPU`).
- **Importador de Horario SIA (PDF)**: Carga en dos pasos con previsualización inteligente de carga académica antes de sincronizar.
- **Modos Oscuro y Claro**: Alternador integrado con persistencia local.

### ⚡ Backend & Nube
- **FastAPI**: API asíncrona de alto rendimiento.
- **Neon PostgreSQL**: Base de datos serverless en la nube con SQLAlchemy 2.0 Async.
- **Parser SIA**: Extracción automática de tablas de horario universitario mediante `pdfplumber`.
- **Integración CI/CD**: Compilación automática de APKs en GitHub Actions en cada actualización.

---

## 📁 Estructura del Repositorio

```
UFPSOAPPmyversion/
├── android/                      # Proyecto nativo Android (Gradle + Kotlin)
│   ├── app/                      # Módulo de la app (MainActivity, WebView nativo, recursos)
│   │   ├── src/main/AndroidManifest.xml
│   │   └── src/main/java/com/ufpso/horarios/MainActivity.kt
│   ├── build.gradle.kts
│   └── gradlew                   # Wrapper de Gradle
├── backend/                      # API REST asíncrona en Python
│   ├── app/
│   │   ├── config.py             # Configuración y conexión Neon DB
│   │   ├── database.py           # Conexión SQLAlchemy async
│   │   ├── main.py               # Servidor FastAPI
│   │   ├── models/               # Modelos relacionales
│   │   ├── routers/              # Rutas /api/v1 (auth, schedule, tasks, campus)
│   │   ├── schemas/              # Validación Pydantic V2
│   │   └── services/             # Lógica de negocio y parser PDF
│   ├── requirements.txt          # Dependencias Python
│   └── Dockerfile
├── frontend/                     # Aplicación Web moderna (HTML5, CSS3, ES Modules)
│   ├── index.html
│   ├── css/style.css             # Sistema de diseño minimalista UFPSO
│   └── js/
│       ├── api.js                # Cliente REST
│       ├── app.js                # Controlador principal
│       └── components/           # Vistas (today, week, tasks, campus, import)
├── .github/workflows/
│   └── build-apk.yml             # Workflow de compilación automática del APK
├── start.sh                      # Script de arranque en 1 clic
└── README.md                     # Documentación principal
```

---

## 🚀 Cómo ejecutar en desarrollo local

### 1. Iniciar Servidor (Backend + Frontend Web)
```bash
./start.sh
```
Abre en tu navegador: **http://localhost:8000**

### 2. Probar en Dispositivos en la Misma Red Wi-Fi
Conecta tu celular a la misma red Wi-Fi e ingresa la IP local de tu equipo:
```
http://TU_IP_LOCAL:8000
```

---

## 🧪 Pruebas Automatizadas

```bash
.venv/bin/python -m pytest backend/tests/
```

---

## 📖 Documentación de la API

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📄 Licencia

Desarrollado para la comunidad universitaria de la **Universidad Francisco de Paula Santander Seccional Ocaña (UFPSO)**.
