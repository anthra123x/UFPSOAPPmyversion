/**
 * UFPSO Horarios & Gestión Académica
 * Controlador Principal de la Aplicación
 */

import { api, AuthStore } from './api.js';
import { TodayView } from './components/todayView.js';
import { WeekView } from './components/weekView.js';
import { TasksView } from './components/tasksView.js';
import { CampusView } from './components/campusView.js';
import { ImportView } from './components/importView.js';

class App {
  constructor() {
    this.activeTab = 'today';
    this.simulationParams = {
      weekday: null,
      timeSim: null
    };
    this.views = {
      today: TodayView,
      week: WeekView,
      tasks: TasksView,
      campus: CampusView,
      import: ImportView
    };
  }

  async init() {
    this.initTheme();
    this.initClock();
    this.initNavigation();
    this.initAuthModal();
    this.initSimControls();

    // Soporte para parámetros de URL (?tab=week, ?sim=jueves-0615)
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab') || window.location.hash.replace('#', '');
    const simParam = urlParams.get('sim');

    if (simParam) {
      const simSelect = document.getElementById('sim-time-select');
      if (simSelect) {
        simSelect.value = simParam;
        simSelect.dispatchEvent(new Event('change'));
      }
    }

    if (tabParam && this.views[tabParam]) {
      this.activeTab = tabParam;
    }

    // Renderizar pestaña inicial INMEDIATAMENTE (sin bloquear la interfaz)
    this.switchTab(this.activeTab);

    // Comprobar autenticación en segundo plano
    this.checkAuth().catch(err => {
      console.warn('Verificación de sesión:', err.message);
    });
  }

  // --- TEMA (DARK / LIGHT) ---
  initTheme() {
    const savedTheme = localStorage.getItem('ufpso_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeToggleBtn = document.getElementById('btn-theme-toggle');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('ufpso_theme', next);
      });
    }
  }

  // --- RELOJ EN TIEMPO REAL ---
  initClock() {
    const clockEl = document.getElementById('header-live-clock');
    const updateClock = () => {
      if (!clockEl) return;
      if (this.simulationParams.timeSim) {
        clockEl.textContent = `SIM: ${this.simulationParams.timeSim}`;
        clockEl.classList.add('clock--simulated');
      } else {
        const now = new Date();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        const ss = String(now.getSeconds()).padStart(2, '0');
        clockEl.textContent = `${hh}:${mm}:${ss}`;
        clockEl.classList.remove('clock--simulated');
      }
    };
    updateClock();
    setInterval(updateClock, 1000);
  }

  // --- NAVEGACIÓN ENTRE PESTAÑAS ---
  initNavigation() {
    const navButtons = document.querySelectorAll('.nav-tab-btn');
    navButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        if (tab) this.switchTab(tab);
      });
    });

    // Atajos de teclado (1-5)
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
      const keyMap = { '1': 'today', '2': 'week', '3': 'tasks', '4': 'campus', '5': 'import' };
      if (keyMap[e.key]) {
        this.switchTab(keyMap[e.key]);
      }
    });
  }

  switchTab(tabName) {
    if (!this.views[tabName]) return;
    this.activeTab = tabName;

    // Actualizar botones de navegación
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Actualizar vista activa
    const mainContainer = document.getElementById('main-content');
    if (!mainContainer) return;

    mainContainer.innerHTML = '';
    const viewInstance = this.views[tabName];
    viewInstance.render(mainContainer, this.simulationParams);
  }

  // --- AUTENTICACIÓN Y ESTUDIANTE ---
  async checkAuth() {
    const student = AuthStore.getStudent();
    if (student) {
      this.updateStudentHeader(student);
      // Validar token en segundo plano
      api.getMe().catch(() => {});
    } else {
      // Auto-login con el código del usuario de prueba
      try {
        const res = await api.login('0192977');
        if (res?.student) {
          this.updateStudentHeader(res.student);
        }
      } catch (e) {
        console.warn('Auto-login inicial no completado:', e.message);
      }
    }
  }

  updateStudentHeader(student) {
    const codeEl = document.getElementById('student-code-badge');
    const nameEl = document.getElementById('student-name-badge');

    if (codeEl) codeEl.textContent = student.code || '0192977';
    if (nameEl) nameEl.textContent = student.name || student.career || 'Estudiante UFPSO';
  }

  initAuthModal() {
    const modal = document.getElementById('auth-modal');
    const openBtn = document.getElementById('btn-student-profile');
    const closeBtn = document.getElementById('btn-close-auth-modal');
    const form = document.getElementById('form-auth-login');

    if (!modal) return;

    const openModal = () => {
      const current = AuthStore.getStudent();
      const codeInput = document.getElementById('login-student-code');
      const urlInput = document.getElementById('login-server-url');
      if (codeInput && current) {
        codeInput.value = current.code;
      }
      if (urlInput) {
        urlInput.value = localStorage.getItem('ufpso_api_base') || 'http://10.81.48.45:8000/api/v1';
      }
      modal.classList.remove('hidden');
    };

    const closeModal = () => modal.classList.add('hidden');

    openBtn?.addEventListener('click', openModal);
    closeBtn?.addEventListener('click', closeModal);

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const code = document.getElementById('login-student-code').value.trim();
      const pwd = document.getElementById('login-student-pwd').value.trim();
      const serverUrl = document.getElementById('login-server-url')?.value.trim();

      if (serverUrl) {
        const cleanUrl = serverUrl.endsWith('/api/v1') ? serverUrl : `${serverUrl.replace(/\/$/, '')}/api/v1`;
        localStorage.setItem('ufpso_api_base', cleanUrl);
      }

      if (!code) return;

      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Accediendo...';

      try {
        const res = await api.login(code, pwd || null);
        this.updateStudentHeader(res.student);
        closeModal();
        this.showToast(`Bienvenido, ${res.student.name || res.student.code}`, 'success');
        this.switchTab(this.activeTab); // Recargar vista actual
      } catch (err) {
        this.showToast(err.message, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Ingresar / Cambiar';
      }
    });
  }

  // --- CONTROLADOR DE SIMULACIÓN (PARA PRUEBAS) ---
  initSimControls() {
    const simSelect = document.getElementById('sim-time-select');
    if (!simSelect) return;

    simSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      if (!val || val === 'real') {
        this.simulationParams = { weekday: null, timeSim: null };
      } else if (val === 'jueves-0615') {
        // Jueves = 3, 06:15 AM
        this.simulationParams = { weekday: 3, timeSim: '06:15' };
      } else if (val === 'jueves-1130') {
        this.simulationParams = { weekday: 3, timeSim: '11:30' };
      } else if (val === 'lunes-0800') {
        this.simulationParams = { weekday: 0, timeSim: '08:00' };
      } else if (val === 'viernes-1600') {
        this.simulationParams = { weekday: 4, timeSim: '16:00' };
      }

      this.initClock();
      if (this.activeTab === 'today') {
        this.views.today.load(document.getElementById('main-content'), this.simulationParams);
      }
    });
  }

  // --- TOASTS NOTIFICACIONES ---
  showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `
      <span class="toast-msg">${message}</span>
      <button class="toast-close">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast--fading');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

// Instanciar globalmente
window.app = new App();
document.addEventListener('DOMContentLoaded', () => {
  window.app.init();
});
