import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  BookOpen, 
  Plus, 
  Home, 
  Activity, 
  Settings, 
  Menu, 
  X,
  Wifi,
  WifiOff
} from 'lucide-react'
import { apiUtils } from '../services/api'

function Layout({ children }) {
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isApiOnline, setIsApiOnline] = useState(null)

  // Проверка доступности API
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const isOnline = await apiUtils.healthCheck()
        setIsApiOnline(isOnline)
      } catch (error) {
        setIsApiOnline(false)
      }
    }

    checkApiHealth()
    
    // Проверяем каждые 30 секунд
    const interval = setInterval(checkApiHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const navigationItems = [
    {
      name: 'Главная',
      href: '/',
      icon: Home,
      current: location.pathname === '/'
    },
    {
      name: 'Создать урок',
      href: '/lessons/create',
      icon: Plus,
      current: location.pathname === '/lessons/create'
    }
  ]

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Шапка */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Логотип и название */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">KristyLessons</h1>
                  <p className="text-xs text-gray-500">Управление уроками</p>
                </div>
              </Link>
            </div>

            {/* Десктопная навигация */}
            <nav className="hidden md:flex space-x-8">
              {navigationItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      item.current
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </nav>

            {/* Статус API и мобильное меню */}
            <div className="flex items-center space-x-4">
              {/* Индикатор статуса API */}
              <div className="flex items-center space-x-2">
                {isApiOnline === null ? (
                  <Activity className="w-4 h-4 text-gray-400 animate-pulse" />
                ) : isApiOnline ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                <span className="hidden sm:block text-xs text-gray-500">
                  {isApiOnline === null ? 'Проверка...' : isApiOnline ? 'Онлайн' : 'Оффлайн'}
                </span>
              </div>

              {/* Мобильное меню кнопка */}
              <button
                onClick={toggleMobileMenu}
                className="md:hidden p-2 rounded-lg text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Мобильная навигация */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigationItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-base font-medium ${
                      item.current
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </header>

      {/* Основной контент */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>

      {/* Подвал */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-sm text-gray-500">
              © 2024 KristyLessonRecords. Система управления онлайн-уроками.
            </div>
            <div className="flex items-center space-x-4 mt-4 md:mt-0">
              <Link
                to="/docs"
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                API Документация
              </Link>
              <Link
                to="/support"
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Поддержка
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout 