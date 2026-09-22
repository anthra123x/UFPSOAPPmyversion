/**
 * Componente Vista "Tareas & Cortes"
 * Gestión minimalista de parciales, quizzes y entregas divididos por cortes académicos UFPSO.
 */

import { api } from '../api.js';

export const TasksView = {
  currentCorte: null, // null = todos, 1, 2, 3
  hideCompleted: false,
  enrollments: [],
  tasks: [],

  async render(container) {
    container.innerHTML = `
      <div class="view-header">
        <div>
          <h2 class="view-title">Tareas y Evaluaciones</h2>
          <p class="view-subtitle">Seguimiento de parciales, talleres y notas por corte</p>
        </div>
        <div class="view-actions">
          <button id="btn-open-task-modal" class="btn btn-primary btn-sm">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Nueva Entrega
          </button>
        </div>
      </div>

      <!-- Filtros de Corte -->
      <div class="tasks-filter-bar">
        <div class="segmented-control" id="corte-filter">
          <button class="segment-btn active" data-corte="">Todos los Cortes</button>
          <button class="segment-btn" data-corte="1">1° Corte (35%)</button>
          <button class="segment-btn" data-corte="2">2° Corte (35%)</button>
          <button class="segment-btn" data-corte="3">3° Corte (30%)</button>
        </div>

        <label class="toggle-checkbox-label">
          <input type="checkbox" id="chk-hide-completed" />
          <span>Ocultar completadas</span>
        </label>
      </div>

      <!-- Lista de Tareas -->
      <div id="tasks-list-container" class="tasks-list-container">
        <!-- Renderizado dinámico -->
      </div>

      <!-- Modal de Creación de Tarea -->
      <div id="task-modal" class="modal-backdrop hidden">
        <div class="modal-dialog">
          <div class="modal-header">
            <h3 class="modal-title">Agregar Entrega o Evaluación</h3>
            <button class="modal-close-btn" id="btn-close-task-modal">&times;</button>
          </div>
          <form id="form-create-task" class="modal-form">
            <div class="form-group">
              <label class="form-label" for="task-title">Título o descripción corta *</label>
              <input type="text" id="task-title" class="form-input" placeholder="Ej. Primer Parcial, Taller Algoritmos" required />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label" for="task-type">Tipo</label>
                <select id="task-type" class="form-select">
                  <option value="PARCIAL">Parcial</option>
                  <option value="QUIZ">Quiz</option>
                  <option value="TALLER" selected>Taller</option>
                  <option value="TAREA">Tarea</option>
                  <option value="PROYECTO">Proyecto</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label" for="task-corte">Corte Académico</label>
                <select id="task-corte" class="form-select">
                  <option value="1">1° Corte (35%)</option>
                  <option value="2">2° Corte (35%)</option>
                  <option value="3">3° Corte (30%)</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label" for="task-enrollment">Asignatura asociada</label>
              <select id="task-enrollment" class="form-select">
                <option value="">-- General / Sin materia específica --</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="task-due-date">Fecha y hora límite</label>
              <input type="datetime-local" id="task-due-date" class="form-input" />
            </div>

            <div class="modal-actions">
              <button type="button" class="btn btn-ghost" id="btn-cancel-task">Cancelar</button>
              <button type="submit" class="btn btn-primary" id="btn-submit-task">Guardar Entrega</button>
            </div>
          </form>
        </div>
      </div>
    `;

    this.bindEvents(container);
    await this.load(container);
  },

  bindEvents(container) {
    // Filtros de corte
    const corteFilters = container.querySelector('#corte-filter');
    corteFilters.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        corteFilters.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const c = btn.dataset.corte;
        this.currentCorte = c ? parseInt(c, 10) : null;
        this.renderTasksList(container.querySelector('#tasks-list-container'));
      });
    });

    // Ocultar completadas
    const hideChk = container.querySelector('#chk-hide-completed');
    hideChk.addEventListener('change', (e) => {
      this.hideCompleted = e.target.checked;
      this.renderTasksList(container.querySelector('#tasks-list-container'));
    });

    // Modal
    const modal = container.querySelector('#task-modal');
    const btnOpen = container.querySelector('#btn-open-task-modal');
    const btnClose = container.querySelector('#btn-close-task-modal');
    const btnCancel = container.querySelector('#btn-cancel-task');
    const form = container.querySelector('#form-create-task');

    btnOpen.addEventListener('click', () => {
      form.reset();
      modal.classList.remove('hidden');
      container.querySelector('#task-title').focus();
    });

    const closeModal = () => modal.classList.add('hidden');
    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);

    // Enviar formulario de creación
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = container.querySelector('#task-title').value.trim();
      const type = container.querySelector('#task-type').value;
      const corte = parseInt(container.querySelector('#task-corte').value, 10);
      const enrIdVal = container.querySelector('#task-enrollment').value;
      const enrollment_id = enrIdVal ? parseInt(enrIdVal, 10) : null;
      const dueDateVal = container.querySelector('#task-due-date').value;

      if (!title) return;

      const submitBtn = container.querySelector('#btn-submit-task');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Guardando...';

      try {
        await api.createTask({
          title,
          task_type: type,
          corte,
          enrollment_id,
          due_date: dueDateVal ? new Date(dueDateVal).toISOString() : null
        });

        closeModal();
        window.app.showToast('Entrega guardada correctamente', 'success');
        await this.load(container);
      } catch (err) {
        window.app.showToast(`Error al guardar: ${err.message}`, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Guardar Entrega';
      }
    });
  },

  async load(container) {
    const listContainer = container.querySelector('#tasks-list-container');
    const enrollmentSelect = container.querySelector('#task-enrollment');

    try {
      // Cargar asignaturas para el select si no se han cargado
      if (this.enrollments.length === 0) {
        this.enrollments = await api.getCurrentEnrollments().catch(() => []);
        if (enrollmentSelect) {
          this.enrollments.forEach(enr => {
            const opt = document.createElement('option');
            opt.value = enr.id;
            opt.textContent = `${enr.subject_name} (Gpo. ${enr.group})`;
            enrollmentSelect.appendChild(opt);
          });
        }
      }

      this.tasks = await api.getTasks();
      this.renderTasksList(listContainer);
    } catch (err) {
      listContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-title">Sin tareas registradas</div>
          <p class="empty-desc">Crea tus primeros compromisos de clase para llevar el control del semestre.</p>
        </div>
      `;
    }
  },

  renderTasksList(container) {
    let filtered = [...this.tasks];

    if (this.currentCorte !== null) {
      filtered = filtered.filter(t => t.corte === this.currentCorte);
    }

    if (this.hideCompleted) {
      filtered = filtered.filter(t => !t.is_completed);
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="empty-tasks-placeholder">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polyline points="9 11 12 14 22 4"></polyline>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
          </svg>
          <p>No hay entregas pendientes para este filtro.</p>
        </div>
      `;
      return;
    }

    const html = filtered.map(t => {
      const isDone = t.is_completed;
      let dateBadge = '';
      if (t.due_date) {
        const d = new Date(t.due_date);
        const formatted = d.toLocaleDateString('es-CO', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        dateBadge = `<span class="task-date-pill">${formatted}</span>`;
      }

      return `
        <div class="task-row ${isDone ? 'task-row--completed' : ''}" data-id="${t.id}">
          <label class="custom-checkbox">
            <input type="checkbox" class="chk-task-status" ${isDone ? 'checked' : ''} />
            <span class="checkbox-box"></span>
          </label>

          <div class="task-info">
            <div class="task-title-line">
              <span class="task-title-text">${t.title}</span>
              <span class="task-type-badge task-type--${t.task_type.toLowerCase()}">${t.task_type}</span>
              ${t.corte ? `<span class="corte-tag">${t.corte}° Corte</span>` : ''}
            </div>
            <div class="task-meta-line">
              ${t.subject_name ? `<span class="task-subject">${t.subject_name}</span>` : '<span class="task-subject-general">General</span>'}
              ${dateBadge}
            </div>
          </div>

          <button class="btn-delete-task" title="Eliminar tarea">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      `;
    }).join('');

    container.innerHTML = html;

    // Bind checkbox change and delete buttons
    container.querySelectorAll('.task-row').forEach(row => {
      const taskId = parseInt(row.dataset.id, 10);
      const chk = row.querySelector('.chk-task-status');
      const btnDel = row.querySelector('.btn-delete-task');

      chk.addEventListener('change', async () => {
        const isCompleted = chk.checked;
        row.classList.toggle('task-row--completed', isCompleted);
        try {
          await api.updateTask(taskId, { is_completed: isCompleted });
          const target = this.tasks.find(x => x.id === taskId);
          if (target) target.is_completed = isCompleted;
        } catch (err) {
          chk.checked = !isCompleted;
          row.classList.toggle('task-row--completed', !isCompleted);
          window.app.showToast('Error al actualizar estado', 'error');
        }
      });

      btnDel.addEventListener('click', async () => {
        if (confirm('¿Deseas eliminar esta entrega?')) {
          try {
            await api.deleteTask(taskId);
            this.tasks = this.tasks.filter(x => x.id !== taskId);
            row.remove();
            window.app.showToast('Entrega eliminada', 'info');
          } catch (err) {
            window.app.showToast('Error al eliminar', 'error');
          }
        }
      });
    });
  }
};
