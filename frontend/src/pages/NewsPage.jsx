import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { newsAPI } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import { HandThumbUpIcon, HandThumbDownIcon } from '@heroicons/react/24/outline'
import { HandThumbUpIcon as HandThumbUpSolidIcon, HandThumbDownIcon as HandThumbDownSolidIcon } from '@heroicons/react/24/solid'
import LoadingSpinner from '../components/LoadingSpinner'
import toast from 'react-hot-toast'

export default function NewsPage() {
  const queryClient = useQueryClient()
  
  const { data: articles, isLoading } = useQuery({
    queryKey: ['news'],
    queryFn: async () => {
      const response = await newsAPI.getNews()
      return response.data.articles
    }
  })

  const voteMutation = useMutation({
    mutationFn: ({ articleId, voteType }) => newsAPI.voteNews(articleId, voteType),
    onSuccess: () => {
      queryClient.invalidateQueries(['news'])
    },
    onError: () => {
      toast.error('Failed to vote on article')
    }
  })

  const handleVote = (articleId, voteType) => {
    voteMutation.mutate({ articleId, voteType })
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-100 mb-6">News & Updates</h1>

      <div className="space-y-8 max-w-4xl mx-auto">
        {articles?.length > 0 ? (
          articles.map((article) => (
            <NewsArticle 
              key={article.id} 
              article={article} 
              onVote={handleVote}
            />
          ))
        ) : (
          <div className="bg-dark-card p-6 rounded-lg text-center">
            <p className="text-gray-300">
              No news articles have been posted for you yet. Check back soon!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function NewsArticle({ article, onVote }) {
  const getTargetTag = () => {
    if (article.stream) return article.stream.name
    if (article.level) return article.level.name
    return 'General'
  }

  return (
    <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-border">
      {article.image_url && (
        <img 
          src={article.image_url} 
          alt="News" 
          className="w-full h-64 object-cover rounded-lg mb-4" 
        />
      )}
      
      <div className="flex justify-between items-center mb-2 flex-wrap gap-2">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-100">{article.title}</h2>
        <span className="bg-gray-600 text-white px-2 py-1 rounded-full text-xs font-semibold">
          {getTargetTag()}
        </span>
      </div>
      
      <p className="text-sm text-gray-500 mb-4">
        Posted {formatDistanceToNow(new Date(article.timestamp), { addSuffix: true })}
      </p>
      
      <p className="text-gray-300 whitespace-pre-wrap mb-6">{article.content}</p>

      {/* Voting Section */}
      <div className="flex items-center space-x-4">
        <button
          onClick={() => onVote(article.id, 1)}
          className={`p-2 rounded-full transition-colors duration-200 flex items-center space-x-2 ${
            article.user_vote === 1 
              ? 'text-green-400 bg-gray-700' 
              : 'text-gray-400 hover:bg-gray-700'
          }`}
        >
          {article.user_vote === 1 ? (
            <HandThumbUpSolidIcon className="w-6 h-6" />
          ) : (
            <HandThumbUpIcon className="w-6 h-6" />
          )}
          <span className="font-semibold">{article.upvotes}</span>
        </button>
        
        <button
          onClick={() => onVote(article.id, -1)}
          className={`p-2 rounded-full transition-colors duration-200 flex items-center space-x-2 ${
            article.user_vote === -1 
              ? 'text-red-400 bg-gray-700' 
              : 'text-gray-400 hover:bg-gray-700'
          }`}
        >
          {article.user_vote === -1 ? (
            <HandThumbDownSolidIcon className="w-6 h-6" />
          ) : (
            <HandThumbDownIcon className="w-6 h-6" />
          )}
          <span className="font-semibold">{article.downvotes}</span>
        </button>
      </div>
    </div>
  )
}