/**
 * Componente Vista "Hoy"
 * Enfoque en la clase activa, cuenta regresiva y agenda cronológica del día.
 */

import { api } from '../api.js';

export const TodayView = {
  containerId: 'view-today',
  timerInterval: null,
  autoRefreshInterval: null,
  currentScheduleData: null,

  async render(container, simParams = {}) {
    // Limpiar auto-refresh previo si la vista se vuelve a renderizar
    this.stopAutoRefresh();
    container.innerHTML = `
      <div class="view-header">
        <div>
          <h2 class="view-title">Agenda de Hoy</h2>
          <p class="view-subtitle" id="today-date-str">Cargando horario...</p>
        </div>
        <div class="view-actions">
          <button id="btn-refresh-today" class="btn btn-ghost btn-sm" title="Recargar agenda">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
              <path d="M21 3v5h-5"></path>
              <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
              <path d="M3 21v-5h5"></path>
            </svg>
            Actualizar
          </button>
        </div>
      </div>

      <!-- Hero Card: Clase Activa o Siguiente -->
      <div id="today-hero-container" class="hero-container skeleton-block"></div>

      <!-- Timeline de Clases del Día -->
      <div class="section-title-wrapper">
        <h3 class="section-title">Clases Programadas</h3>
        <span class="badge badge-muted" id="today-classes-count">0 materias</span>
      </div>

      <div id="today-timeline-container" class="timeline-container">
        <!-- Generado dinámicamente -->
      </div>
    `;

    // Bind refresh button
    container.querySelector('#btn-refresh-today')?.addEventListener('click', () => {
      this.load(container, simParams);
    });

    await this.load(container, simParams);
  },

  async load(container, simParams = {}) {
    const heroContainer = container.querySelector('#today-hero-container');
    const timelineContainer = container.querySelector('#today-timeline-container');
    const dateStr = container.querySelector('#today-date-str');
    const countBadge = container.querySelector('#today-classes-count');

    // Reiniciar auto-revalidación en tiempo real (cada 60s, solo en modo real)
    this.stopAutoRefresh();
    const isSimulating = simParams.weekday !== null || simParams.timeSim;
    if (!isSimulating) {
      this.autoRefreshInterval = setInterval(() => {
        this.load(container, simParams).catch(() => {});
      }, 60000);
    } else {
      this.stopAutoRefresh();
    }

    // 1. Mostrar caché instantánea (0ms) si existe y no estamos simulando
    if (!isSimulating) {
      const cached = api.getCachedToday();
      if (cached) {
        this.currentScheduleData = cached;
        countBadge.textContent = `${cached.total_classes} ${cached.total_classes === 1 ? 'clase' : 'clases'}`;
        this.renderHero(heroContainer, cached);
        this.renderTimeline(timelineContainer, cached.classes);
      }
    }

    // 2. Refrescar desde el backend en tiempo real
    try {
      const data = await api.getTodaySchedule(simParams.weekday, simParams.timeSim);
      this.currentScheduleData = data;

      // Actualizar subtítulo con fecha o simulación
      const now = new Date();
      const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
      const formattedDate = now.toLocaleDateString('es-CO', options);
      
      if (isSimulating) {
        dateStr.innerHTML = `<span class="sim-pill">Modo Simulación: ${data.day_name} ${data.current_time}</span>`;
      } else {
        dateStr.textContent = `${data.day_name}, ${formattedDate} · ${data.current_time}`;
      }

      countBadge.textContent = `${data.total_classes} ${data.total_classes === 1 ? 'clase' : 'clases'}`;

      // Renderizar Hero Card
      this.renderHero(heroContainer, data);

      // Renderizar Timeline
      this.renderTimeline(timelineContainer, data.classes);

    } catch (err) {
      if (!this.currentScheduleData) {
        heroContainer.classList.remove('skeleton-block');
        heroContainer.innerHTML = `
          <div class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <div class="empty-title">Aún no hay horario importado</div>
            <p class="empty-desc">Para ver tus clases de hoy, sube tu archivo PDF descargado del portal SIA de la UFPSO.</p>
            <button class="btn btn-primary btn-sm" onclick="window.app.switchTab('import')">
              Importar Horario PDF
            </button>
          </div>
        `;
        timelineContainer.innerHTML = '';
      }
    }
  },

  renderHero(container, data) {
    container.classList.remove('skeleton-block');

    if (data.active_class) {
      const c = data.active_class;
      const remaining = c.minutes_remaining ?? 0;
      container.innerHTML = `
        <div class="hero-card hero-card--active">
          <div class="hero-header">
            <span class="status-indicator status-indicator--live">
              <span class="pulsing-dot"></span> EN CURSO AHORA
            </span>
            <span class="hero-timer">${remaining > 0 ? `Termina en ${remaining} min` : 'Finalizando'}</span>
          </div>
          <div class="hero-body">
            <div class="hero-meta">
              <span class="hero-time">${c.start_time} - ${c.end_time}</span>
              <span class="hero-group">Grupo ${c.group}</span>
            </div>
            <h1 class="hero-subject">${c.subject_name}</h1>
            <div class="hero-footer">
              <div class="location-badge">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <strong>${c.classroom_code}</strong>
                <span>${c.building ? `· ${c.building}` : ''} ${c.floor ? `· Piso ${c.floor}` : ''}</span>
              </div>
              <div class="professor-tag">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <span>${c.professor_name || 'Docente sin asignar'}</span>
              </div>
            </div>
          </div>
        </div>
      `;
    } else if (data.next_class) {
      const c = data.next_class;
      const until = c.minutes_until_start ?? 0;
      const timeMsg = until > 60 
        ? `Empieza en ${Math.floor(until / 60)}h ${until % 60}m`
        : `Empieza en ${until} min`;

      container.innerHTML = `
        <div class="hero-card hero-card--next">
          <div class="hero-header">
            <span class="status-indicator status-indicator--next">
              PRÓXIMA CLASE
            </span>
            <span class="hero-timer">${timeMsg}</span>
          </div>
          <div class="hero-body">
            <div class="hero-meta">
              <span class="hero-time">${c.start_time} - ${c.end_time}</span>
              <span class="hero-group">Grupo ${c.group}</span>
            </div>
            <h1 class="hero-subject">${c.subject_name}</h1>
            <div class="hero-footer">
              <div class="location-badge">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <strong>${c.classroom_code}</strong>
                <span>${c.building ? `· ${c.building}` : ''} ${c.floor ? `· Piso ${c.floor}` : ''}</span>
              </div>
              <div class="professor-tag">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <span>${c.professor_name || 'Docente sin asignar'}</span>
              </div>
            </div>
          </div>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="hero-card hero-card--free">
          <div class="hero-header">
            <span class="status-indicator status-indicator--free">
              LIBRE POR HOY
            </span>
          </div>
          <div class="hero-body">
            <h2 class="hero-subject" style="font-size: 1.15rem; font-weight: 500;">
              ${data.total_classes > 0 ? 'Has completado todas tus clases del día.' : 'No tienes clases programadas para este día.'}
            </h2>
            <p class="hero-free-sub">Aprovecha para adelantar tareas de los cortes o revisar tu horario de la semana.</p>
          </div>
        </div>
      `;
    }
  },

  renderTimeline(container, classes) {
    if (!classes || classes.length === 0) {
      container.innerHTML = `
        <div class="empty-timeline">
          <p>No hay franjas horarias registradas para este día.</p>
        </div>
      `;
      return;
    }

    const itemsHtml = classes.map(c => {
      let statusClass = 'timeline-item--scheduled';
      let statusLabel = 'Programada';
      if (c.status === 'EN_CURSO') {
        statusClass = 'timeline-item--active';
        statusLabel = 'En curso';
      } else if (c.status === 'PROXIMA') {
        statusClass = 'timeline-item--next';
        statusLabel = 'Próxima';
      } else if (c.status === 'FINALIZADA') {
        statusClass = 'timeline-item--finished';
        statusLabel = 'Finalizada';
      }

      return `
        <div class="timeline-item ${statusClass}">
          <div class="timeline-time">
            <span class="time-start">${c.start_time}</span>
            <span class="time-end">${c.end_time}</span>
          </div>
          <div class="timeline-track">
            <div class="timeline-dot"></div>
            <div class="timeline-line"></div>
          </div>
          <div class="timeline-card">
            <div class="timeline-card-header">
              <span class="subject-title">${c.subject_name}</span>
              <span class="status-badge status-badge--${c.status.toLowerCase()}">${statusLabel}</span>
            </div>
            <div class="timeline-card-meta">
              <span class="room-pill">
                <strong>${c.classroom_code}</strong>
                ${c.building ? `· ${c.building}` : ''}
              </span>
              <span class="group-pill">Gpo. ${c.group}</span>
              ${c.professor_name ? `<span class="prof-pill">${c.professor_name}</span>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = itemsHtml;
  },

  stopAutoRefresh() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
      this.autoRefreshInterval = null;
    }
  }
};
