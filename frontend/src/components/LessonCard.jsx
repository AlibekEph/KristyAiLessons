import React from 'react'
import { Link } from 'react-router-dom'
import { 
  Calendar, 
  Clock, 
  User, 
  PlayCircle, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  Loader,
  ArrowRight,
  Book,
  Languages
} from 'lucide-react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

function LessonCard({ lesson }) {
  const getStatusInfo = (status) => {
    const statusMap = {
      recording: {
        label: 'Записывается',
        className: 'status-recording',
        icon: <Loader className="w-3 h-3 animate-spin" />
      },
      transcribing: {
        label: 'Транскрипция',
        className: 'status-transcribing',
        icon: <Clock className="w-3 h-3" />
      },
      processing: {
        label: 'Обработка',
        className: 'status-processing',
        icon: <Loader className="w-3 h-3 animate-spin" />
      },
      completed: {
        label: 'Завершено',
        className: 'status-completed',
        icon: <CheckCircle className="w-3 h-3" />
      },
      failed: {
        label: 'Ошибка',
        className: 'status-failed',
        icon: <AlertCircle className="w-3 h-3" />
      }
    }
    return statusMap[status] || statusMap.recording
  }

  const getLessonTypeInfo = (type) => {
    const typeMap = {
      chinese: {
        label: 'Китайский язык',
        emoji: '🇨🇳',
        color: 'text-red-600'
      },
      english: {
        label: 'Английский язык',
        emoji: '🇺🇸',
        color: 'text-blue-600'
      },
      spanish: {
        label: 'Испанский язык',
        emoji: '🇪🇸',
        color: 'text-yellow-600'
      }
    }
    return typeMap[type] || { label: type, emoji: '🌐', color: 'text-gray-600' }
  }

  const getLevelInfo = (level) => {
    const levelMap = {
      beginner: { label: 'Начинающий', color: 'bg-green-100 text-green-800' },
      intermediate: { label: 'Средний', color: 'bg-yellow-100 text-yellow-800' },
      advanced: { label: 'Продвинутый', color: 'bg-red-100 text-red-800' }
    }
    return levelMap[level] || { label: level, color: 'bg-gray-100 text-gray-800' }
  }

  const statusInfo = getStatusInfo(lesson.status)
  const typeInfo = getLessonTypeInfo(lesson.lesson_type)
  const levelInfo = getLevelInfo(lesson.student_level)
  
  const createdDate = new Date(lesson.created_at)
  const formattedDate = format(createdDate, 'dd MMMM yyyy, HH:mm', { locale: ru })

  return (
    <div className="card-hover group">
      {/* Заголовок карточки */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
            <Languages className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
              {typeInfo.label}
            </h3>
            <p className="text-sm text-gray-500">
              ID: {lesson.id.split('_')[1]?.substring(0, 8)}...
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={statusInfo.className}>
            {statusInfo.icon}
            {statusInfo.label}
          </span>
        </div>
      </div>

      {/* Информация об уроке */}
      <div className="space-y-3 mb-4">
        {/* Уровень */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Уровень:</span>
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${levelInfo.color}`}>
            {levelInfo.label}
          </span>
        </div>

        {/* Дата создания */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Создан:</span>
          <span className="text-sm text-gray-900 flex items-center">
            <Calendar className="w-4 h-4 mr-1 text-gray-400" />
            {formattedDate}
          </span>
        </div>

        {/* Описание урока */}
        {lesson.description && (
          <div className="pt-2 border-t border-gray-100">
            <p className="text-sm text-gray-600 line-clamp-2">
              {lesson.description}
            </p>
          </div>
        )}
      </div>

      {/* Прогресс */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500">Прогресс обработки</span>
          <span className="text-xs text-gray-500">
            {lesson.status === 'completed' ? '100%' : 
             lesson.status === 'processing' ? '80%' :
             lesson.status === 'transcribing' ? '50%' :
             lesson.status === 'recording' ? '20%' : '0%'}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${
              lesson.status === 'completed' ? 'bg-green-500 w-full' :
              lesson.status === 'processing' ? 'bg-purple-500 w-4/5' :
              lesson.status === 'transcribing' ? 'bg-yellow-500 w-1/2' :
              lesson.status === 'recording' ? 'bg-blue-500 w-1/5' :
              'bg-gray-300 w-0'
            }`}
          />
        </div>
      </div>

      {/* Доступные материалы */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className={`flex items-center space-x-2 p-2 rounded-lg border ${
          lesson.recording_url ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
        }`}>
          <PlayCircle className={`w-4 h-4 ${
            lesson.recording_url ? 'text-green-600' : 'text-gray-400'
          }`} />
          <span className={`text-xs ${
            lesson.recording_url ? 'text-green-700' : 'text-gray-500'
          }`}>
            Запись
          </span>
        </div>
        
        <div className={`flex items-center space-x-2 p-2 rounded-lg border ${
          lesson.materials_id ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
        }`}>
          <FileText className={`w-4 h-4 ${
            lesson.materials_id ? 'text-green-600' : 'text-gray-400'
          }`} />
          <span className={`text-xs ${
            lesson.materials_id ? 'text-green-700' : 'text-gray-500'
          }`}>
            Материалы
          </span>
        </div>
      </div>

      {/* Домашнее задание (если есть) */}
      {lesson.homework && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Book className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-800">Домашнее задание</span>
          </div>
          <p className="text-sm text-blue-700 line-clamp-2">
            {lesson.homework}
          </p>
        </div>
      )}

      {/* Действия */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <Link
          to={`/lessons/${lesson.id}`}
          className="flex items-center space-x-2 text-primary-600 hover:text-primary-700 transition-colors"
        >
          <span className="text-sm font-medium">Подробнее</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </Link>

        {/* Быстрые действия */}
        <div className="flex items-center space-x-1">
          {lesson.status === 'recording' && (
            <button className="p-2 text-gray-400 hover:text-primary-600 transition-colors">
              <Clock className="w-4 h-4" />
            </button>
          )}
          {lesson.recording_url && (
            <button className="p-2 text-gray-400 hover:text-primary-600 transition-colors">
              <PlayCircle className="w-4 h-4" />
            </button>
          )}
          {lesson.materials_id && (
            <button className="p-2 text-gray-400 hover:text-primary-600 transition-colors">
              <FileText className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default LessonCard 