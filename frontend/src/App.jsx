import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import LessonsPage from './pages/LessonsPage'
import LessonDetailPage from './pages/LessonDetailPage'
import CreateLessonPage from './pages/CreateLessonPage'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Layout>
        <Routes>
          {/* Главная страница со списком уроков */}
          <Route path="/" element={<LessonsPage />} />
          
          {/* Страница создания нового урока */}
          <Route path="/lessons/create" element={<CreateLessonPage />} />
          
          {/* Детальная страница урока */}
          <Route path="/lessons/:lessonId" element={<LessonDetailPage />} />
          
          {/* 404 страница */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
    </div>
  )
}

export default App 