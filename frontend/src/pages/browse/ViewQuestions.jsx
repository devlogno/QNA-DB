import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { questionsAPI, categoriesAPI } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import QuestionCard from '../../components/QuestionCard'
import LoadingSpinner from '../../components/LoadingSpinner'
import Breadcrumb from '../../components/Breadcrumb'

export default function ViewQuestions() {
  const { boardId, questionType } = useParams()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [allQuestions, setAllQuestions] = useState([])
  const [hasMore, setHasMore] = useState(true)

  const isPremium = user?.is_admin || (user?.subscription_expiry && new Date(user.subscription_expiry) > new Date())

  // Get board info for breadcrumb
  const { data: boardInfo } = useQuery({
    queryKey: ['board', boardId],
    queryFn: async () => {
      // This would need a specific endpoint to get board with relationships
      const response = await categoriesAPI.getBoards()
      return response.data.find(b => b.id === parseInt(boardId))
    }
  })

  const { data: questionsData, isLoading, isFetching } = useQuery({
    queryKey: ['questions', boardId, questionType, page],
    queryFn: async () => {
      const response = await questionsAPI.getQuestions({
        board_id: boardId,
        question_type: questionType,
        page
      })
      return response.data
    },
    keepPreviousData: true
  })

  useEffect(() => {
    if (questionsData?.questions) {
      if (page === 1) {
        setAllQuestions(questionsData.questions)
      } else {
        setAllQuestions(prev => [...prev, ...questionsData.questions])
      }
      setHasMore(questionsData.pagination.has_next)
    }
  }, [questionsData, page])

  const loadMore = () => {
    if (hasMore && !isFetching) {
      setPage(prev => prev + 1)
    }
  }

  // Infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (window.innerHeight + document.documentElement.scrollTop >= document.documentElement.offsetHeight - 1000) {
        loadMore()
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [hasMore, isFetching])

  const breadcrumbItems = [
    { name: 'Browse', href: '/browse' },
    // Add more breadcrumb items based on boardInfo when available
    { name: boardInfo?.name || 'Board', href: `/browse/board/${boardId}` },
    { name: questionType, href: `/browse/board/${boardId}/${questionType}` }
  ]

  if (isLoading && page === 1) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <Breadcrumb items={breadcrumbItems} />
      
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-100 mb-6">
        {questionType} Questions for {boardInfo?.name}
      </h1>

      <div className="space-y-8">
        {allQuestions.map((question, index) => (
          <QuestionCard
            key={question.id}
            question={question}
            index={index + 1}
            isPremium={isPremium}
          />
        ))}
      </div>

      {isFetching && page > 1 && (
        <div className="text-center py-8">
          <LoadingSpinner />
          <p className="text-gray-400 mt-2">Loading more questions...</p>
        </div>
      )}

      {!hasMore && allQuestions.length > 0 && (
        <div className="text-center py-8">
          <p className="text-gray-400">You've reached the end of the questions.</p>
        </div>
      )}

      {allQuestions.length === 0 && !isLoading && (
        <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-border text-center">
          <p className="text-xl font-semibold text-gray-200">Coming Soon!</p>
          <p className="text-gray-400 mt-2">
            No {questionType} questions are available for this section yet. Please check back later!
          </p>
        </div>
      )}
    </div>
  )
}