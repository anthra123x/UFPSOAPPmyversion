# 🎓 UFPSO Horarios & Gestión Académica

Plataforma integral y minimalista para estudiantes de la **Universidad Francisco de Paula Santander Seccional Ocaña (UFPSO)**. Permite la importación inteligente del horario desde el portal SIA, visualización en tiempo real de clases y salones enriquecidos (Bloque, Salón, Piso), seguimiento de compromisos académicos por cortes, y directorio predictivo de espacios del campus El Algodonal.

---

## 🌟 Características Principales

### 🖥️ Frontend Moderno & Editorial
- **Diseño limpio y enfocado**: Sin saturación visual, sin gradientes morados genéricos ni tarjetas infladas con sombras excesivas. Interfaz tipográfica de alta legibilidad basada en *Inter* y números tabulares (`tabular-nums`).
- **Vista Hoy**: Resalta la clase activa en curso o la próxima clase con cuenta regresiva en minutos (`Termina en 45 min` / `Empieza en 20 min`), junto con la agenda cronológica del día.
- **Vista Semana**: Cuadrícula horaria completa (Lunes a Sábado de 06:00 a 22:00) y modo agenda por días con conteo de horas semanales.
- **Seguimiento por Cortes UFPSO**: Organización de parciales, talleres y quizzes clasificados por 1° Corte (35%), 2° Corte (35%) y 3° Corte (30%).
- **Directorio de Campus El Algodonal**: Buscador en vivo de aulas, bloques y salas de cómputo con resolución automática de códigos (ej. `I102`, `SCIS`, `CDPU`).
- **Importador de Horario SIA (PDF)**: Arrastrar y soltar con previsualización de 2 pasos para validar materias antes de confirmar la carga.
- **Modos Oscuro y Claro**: Alternador con persistencia en almacenamiento local.
- **Arquitectura Cero-Build**: Construido en HTML5 semántico, CSS3 Vanilla y ES Modules nativos servido directamente por el backend.

### ⚡ Backend de Alto Rendimiento
- **FastAPI**: API asíncrona de baja latencia con documentación automática OpenAPI en `/docs`.
- **Base de Datos en la Nube**: Integración con PostgreSQL serverless (Neon) mediante SQLAlchemy 2.0 Async + asyncpg.
- **Parser Inteligente de PDFs**: Extracción y reconciliación de tablas de horario del sistema SIA institucional (`pdfplumber` + `pypdf`).
- **Catálogo de Salones**: Mapeo y enriquecimiento semántico de códigos de espacio a bloques, pisos y facultades de la UFPSO.
- **Autenticación JWT**: Seguridad con tokens de portador y persistencia de sesión por código estudiantil.

---

## 📁 Estructura del Proyecto

```
apphorario/
├── backend/
│   ├── app/
│   │   ├── config.py             # Configuración central y variables de entorno
│   │   ├── database.py           # Conexión asíncrona a Neon PostgreSQL
│   │   ├── main.py               # Aplicación FastAPI y montaje de frontend
│   │   ├── models/               # Modelos de base de datos (Estudiantes, Materias, Horarios, Tareas)
│   │   ├── routers/              # Endpoints: auth, schedule, tasks, campus
│   │   ├── schemas/              # Validación de datos y DTOs con Pydantic V2
│   │   └── services/             # Lógica de negocio (PDF parser, catálogo salones, schedule)
│   ├── tests/                    # Suite de pruebas unitarias y de integración
│   ├── requirements.txt          # Dependencias Python
│   └── Dockerfile                # Empaquetado para despliegue
├── frontend/
│   ├── index.html                # Estructura principal y navegación
│   ├── css/
│   │   └── style.css             # Sistema de diseño minimalista (variables, temas, componentes)
│   └── js/
│       ├── api.js                # Cliente REST con token JWT
│       ├── app.js                # Controlador principal y simulador
│       └── components/           # Módulos de vistas (today, week, tasks, campus, import)
├── start.sh                      # Script de arranque en 1 clic
└── pytest.ini                    # Configuración de pruebas
```

---

## 🚀 Inicio Rápido (Local)

### 1. Requisitos Previos
- Python 3.10 o superior instalado.

### 2. Configurar Variables de Entorno
Copia el archivo de ejemplo en `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
*(Asegúrate de configurar `DATABASE_URL` con tu cadena de conexión PostgreSQL de Neon o local).*

### 3. Ejecutar el Servidor
Ejecuta el script unificado de inicio:
```bash
./start.sh
```
El script creará automáticamente el entorno virtual `.venv` si no existe, instalará las dependencias necesarias y levantará el servidor en:
👉 **http://localhost:8000**

---

## 📱 Cómo Probar la App en tu Celular / Dispositivo Móvil

La aplicación está diseñada con un diseño 100% responsivo para pantallas móviles. Para abrirla desde tu celular o tablet:

### Método 1: En la misma red Wi-Fi (Recomendado)

1. Conecta tu celular a la **misma red Wi-Fi** donde está tu computador.
2. Consulta la dirección IP local de tu computador. En Linux:
   ```bash
   ip route get 1.1.1.1 | awk '{print $7}'
   # Ejemplo de IP obtenida: 10.81.48.45
   ```
3. En el navegador de tu teléfono (Chrome, Safari o Firefox), ingresa la dirección con el puerto `8000`:
   ```
   http://TU_IP_LOCAL:8000
   # Ejemplo: http://10.81.48.45:8000
   ```
4. *(Opcional)* Si tu sistema tiene firewall activo (UFW), asegúrate de permitir el puerto:
   ```bash
   sudo ufw allow 8000/tcp
   ```

### Método 2: Instalar como Web App en la Pantalla de Inicio
Una vez abras la página en el navegador de tu teléfono:
- **Android (Chrome)**: Pulsa el menú de 3 puntos `⋮` y selecciona **"Agregar a la pantalla principal"** / **"Instalar aplicación"**.
- **iOS (Safari)**: Pulsa el botón de compartir y selecciona **"Agregar al inicio"**.
Tendrás un acceso directo nativo a pantalla completa sin barra de navegador.

### Método 3: Probar fuera de tu casa (Túnel Cloudflare / Ngrok)
Si quieres probar la app cuando estés en la universidad usando datos móviles:
```bash
# Con Cloudflare (rápido, sin registro previo):
npx cloudflared tunnel --url http://localhost:8000
```
Te entregará un enlace HTTPS seguro temporal (ej. `https://xxxx.trycloudflare.com`) para abrir desde cualquier lugar del mundo.

---

## 🧪 Pruebas Automatizadas

Para ejecutar la suite de pruebas unitarias y de integración:
```bash
.venv/bin/python -m pytest backend/tests/
```

---

## 📖 Documentación de la API

FastAPI genera documentación interactiva en tiempo real:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📄 Licencia

Desarrollado para la comunidad universitaria de la **Universidad Francisco de Paula Santander Seccional Ocaña (UFPSO)**.
