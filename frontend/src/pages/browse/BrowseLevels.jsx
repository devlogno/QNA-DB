import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { categoriesAPI } from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'

export default function BrowseLevels() {
  const { data: levels, isLoading } = useQuery({
    queryKey: ['levels'],
    queryFn: async () => {
      const response = await categoriesAPI.getLevels()
      return response.data
    }
  })

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-100 mb-6">Browse Questions</h1>
      <h2 className="text-2xl font-semibold text-gray-200 mb-6">Select a Level:</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {levels?.map((level) => (
          <Link
            key={level.id}
            to={`level/${level.id}`}
            className="block bg-dark-card p-6 rounded-lg shadow-md border border-dark-border hover:bg-gray-700 transition-colors duration-300"
          >
            <h3 className="text-xl font-semibold text-gray-200 mb-3">{level.name}</h3>
            <p className="text-sm text-gray-400">Browse questions for the {level.name} level.</p>
          </Link>
        )) || (
          <div className="col-span-full bg-dark-card p-6 rounded-lg text-center">
            <p className="text-gray-300">No levels have been configured yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}