import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { 
  ArrowLeft, 
  Calendar, 
  Clock, 
  PlayCircle, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  Loader,
  Book,
  Languages,
  Download,
  RefreshCw,
  Settings,
  ExternalLink
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { lessonsAPI, apiUtils } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function LessonDetailPage() {
  const { lessonId } = useParams()
  
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [processing, setProcessing] = useState(false)

  // Моковые данные для демонстрации
  const mockLesson = {
    id: lessonId,
    meeting_url: 'https://meet.google.com/hmn-wtbp-myh',
    lesson_type: 'chinese',
    student_level: 'beginner',
    status: 'completed',
    created_at: '2024-12-29T08:32:28.560986Z',
    bot_id: 'bot_123',
    recording_url: 'https://example.com/recording.mp4',
    materials_id: 'materials_456',
    description: 'Урок по изучению базовых фраз китайского языка для начинающих. На этом уроке мы изучили основные приветствия, числа от 1 до 10, и базовые фразы вежливости. Студент показал хорошее понимание тонов и правильное произношение большинства звуков.',
    homework: 'Выучить 10 базовых иероглифов: 你好 (привет), 谢谢 (спасибо), 请 (пожалуйста), 对不起 (извините), 再见 (до свидания), 一 到 十 (числа 1-10). Потренировать произношение тонов используя приложение. Записать себя, произнося все изученные фразы, и прислать аудио для проверки.',
    transcript: 'Преподаватель: Добро пожаловать на урок китайского языка! Сегодня мы изучаем базовые приветствия...\n\nСтудент: Спасибо! Я готов начать.\n\nПреподаватель: Отлично! Начнем с самого важного - "你好" (nǐ hǎo)...',
    materials: {
      vocabulary: [
        { chinese: '你好', pinyin: 'nǐ hǎo', translation: 'привет, здравствуйте' },
        { chinese: '谢谢', pinyin: 'xiè xiè', translation: 'спасибо' },
        { chinese: '请', pinyin: 'qǐng', translation: 'пожалуйста' },
        { chinese: '对不起', pinyin: 'duì bù qǐ', translation: 'извините' },
        { chinese: '再见', pinyin: 'zài jiàn', translation: 'до свидания' }
      ],
      grammar_points: [
        'Базовая структура китайского предложения: Подлежащее + Сказуемое + Дополнение',
        'Использование тонов в китайском языке',
        'Формы вежливости и обращения'
      ],
      practice_exercises: [
        'Произнесите каждое новое слово 10 раз с правильными тонами',
        'Составьте диалог, используя все изученные фразы',
        'Напишите иероглифы по памяти'
      ]
    }
  }

  const fetchLesson = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Имитация загрузки
      await new Promise(resolve => setTimeout(resolve, 1000))
      setLesson(mockLesson)
    } catch (err) {
      console.error('Failed to fetch lesson:', err)
      setError(apiUtils.formatError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLesson()
  }, [lessonId])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" text="Загрузка урока..." />
      </div>
    )
  }

  if (!lesson) {
    return (
      <div className="text-center py-12">
        <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Урок не найден</h2>
        <Link to="/" className="btn-primary">Вернуться к урокам</Link>
      </div>
    )
  }

  const createdDate = new Date(lesson.created_at)

  return (
    <div className="max-w-4xl mx-auto">
      {/* Заголовок */}
      <div className="mb-8">
        <Link 
          to="/" 
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Назад к урокам
        </Link>
        
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Languages className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  🇨🇳 Китайский язык
                </h1>
                <p className="text-gray-600">
                  Уровень: {lesson.student_level} | ID: {lesson.id.split('_')[1]?.substring(0, 12)}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <Calendar className="w-4 h-4 mr-1" />
                {format(createdDate, 'dd MMMM yyyy, HH:mm', { locale: ru })}
              </span>
              <span className="status-completed">
                <CheckCircle className="w-3 h-3" />
                Завершено
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Основная информация */}
        <div className="lg:col-span-2 space-y-6">
          {/* Описание урока */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <FileText className="w-5 h-5 mr-2" />
              Описание урока
            </h2>
            <p className="text-gray-700 leading-relaxed">{lesson.description}</p>
          </div>

          {/* Домашнее задание */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Book className="w-5 h-5 mr-2 text-blue-600" />
              Домашнее задание
            </h2>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 leading-relaxed">{lesson.homework}</p>
            </div>
          </div>

          {/* Материалы урока */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Languages className="w-5 h-5 mr-2 text-purple-600" />
              Материалы урока
            </h2>
            
            {/* Словарь */}
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">Новые слова</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                {lesson.materials.vocabulary.map((word, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-3">
                    <div className="text-lg font-semibold text-gray-900">{word.chinese}</div>
                    <div className="text-sm text-gray-600">{word.pinyin}</div>
                    <div className="text-sm text-gray-800">{word.translation}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Грамматика */}
            <div className="mb-6">
              <h3 className="font-medium text-gray-900 mb-3">Грамматика</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {lesson.materials.grammar_points.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>

            {/* Упражнения */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Упражнения</h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                {lesson.materials.practice_exercises.map((exercise, index) => (
                  <li key={index}>{exercise}</li>
                ))}
              </ol>
            </div>
          </div>
        </div>

        {/* Боковая панель */}
        <div className="space-y-6">
          {/* Быстрые действия */}
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Быстрые действия</h3>
            <div className="space-y-3">
              <button className="w-full flex items-center justify-center p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors">
                <PlayCircle className="w-5 h-5 text-blue-600 mr-2" />
                <span className="text-blue-800 font-medium">Посмотреть запись</span>
              </button>
              
              <button className="w-full flex items-center justify-center p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors">
                <Download className="w-5 h-5 text-green-600 mr-2" />
                <span className="text-green-800 font-medium">Скачать материалы</span>
              </button>
            </div>
          </div>

          {/* Информация */}
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Информация</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Статус:</span>
                <span className="status-completed">Завершено</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Bot ID:</span>
                <span className="text-gray-900 font-mono text-xs">{lesson.bot_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Materials ID:</span>
                <span className="text-gray-900 font-mono text-xs">{lesson.materials_id}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LessonDetailPage 