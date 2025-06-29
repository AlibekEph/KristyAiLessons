import axios from 'axios';

// Конфигурация API клиента
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptors для обработки ошибок
api.interceptors.request.use(
  (config) => {
    // Логируем запросы в development
    if (process.env.NODE_ENV !== 'production') {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    // Логируем ответы в development
    if (process.env.NODE_ENV !== 'production') {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message);
    
    // Обработка специфичных ошибок
    if (error.response?.status === 404) {
      console.warn('🔍 Resource not found');
    } else if (error.response?.status >= 500) {
      console.error('🚨 Server error occurred');
    }
    
    return Promise.reject(error);
  }
);

// API методы для работы с уроками
export const lessonsAPI = {
  // Получить список всех уроков
  async getAll() {
    try {
      // Поскольку у нас нет эндпоинта списка уроков, симулируем его
      // В реальном проекте здесь был бы GET /lessons
      const response = await api.get('/');
      return { lessons: [] }; // Временная заглушка
    } catch (error) {
      throw new Error('Не удалось загрузить список уроков: ' + error.message);
    }
  },

  // Получить урок по ID
  async getById(lessonId) {
    try {
      const response = await api.get(`/lessons/${lessonId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Не удалось загрузить урок ${lessonId}: ` + error.message);
    }
  },

  // Создать новый урок
  async create(lessonData) {
    try {
      const response = await api.post('/lessons/record', lessonData);
      return response.data;
    } catch (error) {
      throw new Error('Не удалось создать урок: ' + error.message);
    }
  },

  // Запустить обработку урока через polling
  async processLesson(lessonId, options = {}) {
    try {
      const payload = {
        lesson_id: lessonId,
        timeout: options.timeout || 3600,
        interval: options.interval || 30,
      };
      const response = await api.post('/lessons/process', payload);
      return response.data;
    } catch (error) {
      throw new Error('Не удалось запустить обработку урока: ' + error.message);
    }
  },

  // Получить транскрипцию урока
  async getTranscript(lessonId) {
    try {
      const response = await api.get(`/lessons/${lessonId}/transcript`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        throw new Error('Транскрипция еще не готова');
      }
      throw new Error('Не удалось загрузить транскрипцию: ' + error.message);
    }
  },

  // Получить учебные материалы урока
  async getMaterials(lessonId) {
    try {
      const response = await api.get(`/lessons/${lessonId}/materials`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        throw new Error('Учебные материалы еще не готовы');
      }
      throw new Error('Не удалось загрузить учебные материалы: ' + error.message);
    }
  },
};

// API методы для отладки
export const debugAPI = {
  // Получить логи API запросов
  async getLogs(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.service) params.append('service', filters.service);
      if (filters.date) params.append('date', filters.date);
      if (filters.limit) params.append('limit', filters.limit);
      
      const response = await api.get(`/debug/api-logs?${params}`);
      return response.data;
    } catch (error) {
      throw new Error('Не удалось загрузить логи: ' + error.message);
    }
  },
};

// Утилиты для работы с API
export const apiUtils = {
  // Проверка доступности API
  async healthCheck() {
    try {
      const response = await api.get('/');
      return response.data.status === 'ok';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  },

  // Форматирование ошибок API
  formatError(error) {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return 'Произошла неизвестная ошибка';
  },

  // Извлечение данных из ответа API
  extractData(response) {
    return response?.data || response;
  },
};

export default api; 