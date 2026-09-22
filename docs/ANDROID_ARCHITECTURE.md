# Guía de Arquitectura e Implementación Android - App UFPSO

Este documento contiene la especificación arquitectónica, diseño de componentes y guía de implementación para la aplicación Android nativa de los estudiantes de la **Universidad Francisco de Paula Santander Seccional Ocaña (UFPSO)**.

---

## 1. Filosofía y Reto a Resolver

Las herramientas oficiales de la universidad (portal SIA / Divisist / app institucional) sufren de:
- Caídas frecuentes en horas pico (inicios de semestre y subida de notas).
- Tiempos de carga lentos e interfaces poco intuitivas en pantallas móviles.
- Cero soporte offline: en aulas de la UFPSO (por ejemplo, plantas bajas de Bloque I, Bloque C o laboratorios) la señal móvil puede ser deficiente o inexistente, dejando al estudiante sin acceso a su horario.

**Nuestra solución móvil:**
- **100% Offline-First**: El horario, materias, salones y docentes se guardan en SQLite local mediante Room. La app funciona de forma instantánea sin necesidad de conexión a internet.
- **Importación con 1 Clic**: El estudiante selecciona el PDF descargado del SIA y la app extrae, reconcilia y configura todo automáticamente.
- **UX Moderna y Atractiva**: Diseñada con Jetpack Compose, colores institucionales de la UFPSO (Rojo `#B71C1C` / `#D32F2F`, fondos oscuros elegantes `#121212`, tarjetas glassmorphic, y chips dinámicos con estados de clase).
- **Notificaciones Proactivas**: Recordatorio 15 minutos antes de cada clase indicando salón exacto, bloque y piso.

---

## 2. Stack Tecnológico Android Recomendado

| Capa / Componente | Tecnología Seleccionada | Justificación |
| :--- | :--- | :--- |
| **Lenguaje** | Kotlin 2.0+ | Lenguaje oficial de Android, seguro y conciso. |
| **UI Framework** | Jetpack Compose + Material 3 | Interfaz declarativa moderna, animación fluida y soporte nativo de modo oscuro. |
| **Arquitectura** | MVVM + Clean Architecture | Separación estricta de responsabilidades (UI, Dominio, Datos). |
| **Base de Datos Local** | Room (SQLite) | Soporte offline-first, consultas reactivas con `Flow<List<T>>`. |
| **Cliente HTTP** | Retrofit 2 + OkHttp 3 + Kotlinx.Serialization | Cliente REST de alto rendimiento con interceptor de token JWT. |
| **Inyección de Dependencias** | Hilt (Dagger) o Koin | Manejo limpio del ciclo de vida de ViewModels y Repositorios. |
| **Tareas en Segundo Plano** | WorkManager / AlarmManager | Sincronización periódica y alarmas exactas para las clases. |
| **Navegación** | Jetpack Compose Navigation | Rutas fuertemente tipadas y animaciones de transición. |

---

## 3. Estructura de Paquetes (Clean Architecture)

```
com.ufpso.horarios/
├── data/
│   ├── local/
│   │   ├── AppDatabase.kt
│   │   ├── dao/
│   │   │   ├── StudentDao.kt
│   │   │   ├── SubjectDao.kt
│   │   │   ├── ScheduleSlotDao.kt
│   │   │   └── TaskDao.kt
│   │   └── entities/
│   │       ├── StudentEntity.kt
│   │       ├── SubjectEntity.kt
│   │       ├── ScheduleSlotEntity.kt
│   │       └── TaskEntity.kt
│   ├── remote/
│   │   ├── UfpsoApiService.kt
│   │   ├── AuthInterceptor.kt
│   │   └── dto/
│   │       ├── StudentDto.kt
│   │       ├── EnrollmentDto.kt
│   │       ├── TodayScheduleDto.kt
│   │       └── UploadSummaryDto.kt
│   └── repository/
│       ├── ScheduleRepositoryImpl.kt
│       ├── AuthRepositoryImpl.kt
│       └── TaskRepositoryImpl.kt
├── domain/
│   ├── model/
│   │   ├── Student.kt
│   │   ├── Course.kt
│   │   ├── ScheduleSlot.kt
│   │   ├── TodaySchedule.kt
│   │   └── TaskItem.kt
│   ├── repository/
│   │   ├── ScheduleRepository.kt
│   │   ├── AuthRepository.kt
│   │   └── TaskRepository.kt
│   └── usecase/
│       ├── GetTodayScheduleUseCase.kt
│       ├── GetWeekScheduleUseCase.kt
│       ├── UploadSiaPdfUseCase.kt
│       ├── GetTasksByCorteUseCase.kt
│       └── ToggleTaskCompletionUseCase.kt
├── presentation/
│   ├── theme/
│   │   ├── Color.kt (Rojos UFPSO, Acabados Dark/Light)
│   │   ├── Theme.kt
│   │   └── Type.kt
│   ├── navigation/
│   │   ├── NavGraph.kt
│   │   └── Screen.kt
│   ├── components/
│   │   ├── ActiveClassCard.kt (Tarjeta con cuenta regresiva)
│   │   ├── CourseItemCard.kt
│   │   ├── CampusLocationBadge.kt
│   │   └── GlassmorphicContainer.kt
│   ├── dashboard/
│   │   ├── DashboardScreen.kt
│   │   └── DashboardViewModel.kt
│   ├── week/
│   │   ├── WeekScheduleScreen.kt
│   │   └── WeekScheduleViewModel.kt
│   ├── import_pdf/
│   │   ├── ImportPdfScreen.kt
│   │   └── ImportPdfViewModel.kt
│   ├── tasks/
│   │   ├── TasksScreen.kt
│   │   └── TasksViewModel.kt
│   └── campus/
│       ├── CampusDirectoryScreen.kt
│       └── CampusViewModel.kt
└── worker/
    ├── ClassReminderWorker.kt
    └── ScheduleSyncWorker.kt
```

---

## 4. Contrato de la API Backend para Retrofit

Para la sesión de desarrollo en Android, esta es la interfaz Retrofit que consumirá directamente el backend desarrollado:

```kotlin
package com.ufpso.horarios.data.remote

import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.*

interface UfpsoApiService {

    // --- Autenticación ---
    @POST("api/v1/auth/login")
    async suspend fun login(
        @Body request: StudentLoginRequest
    ): Response<TokenResponseDto>

    @GET("api/v1/auth/me")
    async suspend fun getMe(): Response<StudentDto>

    // --- Importación y Horario ---
    @Multipart
    @POST("api/v1/schedule/upload-pdf")
    suspend fun uploadSchedulePdf(
        @Part file: MultipartBody.Part
    ): Response<ScheduleUploadSummaryDto>

    @Multipart
    @POST("api/v1/schedule/parse-preview")
    suspend fun previewSchedulePdf(
        @Part file: MultipartBody.Part
    ): Response<ParsedScheduleResultDto>

    @GET("api/v1/schedule/today")
    suspend fun getTodaySchedule(
        @Query("weekday") customWeekday: Int? = null,
        @Query("time_sim") customTime: String? = null
    ): Response<TodayScheduleDto>

    @GET("api/v1/schedule/week")
    suspend fun getWeekSchedule(): Response<WeekScheduleDto>

    @GET("api/v1/schedule/current")
    suspend fun getCurrentSchedule(): Response<List<EnrollmentDto>>

    // --- Tareas y Cortes ---
    @GET("api/v1/tasks/")
    suspend fun getTasks(
        @Query("corte") corte: Int? = null,
        @Query("is_completed") isCompleted: Boolean? = null
    ): Response<List<TaskDto>>

    @POST("api/v1/tasks/")
    suspend fun createTask(
        @Body task: CreateTaskRequest
    ): Response<TaskDto>

    @PUT("api/v1/tasks/{id}")
    suspend fun updateTask(
        @Path("id") taskId: Int,
        @Body task: UpdateTaskRequest
    ): Response<TaskDto>

    @DELETE("api/v1/tasks/{id}")
    suspend fun deleteTask(
        @Path("id") taskId: Int
    ): Response<Unit>

    // --- Campus y Salones ---
    @GET("api/v1/campus/resolve/{code}")
    suspend fun resolveClassroom(
        @Path("code") code: String
    ): Response<ClassroomInfoDto>
}
```

---

## 5. Estrategia Offline-First (Patrón Repositorio)

Para garantizar que el estudiante **siempre** tenga acceso a su horario sin importar la cobertura de red:

```kotlin
class ScheduleRepositoryImpl @Inject constructor(
    private val apiService: UfpsoApiService,
    private val subjectDao: SubjectDao,
    private val slotDao: ScheduleSlotDao
) : ScheduleRepository {

    override fun getTodaySchedule(): Flow<Resource<TodaySchedule>> = flow {
        emit(Resource.Loading())

        // 1. Emitir inmediatamente desde la base de datos local (Room)
        val localSlots = slotDao.getSlotsForDay(getTodayDayNumber())
        if (localSlots.isNotEmpty()) {
            emit(Resource.Success(data = localSlots.toTodaySchedule()))
        }

        // 2. Intentar refrescar desde la API en segundo plano
        try {
            val response = apiService.getTodaySchedule()
            if (response.isSuccessful && response.body() != null) {
                val remoteData = response.body()!!
                // Guardar en base de datos local
                slotDao.upsertSlots(remoteData.toEntityList())
                emit(Resource.Success(data = remoteData.toDomain()))
            }
        } catch (e: Exception) {
            // Si no hay red, la UI ya mostró los datos locales de Room sin fallar
            if (localSlots.isEmpty()) {
                emit(Resource.Error(message = "Sin conexión a internet. Importa tu horario para verlo offline."))
            }
        }
    }
}
```

---

## 6. Notificaciones Proactivas (WorkManager)

Configurar un worker que revise periódicamente las franjas horarias del día y lance notificaciones 15 minutos antes de la hora de inicio:

- **Título**: `Próxima clase en 15 minutos`
- **Mensaje**: `Cálculo Diferencial (Grupo C) con Serrano Carvajalino Fabian Alonso`
- **Subtítulo / Acción**: `Salón: Bloque C - Salón 106 (Piso 1, Sede El Algodonal)`

---

## 7. Paleta de Colores UI (Inspirada en UFPSO)

- **Primary**: `#B71C1C` (Rojo Caramelo UFPSO)
- **Primary Variant**: `#D32F2F`
- **Secondary**: `#1E88E5` (Azul Ingeniería)
- **Background Dark**: `#121212` / `#1E1E1E`
- **Surface**: `#1E1E1E` con bordes sutiles `#2C2C2C`
- **Text Primary**: `#FFFFFF`
- **Text Secondary**: `#B0BEC5`
- **Accents**:
  - `EN_CURSO`: `#4CAF50` (Verde esmeralda palpitante)
  - `PROXIMA`: `#FFA000` (Ámbar brillante)
  - `FINALIZADA`: `#757575` (Gris tenue)
