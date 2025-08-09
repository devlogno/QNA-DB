import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import LoadingSpinner from '../components/LoadingSpinner'

export default function DashboardPage() {
  const { user } = useAuth()
  
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/api/dashboard/stats')
      return response.data
    }
  })

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-lg text-gray-400 mt-2">
          Here's a snapshot of your progress and available resources.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Questions"
          value={stats?.total_questions || 0}
          subtitle="in your selected streams"
          color="text-white"
        />
        <StatCard
          title="Total MCQs"
          value={stats?.total_mcqs || 0}
          subtitle="Multiple Choice"
          color="text-white"
        />
        <StatCard
          title="Total CQs"
          value={stats?.total_cqs || 0}
          subtitle="Creative Questions"
          color="text-white"
        />
        <StatCard
          title="Study Time"
          value={stats?.study_time || '0h 0m'}
          subtitle="from completed quizzes"
          color="text-red-400"
        />
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ActionCard
          title="Start a Practice Quiz"
          description="Create a custom quiz based on your subjects and chapters to test your knowledge."
          href="/quiz/create"
        />
        <ActionCard
          title="Browse All Questions"
          description="Explore our entire library of questions, filtered by level, stream, and board."
          href="/browse"
        />
      </div>
    </div>
  )
}

function StatCard({ title, value, subtitle, color }) {
  return (
    <div className="bg-dark-card p-6 rounded-xl border border-dark-border">
      <h2 className="text-lg font-semibold text-gray-400 mb-2">{title}</h2>
      <p className={`text-3xl sm:text-4xl font-bold ${color}`}>{value}</p>
      <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

function ActionCard({ title, description, href }) {
  return (
    <Link to={href} className="block group">
      <div className="h-full p-6 sm:p-8 bg-dark-card rounded-xl border border-dark-border transition-all duration-300 group-hover:border-neon-blue group-hover:scale-105 group-hover:shadow-2xl group-hover:glow-effect">
        <h2 className="text-xl sm:text-2xl font-bold mb-2 text-white">{title}</h2>
        <p className="text-gray-400">{description}</p>
      </div>
    </Link>
  )
}