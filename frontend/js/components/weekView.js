/**
 * Componente Vista "Semana"
 * Visualización completa del horario de Lunes a Sábado en formato agenda y cuadrícula.
 */

import { api } from '../api.js';

export const WeekView = {
  viewMode: 'agenda', // 'agenda' | 'grid'
  currentData: null,

  async render(container) {
    container.innerHTML = `
      <div class="view-header">
        <div>
          <h2 class="view-title">Horario Semanal</h2>
          <p class="view-subtitle" id="week-period-info">Cargando periodo académico...</p>
        </div>
        <div class="view-actions">
          <div class="segmented-control" id="week-view-toggle">
            <button class="segment-btn active" data-mode="agenda">Lista por Días</button>
            <button class="segment-btn" data-mode="grid">Cuadrícula</button>
          </div>
        </div>
      </div>

      <div class="week-stats-bar" id="week-stats-bar">
        <!-- Totales de asignaturas y horas -->
      </div>

      <div id="week-content-container" class="week-content">
        <!-- Renderizado dinámico -->
      </div>
    `;

    // Bind toggle buttons
    const toggleContainer = container.querySelector('#week-view-toggle');
    toggleContainer.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        toggleContainer.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.viewMode = btn.dataset.mode;
        this.renderContent(container.querySelector('#week-content-container'));
      });
    });

    await this.load(container);
  },

  async load(container) {
    const periodInfo = container.querySelector('#week-period-info');
    const statsBar = container.querySelector('#week-stats-bar');
    const contentContainer = container.querySelector('#week-content-container');

    try {
      const data = await api.getWeekSchedule();
      this.currentData = data;

      periodInfo.textContent = `Periodo ${data.period_name || 'Académico Actual'}`;
      statsBar.innerHTML = `
        <div class="stat-item">
          <span class="stat-value">${data.total_subjects}</span>
          <span class="stat-label">Materias inscritas</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">${data.total_weekly_hours}h</span>
          <span class="stat-label">Horas semanales</span>
        </div>
      `;

      this.renderContent(contentContainer);
    } catch (err) {
      contentContainer.innerHTML = `
        <div class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          <div class="empty-title">Sin horario registrado</div>
          <p class="empty-desc">Sube el PDF de tu horario del SIA para consultar tu semana completa.</p>
          <button class="btn btn-primary btn-sm" onclick="window.app.switchTab('import')">
            Importar Horario PDF
          </button>
        </div>
      `;
    }
  },

  renderContent(container) {
    if (!this.currentData) return;

    if (this.viewMode === 'agenda') {
      this.renderAgendaMode(container, this.currentData);
    } else {
      this.renderGridMode(container, this.currentData);
    }
  },

  renderAgendaMode(container, data) {
    const daysOrder = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO'];
    
    // Mapear días existentes
    const daysMap = {};
    (data.days || []).forEach(d => {
      daysMap[d.day_name.toUpperCase()] = d.slots || [];
    });

    const todayIndex = (new Date().getDay() + 6) % 7; // 0=Lunes, 5=Sábado, 6=Domingo
    const dayNames = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO'];

    const html = daysOrder.map((dayName, idx) => {
      const slots = daysMap[dayName] || [];
      const isToday = todayIndex === idx;

      return `
        <div class="day-group-card ${isToday ? 'day-group-card--today' : ''}">
          <div class="day-group-header">
            <div class="day-group-title">
              <span class="day-name">${dayName}</span>
              ${isToday ? '<span class="badge badge-accent">Hoy</span>' : ''}
            </div>
            <span class="day-slots-count">${slots.length} ${slots.length === 1 ? 'clase' : 'clases'}</span>
          </div>

          ${slots.length === 0 
            ? `<div class="day-empty-slot">Sin clases programadas</div>`
            : `<div class="day-slots-list">
                ${slots.map(s => `
                  <div class="week-slot-row">
                    <div class="slot-time-col">
                      <span class="slot-time-range">${s.start_time} - ${s.end_time}</span>
                    </div>
                    <div class="slot-details-col">
                      <div class="slot-title">${s.subject_name}</div>
                      <div class="slot-meta">
                        <span class="room-pill">
                          <strong>${s.classroom_code}</strong>
                          ${s.building ? `· ${s.building}` : ''}
                        </span>
                        <span class="group-pill">Gpo. ${s.group}</span>
                        ${s.professor_name ? `<span class="prof-pill">${s.professor_name}</span>` : ''}
                      </div>
                    </div>
                  </div>
                `).join('')}
               </div>`
          }
        </div>
      `;
    }).join('');

    container.innerHTML = `<div class="days-agenda-grid">${html}</div>`;
  },

  renderGridMode(container, data) {
    const days = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO'];
    const timeSlots = [];
    for (let h = 6; h <= 21; h++) {
      const start = String(h).padStart(2, '0') + ':00';
      const end = String(h + 1).padStart(2, '0') + ':00';
      timeSlots.push({ start, end, label: `${start}` });
    }

    // Indexar slots por día y hora inicio
    const matrix = {};
    days.forEach(d => { matrix[d] = []; });
    (data.days || []).forEach(d => {
      const name = d.day_name.toUpperCase();
      if (matrix[name]) {
        matrix[name] = d.slots || [];
      }
    });

    let headerHtml = `<th class="grid-time-th">Hora</th>`;
    days.forEach(d => {
      headerHtml += `<th>${d}</th>`;
    });

    let rowsHtml = '';
    timeSlots.forEach(t => {
      rowsHtml += `<tr><td class="grid-time-cell">${t.label}</td>`;
      days.forEach(d => {
        // Buscar si hay clase que comience o esté en esta franja
        const matching = matrix[d].filter(s => s.start_time <= t.start && s.end_time > t.start);
        if (matching.length > 0) {
          const item = matching[0];
          // Solo renderizar el contenido en la hora de inicio para evitar repetición
          if (item.start_time === t.start) {
            rowsHtml += `
              <td class="grid-class-cell">
                <div class="grid-chip">
                  <div class="grid-chip-subject">${item.subject_name}</div>
                  <div class="grid-chip-meta">${item.classroom_code} · Gpo ${item.group}</div>
                </div>
              </td>
            `;
          } else {
            rowsHtml += `<td class="grid-class-cell grid-class-cell--span"></td>`;
          }
        } else {
          rowsHtml += `<td class="grid-empty-cell"></td>`;
        }
      });
      rowsHtml += `</tr>`;
    });

    container.innerHTML = `
      <div class="week-grid-wrapper">
        <table class="week-grid-table">
          <thead><tr>${headerHtml}</tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
    `;
  }
};
