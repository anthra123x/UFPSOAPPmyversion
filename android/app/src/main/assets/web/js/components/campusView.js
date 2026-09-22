/**
 * Componente Vista "Campus & Salones"
 * Directorio y buscador en vivo de aulas, bloques y laboratorios del campus El Algodonal UFPSO.
 */

import { api } from '../api.js';

export const CampusView = {
  classrooms: [],
  activeCategory: 'ALL',
  searchQuery: '',

  async render(container) {
    container.innerHTML = `
      <div class="view-header">
        <div>
          <h2 class="view-title">Directorio de Salones y Campus</h2>
          <p class="view-subtitle">Guía de ubicación en el campus El Algodonal (UFPSO)</p>
        </div>
      </div>

      <!-- Buscador y Filtros -->
      <div class="campus-controls">
        <div class="search-input-wrapper">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" id="campus-search-input" class="search-input" placeholder="Buscar por código (ej. I106, SCIS, C201) o edificio..." />
        </div>

        <div class="segmented-control" id="campus-category-filter">
          <button class="segment-btn active" data-cat="ALL">Todos</button>
          <button class="segment-btn" data-cat="AULA">Aulas</button>
          <button class="segment-btn" data-cat="SALA_COMPUTO">Sistemas</button>
          <button class="segment-btn" data-cat="LABORATORIO">Laboratorios</button>
          <button class="segment-btn" data-cat="AUDITORIO">Auditorios</button>
        </div>
      </div>

      <!-- Resultados de Salones -->
      <div id="classrooms-grid" class="classrooms-grid">
        <!-- Generado dinámicamente -->
      </div>
    `;

    this.bindEvents(container);
    await this.load(container);
  },

  bindEvents(container) {
    const searchInput = container.querySelector('#campus-search-input');
    const catFilter = container.querySelector('#campus-category-filter');
    const grid = container.querySelector('#classrooms-grid');

    searchInput.addEventListener('input', (e) => {
      this.searchQuery = e.target.value.trim().toLowerCase();
      this.renderGrid(grid);
    });

    catFilter.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        catFilter.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeCategory = btn.dataset.cat;
        this.renderGrid(grid);
      });
    });
  },

  async load(container) {
    const grid = container.querySelector('#classrooms-grid');
    try {
      this.classrooms = await api.getClassrooms();
      this.renderGrid(grid);
    } catch (err) {
      grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-title">Error al cargar salones</div>
          <p class="empty-desc">${err.message}</p>
        </div>
      `;
    }
  },

  renderGrid(container) {
    let filtered = [...this.classrooms];

    if (this.activeCategory !== 'ALL') {
      filtered = filtered.filter(c => c.category === this.activeCategory);
    }

    if (this.searchQuery) {
      filtered = filtered.filter(c => 
        c.code.toLowerCase().includes(this.searchQuery) ||
        c.name.toLowerCase().includes(this.searchQuery) ||
        c.building.toLowerCase().includes(this.searchQuery) ||
        (c.description && c.description.toLowerCase().includes(this.searchQuery))
      );
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="empty-search-placeholder">
          <p>No se encontraron espacios que coincidan con la búsqueda "${this.searchQuery}".</p>
        </div>
      `;
      return;
    }

    const html = filtered.map(c => {
      let categoryLabel = 'Aula';
      if (c.category === 'SALA_COMPUTO') categoryLabel = 'Sala Cómputo';
      else if (c.category === 'LABORATORIO') categoryLabel = 'Laboratorio';
      else if (c.category === 'AUDITORIO') categoryLabel = 'Auditorio';

      return `
        <div class="classroom-card">
          <div class="classroom-card-header">
            <span class="classroom-code">${c.code}</span>
            <span class="category-badge category-badge--${c.category.toLowerCase()}">${categoryLabel}</span>
          </div>
          <div class="classroom-name">${c.name}</div>
          <div class="classroom-location">
            <span class="loc-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect>
                <line x1="9" y1="22" x2="9" y2="22.01"></line>
                <line x1="15" y1="22" x2="15" y2="22.01"></line>
              </svg>
              ${c.building}
            </span>
            <span class="loc-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="19" x2="12" y2="5"></line>
                <polyline points="5 12 12 5 19 12"></polyline>
              </svg>
              Piso ${c.floor}
            </span>
          </div>
          ${c.description ? `<p class="classroom-desc">${c.description}</p>` : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = html;
  }
};
