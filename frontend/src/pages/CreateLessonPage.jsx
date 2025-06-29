import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, 
  Plus, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Languages,
  Users,
  Link as LinkIcon
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { lessonsAPI, apiUtils } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function CreateLessonPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  const [formData, setFormData] = useState({
    meeting_url: '',
    lesson_type: 'chinese',
    student_level: 'beginner'
  })

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const validateForm = () => {
    if (!formData.meeting_url.trim()) {
      setError('URL встречи обязателен для заполнения')
      return false
    }

    // Базовая валидация URL
    if (!formData.meeting_url.match(/^https?:\/\/.+/)) {
      setError('Введите корректный URL встречи (должен начинаться с http:// или https://)')
      return false
    }

    // Проверка на поддерживаемые платформы
    const supportedPlatforms = ['meet.google.com', 'zoom.us', 'teams.microsoft.com']
    const isSupported = supportedPlatforms.some(platform => 
      formData.meeting_url.includes(platform)
    )
    
    if (!isSupported) {
      setError('Поддерживаются только Google Meet, Zoom и Microsoft Teams')
      return false
    }

    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await lessonsAPI.create(formData)
      
      setSuccess('Урок успешно создан! Запись началась.')
      
      // Перенаправляем на страницу урока через 2 секунды
      setTimeout(() => {
        navigate(`/lessons/${response.lesson_id}`)
      }, 2000)
      
    } catch (err) {
      console.error('Failed to create lesson:', err)
      setError(apiUtils.formatError(err))
    } finally {
      setLoading(false)
    }
  }

  const lessonTypes = [
    { value: 'chinese', label: 'Китайский язык', emoji: '🇨🇳' },
    { value: 'english', label: 'Английский язык', emoji: '🇺🇸' },
    { value: 'spanish', label: 'Испанский язык', emoji: '🇪🇸' },
    { value: 'french', label: 'Французский язык', emoji: '🇫🇷' },
    { value: 'german', label: 'Немецкий язык', emoji: '🇩🇪' }
  ]

  const studentLevels = [
    { value: 'beginner', label: 'Начинающий', description: 'Изучает основы языка' },
    { value: 'intermediate', label: 'Средний', description: 'Может вести простые диалоги' },
    { value: 'advanced', label: 'Продвинутый', description: 'Свободно владеет языком' }
  ]

  return (
    <div className="max-w-2xl mx-auto">
      {/* Заголовок */}
      <div className="mb-8">
        <Link 
          to="/" 
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Назад к урокам
        </Link>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Создать новый урок</h1>
        <p className="text-gray-600">
          Настройте параметры урока и начните запись встречи
        </p>
      </div>

      {/* Форма */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL встречи */}
          <div>
            <label htmlFor="meeting_url" className="form-label">
              <LinkIcon className="w-4 h-4 inline mr-2" />
              URL встречи *
            </label>
            <input
              type="url"
              id="meeting_url"
              name="meeting_url"
              value={formData.meeting_url}
              onChange={handleInputChange}
              placeholder="https://meet.google.com/your-meeting-id"
              className="form-input"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              Поддерживаются Google Meet, Zoom и Microsoft Teams
            </p>
          </div>

          {/* Тип урока */}
          <div>
            <label htmlFor="lesson_type" className="form-label">
              <Languages className="w-4 h-4 inline mr-2" />
              Тип урока *
            </label>
            <select
              id="lesson_type"
              name="lesson_type"
              value={formData.lesson_type}
              onChange={handleInputChange}
              className="form-input"
              required
            >
              {lessonTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.emoji} {type.label}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              Выберите язык, который изучается на уроке
            </p>
          </div>

          {/* Уровень студента */}
          <div>
            <label htmlFor="student_level" className="form-label">
              <Users className="w-4 h-4 inline mr-2" />
              Уровень студента *
            </label>
            <div className="space-y-3">
              {studentLevels.map(level => (
                <label key={level.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="student_level"
                    value={level.value}
                    checked={formData.student_level === level.value}
                    onChange={handleInputChange}
                    className="mt-1 w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{level.label}</div>
                    <div className="text-sm text-gray-500">{level.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Уведомления */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <p className="text-green-700">{success}</p>
              </div>
            </div>
          )}

          {/* Информационный блок */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <Clock className="w-5 h-5 text-blue-500 mr-2 mt-0.5" />
              <div className="text-sm text-blue-700">
                <div className="font-medium mb-1">Что произойдет после создания:</div>
                <ul className="list-disc list-inside space-y-1">
                  <li>Бот присоединится к встрече и начнет запись</li>
                  <li>Будет создана транскрипция в реальном времени</li>
                  <li>После окончания встречи начнется AI-обработка</li>
                  <li>Будут сгенерированы учебные материалы и домашнее задание</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Кнопки */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <Link to="/" className="btn-secondary">
              Отмена
            </Link>
            
            <button
              type="submit"
              disabled={loading}
              className="btn-primary min-w-[160px]"
            >
              {loading ? (
                <LoadingSpinner size="sm" text="Создание..." />
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Создать урок
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateLessonPage 