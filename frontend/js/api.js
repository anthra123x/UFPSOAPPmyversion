/**
 * UFPSO Horarios & Gestión Académica - API Client
 * Cliente REST modular de ultra-alta velocidad con soporte Stale-While-Revalidate
 */

export const getApiBase = () => {
  const custom = localStorage.getItem('ufpso_api_base');
  if (custom) return custom.endsWith('/api/v1') ? custom : `${custom.replace(/\/$/, '')}/api/v1`;
  if (typeof window !== 'undefined' && 
      window.location.protocol.startsWith('http') && 
      !window.location.hostname.includes('androidplatform.net')) {
    return `${window.location.origin}/api/v1`;
  }
  // En el fallback empaquetado del APK, la base la inyecta MainActivity vía localStorage
  // (ufpso_api_base) o la configura el usuario en el modal. Este valor es solo el último recurso.
  return 'http://10.80.85.104:8000/api/v1';
};

const TOKEN_STORAGE_KEY = 'ufpso_auth_token';
const STUDENT_STORAGE_KEY = 'ufpso_student_profile';

export const AuthStore = {
  getToken() {
    return localStorage.getItem(TOKEN_STORAGE_KEY) || '';
  },
  setToken(token) {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  },
  getStudent() {
    try {
      const data = localStorage.getItem(STUDENT_STORAGE_KEY);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },
  setStudent(student) {
    if (student) {
      localStorage.setItem(STUDENT_STORAGE_KEY, JSON.stringify(student));
    } else {
      localStorage.removeItem(STUDENT_STORAGE_KEY);
    }
  },
  clear() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(STUDENT_STORAGE_KEY);
  },
  isAuthenticated() {
    return Boolean(this.getToken());
  }
};

async function request(endpoint, options = {}) {
  const base = getApiBase();
  const url = `${base}${endpoint}`;
  const headers = options.headers || {};

  const token = AuthStore.getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Encabezado redundante de resiliencia
  const student = AuthStore.getStudent();
  if (student?.code) {
    headers['X-Student-Code'] = student.code;
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers
  };

  try {
    const response = await fetch(url, config);
    
    if (response.status === 204) {
      return null;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = data?.detail || `Error HTTP ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    console.error(`[API Error] ${endpoint}:`, error.message);
    throw error;
  }
}

export const api = {
  // Autenticación
  async login(code, password = null) {
    const res = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ code: code.trim(), password: password || undefined })
    });
    if (res?.access_token) {
      AuthStore.setToken(res.access_token);
      AuthStore.setStudent(res.student);
    }
    return res;
  },

  async getMe() {
    const student = await request('/auth/me');
    if (student) {
      AuthStore.setStudent(student);
    }
    return student;
  },

  logout() {
    AuthStore.clear();
  },

  // Horarios con Caché Local Instantánea (Stale-While-Revalidate)
  getCachedToday() {
    try {
      const raw = localStorage.getItem('ufpso_cached_today');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  getCachedWeek() {
    try {
      const raw = localStorage.getItem('ufpso_cached_week');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  async getTodaySchedule(weekday = null, timeSim = null) {
    const params = new URLSearchParams();
    if (weekday !== null && weekday !== undefined && weekday !== '') {
      params.append('weekday', weekday);
    }
    if (timeSim) {
      params.append('time_sim', timeSim);
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    const data = await request(`/schedule/today${query}`);
    if (data && (!weekday && !timeSim)) {
      localStorage.setItem('ufpso_cached_today', JSON.stringify(data));
    }
    return data;
  },

  async getWeekSchedule() {
    const data = await request('/schedule/week');
    if (data) {
      localStorage.setItem('ufpso_cached_week', JSON.stringify(data));
    }
    return data;
  },

  async getCurrentEnrollments() {
    return request('/schedule/current');
  },

  async getProfessors() {
    return request('/schedule/professors');
  },

  async parseSchedulePreview(file) {
    const formData = new FormData();
    formData.append('file', file);
    return request('/schedule/parse-preview', {
      method: 'POST',
      body: formData
    });
  },

  async uploadSchedulePdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await request('/schedule/upload-pdf', {
      method: 'POST',
      body: formData
    });
    
    // Guardar automáticamente el token y estudiante emitidos por el backend
    if (res?.access_token) {
      AuthStore.setToken(res.access_token);
    }
    if (res?.student) {
      AuthStore.setStudent(res.student);
    }

    // Invalidar cachés locales para refresco total inmediato
    localStorage.removeItem('ufpso_cached_today');
    localStorage.removeItem('ufpso_cached_week');

    return res;
  },

  // Tareas y Evaluaciones
  async getTasks(isCompleted = null, corte = null) {
    const params = new URLSearchParams();
    if (isCompleted !== null) {
      params.append('is_completed', isCompleted);
    }
    if (corte !== null && corte !== undefined && corte !== '') {
      params.append('corte', corte);
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/tasks/${query}`);
  },

  async createTask(taskData) {
    return request('/tasks/', {
      method: 'POST',
      body: JSON.stringify(taskData)
    });
  },

  async updateTask(taskId, taskData) {
    return request(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(taskData)
    });
  },

  async deleteTask(taskId) {
    return request(`/tasks/${taskId}`, {
      method: 'DELETE'
    });
  },

  // Campus y Salones
  async getClassrooms() {
    return request('/campus/classrooms');
  },

  async resolveClassroom(code) {
    return request(`/campus/resolve/${encodeURIComponent(code)}`);
  }
};
