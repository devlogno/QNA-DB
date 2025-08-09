import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'

// Auth pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'

// Main pages
import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import BrowsePage from './pages/browse/BrowsePage'
import QuizPage from './pages/quiz/QuizPage'
import NewsPage from './pages/NewsPage'
import CommunityPage from './pages/CommunityPage'
import NotesPage from './pages/NotesPage'
import HistoryPage from './pages/HistoryPage'
import AnalyticsPage from './pages/AnalyticsPage'
import LeaderboardPage from './pages/LeaderboardPage'
import ProfilePage from './pages/ProfilePage'
import AIDoubtSolverPage from './pages/AIDoubtSolverPage'
import PricingPage from './pages/PricingPage'

// Admin pages
import AdminDashboard from './pages/admin/AdminDashboard'

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

function AppRoutes() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/register" element={<RegisterPage />} />
      <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />

      {/* Protected routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute user={user}>
          <Layout><DashboardPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/browse/*" element={
        <ProtectedRoute user={user}>
          <Layout><BrowsePage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/quiz/*" element={
        <ProtectedRoute user={user}>
          <Layout><QuizPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/news" element={
        <ProtectedRoute user={user}>
          <Layout><NewsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/community" element={
        <ProtectedRoute user={user}>
          <Layout><CommunityPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/notes" element={
        <ProtectedRoute user={user}>
          <Layout><NotesPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/history/*" element={
        <ProtectedRoute user={user}>
          <Layout><HistoryPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/analytics" element={
        <ProtectedRoute user={user}>
          <Layout><AnalyticsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/leaderboard" element={
        <ProtectedRoute user={user}>
          <Layout><LeaderboardPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute user={user}>
          <Layout><ProfilePage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/ai-solver" element={
        <ProtectedRoute user={user}>
          <Layout><AIDoubtSolverPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/pricing" element={
        <ProtectedRoute user={user}>
          <Layout><PricingPage /></Layout>
        </ProtectedRoute>
      } />

      {/* Admin routes */}
      <Route path="/admin/*" element={
        <AdminRoute user={user}>
          <Layout><AdminDashboard /></Layout>
        </AdminRoute>
      } />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function ProtectedRoute({ children, user }) {
  if (!user) {
    return <Navigate to="/auth/login" replace />
  }
  return children
}

function AdminRoute({ children, user }) {
  if (!user || !user.is_admin) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

export default App