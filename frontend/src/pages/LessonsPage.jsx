import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Plus, 
  Search, 
  Filter, 
  Clock, 
  Users,
  Calendar,
  PlayCircle,
  FileText,
  CheckCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react'
import { lessonsAPI, apiUtils } from '../services/api'
import LessonCard from '../components/LessonCard'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

function LessonsPage() {
  const [lessons, setLessons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [refreshing, setRefreshing] = useState(false)

  // Моковые данные для демонстрации
  const mockLessons = [
    {
      id: 'lesson_1751213948.560986',
      meeting_url: 'https://meet.google.com/hmn-wtbp-myh',
      lesson_type: 'chinese',
      student_level: 'beginner',
      status: 'completed',
      created_at: '2024-12-29T08:32:28.560986Z',
      bot_id: 'bot_123',
      recording_url: 'https://example.com/recording.mp4',
      materials_id: 'materials_456',
      description: 'Урок по изучению базовых фраз китайского языка для начинающих',
      homework: 'Выучить 10 базовых иероглифов и потренировать произношение тонов'
    },
    {
      id: 'lesson_1751213578.408572',
      meeting_url: 'https://meet.google.com/test-lesson-2',
      lesson_type: 'chinese',
      student_level: 'intermediate',
      status: 'processing',
      created_at: '2024-12-29T08:26:18.408572Z',
      bot_id: 'bot_124',
      recording_url: null,
      materials_id: null,
      description: 'Урок по диалогам и разговорной речи для продвинутых учеников',
      homework: null
    },
    {
      id: 'lesson_1751212000.123456',
      meeting_url: 'https://meet.google.com/another-lesson',
      lesson_type: 'chinese',
      student_level: 'advanced',
      status: 'recording',
      created_at: '2024-12-29T08:00:00.123456Z',
      bot_id: 'bot_125',
      recording_url: null,
      materials_id: null,
      description: 'Урок по сложной грамматике и литературным текстам',
      homework: null
    }
  ]

  // Загрузка списка уроков
  const fetchLessons = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Пока используем моковые данные
      // const response = await lessonsAPI.getAll()
      // setLessons(response.lessons || [])
      
      // Имитация загрузки
      await new Promise(resolve => setTimeout(resolve, 800))
      setLessons(mockLessons)
    } catch (err) {
      console.error('Failed to fetch lessons:', err)
      setError(apiUtils.formatError(err))
      setLessons(mockLessons) // Fallback к моковым данным
    } finally {
      setLoading(false)
    }
  }

  // Обновление списка уроков
  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchLessons()
    setRefreshing(false)
  }

  useEffect(() => {
    fetchLessons()
  }, [])

  // Фильтрация уроков
  const filteredLessons = lessons.filter(lesson => {
    const matchesSearch = lesson.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lesson.lesson_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lesson.student_level.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lesson.description?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || lesson.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" text="Загрузка уроков..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и действия */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Уроки</h1>
          <p className="text-gray-600 mt-1">
            Управление записями и обработка онлайн-уроков
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Обновить
          </button>
          <Link to="/lessons/create" className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Создать урок
          </Link>
        </div>
      </div>

      {/* Поиск и фильтры */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Поиск */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по ID, типу урока, уровню..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-10"
            />
          </div>

          {/* Фильтр по статусу */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-input min-w-[140px]"
            >
              <option value="all">Все статусы</option>
              <option value="recording">Запись</option>
              <option value="transcribing">Транскрипция</option>
              <option value="processing">Обработка</option>
              <option value="completed">Завершено</option>
              <option value="failed">Ошибка</option>
            </select>
          </div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-100">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">{lessons.length}</div>
            <div className="text-xs text-gray-500">Всего уроков</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">
              {lessons.filter(l => l.status === 'recording').length}
            </div>
            <div className="text-xs text-gray-500">Записывается</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">
              {lessons.filter(l => l.status === 'processing').length}
            </div>
            <div className="text-xs text-gray-500">Обрабатывается</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">
              {lessons.filter(l => l.status === 'completed').length}
            </div>
            <div className="text-xs text-gray-500">Завершено</div>
          </div>
        </div>
      </div>

      {/* Список уроков */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-red-700">Ошибка загрузки: {error}</p>
          </div>
        </div>
      )}

      {filteredLessons.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Уроки не найдены"
          description={
            searchTerm || statusFilter !== 'all'
              ? "Попробуйте изменить фильтры поиска"
              : "Создайте первый урок, чтобы начать работу"
          }
          action={
            <Link to="/lessons/create" className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              Создать урок
            </Link>
          }
        />
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredLessons.map((lesson) => (
            <LessonCard key={lesson.id} lesson={lesson} />
          ))}
        </div>
      )}
    </div>
  )
}

export default LessonsPage 