/**
 * Componente Vista "Importar Horario SIA"
 * Carga por arrastrar y soltar con previsualización inteligente de 2 pasos.
 */

import { api } from '../api.js';

export const ImportView = {
  selectedFile: null,
  parsedData: null,

  async render(container) {
    container.innerHTML = `
      <div class="view-header">
        <div>
          <h2 class="view-title">Importar Horario del SIA</h2>
          <p class="view-subtitle">Sube el PDF descargado del portal universitario para sincronizar tus clases</p>
        </div>
      </div>

      <div class="import-container">
        <!-- Zona Drag & Drop -->
        <div class="dropzone" id="pdf-dropzone">
          <input type="file" id="pdf-file-input" accept="application/pdf" class="file-input-hidden" />
          <div class="dropzone-content">
            <div class="dropzone-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="12" y1="18" x2="12" y2="12"></line>
                <line x1="9" y1="15" x2="12" y2="12"></line>
                <line x1="15" y1="15" x2="12" y2="12"></line>
              </svg>
            </div>
            <div class="dropzone-text">
              <span class="dropzone-title">Arrastra tu archivo PDF de horario aquí</span>
              <span class="dropzone-sub">o haz clic para buscar en tu dispositivo</span>
            </div>
            <div class="dropzone-footer">
              <span class="file-format-badge">PDF oficial SIA UFPSO</span>
            </div>
          </div>
        </div>

        <!-- Archivo seleccionado y barra de acciones -->
        <div id="selected-file-bar" class="selected-file-bar hidden">
          <div class="file-info-left">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
              <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            <span id="file-name-label" class="file-name-label">archivo.pdf</span>
            <span id="file-size-label" class="file-size-label">0 KB</span>
          </div>
          <button id="btn-clear-file" class="btn btn-ghost btn-sm">Quitar</button>
        </div>

        <!-- Estado de Carga -->
        <div id="import-loading" class="import-loading hidden">
          <div class="spinner"></div>
          <p id="import-loading-text">Analizando estructura del documento SIA...</p>
        </div>

        <!-- Panel de Previsualización -->
        <div id="preview-panel" class="preview-panel hidden">
          <div class="preview-header">
            <div>
              <h3 class="preview-title">Vista Previa de Carga Académica</h3>
              <p class="preview-subtitle">Verifica que tus asignaturas coincidan antes de confirmar la sincronización.</p>
            </div>
            <button id="btn-confirm-import" class="btn btn-primary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              Confirmar e Importar
            </button>
          </div>

          <!-- Metadatos de Estudiante Detectado -->
          <div id="preview-student-meta" class="preview-student-meta"></div>

          <!-- Tabla de Materias Extraídas -->
          <div class="preview-courses-table-wrapper">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Asignatura</th>
                  <th>Gpo</th>
                  <th>Docente</th>
                  <th>Horarios Detectados</th>
                </tr>
              </thead>
              <tbody id="preview-courses-tbody"></tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    this.bindEvents(container);
  },

  bindEvents(container) {
    const dropzone = container.querySelector('#pdf-dropzone');
    const fileInput = container.querySelector('#pdf-file-input');
    const selectedBar = container.querySelector('#selected-file-bar');
    const fileNameLabel = container.querySelector('#file-name-label');
    const fileSizeLabel = container.querySelector('#file-size-label');
    const btnClear = container.querySelector('#btn-clear-file');
    const loading = container.querySelector('#import-loading');
    const previewPanel = container.querySelector('#preview-panel');
    const btnConfirm = container.querySelector('#btn-confirm-import');

    // Click en dropzone abre explorador
    dropzone.addEventListener('click', () => fileInput.click());

    // Drag & drop
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('dropzone--dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dropzone--dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pdf')) {
        this.handleFileSelected(files[0], container);
      } else {
        window.app.showToast('Por favor selecciona un archivo PDF válido.', 'warning');
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelected(e.target.files[0], container);
      }
    });

    btnClear.addEventListener('click', () => {
      this.selectedFile = null;
      this.parsedData = null;
      fileInput.value = '';
      selectedBar.classList.add('hidden');
      previewPanel.classList.add('hidden');
      dropzone.classList.remove('hidden');
    });

    btnConfirm.addEventListener('click', async () => {
      if (!this.selectedFile) return;

      btnConfirm.disabled = true;
      btnConfirm.textContent = 'Guardando en base de datos...';
      loading.classList.remove('hidden');
      container.querySelector('#import-loading-text').textContent = 'Guardando asignaturas y enriqueciendo salones...';

      try {
        const result = await api.uploadSchedulePdf(this.selectedFile);
        window.app.showToast('¡Horario importado y sincronizado con éxito!', 'success');
        
        // Actualizar perfil de estudiante en la app
        if (result.student) {
          window.app.updateStudentHeader(result.student);
        }

        // Navegar automáticamente a la vista de Hoy después de 1 segundo
        setTimeout(() => {
          window.app.switchTab('today');
        }, 1200);

      } catch (err) {
        window.app.showToast(`Error al sincronizar: ${err.message}`, 'error');
        btnConfirm.disabled = false;
        btnConfirm.textContent = 'Confirmar e Importar';
        loading.classList.add('hidden');
      }
    });
  },

  async handleFileSelected(file, container) {
    this.selectedFile = file;

    const dropzone = container.querySelector('#pdf-dropzone');
    const selectedBar = container.querySelector('#selected-file-bar');
    const fileNameLabel = container.querySelector('#file-name-label');
    const fileSizeLabel = container.querySelector('#file-size-label');
    const loading = container.querySelector('#import-loading');
    const previewPanel = container.querySelector('#preview-panel');

    dropzone.classList.add('hidden');
    selectedBar.classList.remove('hidden');
    fileNameLabel.textContent = file.name;
    fileSizeLabel.textContent = `${(file.size / 1024).toFixed(1)} KB`;

    // Paso 1: Parse Preview
    loading.classList.remove('hidden');
    container.querySelector('#import-loading-text').textContent = 'Extrayendo asignaturas y horarios del PDF...';
    previewPanel.classList.add('hidden');

    try {
      const preview = await api.parseSchedulePreview(file);
      this.parsedData = preview;
      loading.classList.add('hidden');
      this.renderPreview(container, preview);
    } catch (err) {
      loading.classList.add('hidden');
      window.app.showToast(`Error al procesar PDF: ${err.message}`, 'error');
    }
  },

  renderPreview(container, preview) {
    const panel = container.querySelector('#preview-panel');
    const metaContainer = container.querySelector('#preview-student-meta');
    const tbody = container.querySelector('#preview-courses-tbody');

    panel.classList.remove('hidden');

    const s = preview.student || {};
    metaContainer.innerHTML = `
      <div class="preview-meta-card">
        <span class="preview-meta-label">Estudiante</span>
        <span class="preview-meta-val">${s.student_name || 'Nombre no detectado'}</span>
      </div>
      <div class="preview-meta-card">
        <span class="preview-meta-label">Código</span>
        <span class="preview-meta-val"><strong>${s.student_code || '---'}</strong></span>
      </div>
      <div class="preview-meta-card">
        <span class="preview-meta-label">Carrera</span>
        <span class="preview-meta-val">${s.career || '---'}</span>
      </div>
      <div class="preview-meta-card">
        <span class="preview-meta-label">Periodo</span>
        <span class="preview-meta-val">${s.academic_period || '---'}</span>
      </div>
    `;

    tbody.innerHTML = (preview.courses || []).map(c => {
      const slotsSummary = (c.slots || []).map(slot => 
        `<span class="slot-mini-badge">${slot.day_of_week.slice(0, 3)} ${slot.start_time}-${slot.end_time} (${slot.classroom_code})</span>`
      ).join(' ');

      return `
        <tr>
          <td><code class="code-badge">${c.full_code}</code></td>
          <td><strong>${c.name}</strong></td>
          <td>${c.group || '-'}</td>
          <td class="text-muted-col">${c.professor || 'Sin asignar'}</td>
          <td>${slotsSummary || '<span class="text-subtle">Sin franja</span>'}</td>
        </tr>
      `;
    }).join('');
  }
};
