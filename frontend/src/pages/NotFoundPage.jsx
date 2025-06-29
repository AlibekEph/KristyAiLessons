import React from 'react'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft, AlertCircle } from 'lucide-react'

function NotFoundPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="mx-auto flex items-center justify-center w-24 h-24 bg-red-100 rounded-full mb-6">
          <AlertCircle className="w-12 h-12 text-red-600" />
        </div>
        
        <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
        
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Страница не найдена
        </h2>
        
        <p className="text-gray-600 mb-8 max-w-md mx-auto">
          К сожалению, запрашиваемая страница не существует или была перемещена. 
          Проверьте правильность адреса или вернитесь на главную страницу.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link 
            to="/" 
            className="btn-primary flex items-center gap-2"
          >
            <Home className="w-4 h-4" />
            На главную
          </Link>
          
          <button 
            onClick={() => window.history.back()} 
            className="btn-secondary flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage 