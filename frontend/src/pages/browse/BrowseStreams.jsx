import React from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { categoriesAPI } from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'
import Breadcrumb from '../../components/Breadcrumb'

export default function BrowseStreams() {
  const { levelId } = useParams()
  
  const { data: level } = useQuery({
    queryKey: ['level', levelId],
    queryFn: async () => {
      const response = await categoriesAPI.getLevels()
      return response.data.find(l => l.id === parseInt(levelId))
    }
  })

  const { data: streams, isLoading } = useQuery({
    queryKey: ['streams', levelId],
    queryFn: async () => {
      const response = await categoriesAPI.getStreams(levelId)
      return response.data
    }
  })

  const breadcrumbItems = [
    { name: 'Browse', href: '/browse' },
    { name: level?.name || 'Level', href: `/browse/level/${levelId}` }
  ]

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <Breadcrumb items={breadcrumbItems} />
      
      <h1 className="text-3xl font-bold text-gray-100 mb-6">
        Select a Stream for {level?.name}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {streams?.map((stream) => (
          <Link
            key={stream.id}
            to={`/browse/stream/${stream.id}`}
            className="block bg-dark-card p-6 rounded-lg shadow-md border border-dark-border hover:bg-gray-700 transition-colors duration-300"
          >
            <h3 className="text-xl font-semibold text-gray-200 mb-3">{stream.name}</h3>
            <p className="text-sm text-gray-400">Browse institutions for {stream.name}.</p>
          </Link>
        )) || (
          <div className="col-span-full bg-dark-card p-6 rounded-lg text-center">
            <p className="text-gray-300">No streams have been added for this level yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}