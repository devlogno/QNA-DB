import React, { useState } from 'react'
import { BookmarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid'
import { questionsAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function QuestionCard({ 
  question, 
  index, 
  isPremium = false, 
  quizMode = false,
  onAnswerSelect,
  selectedAnswer,
  showSolution = false 
}) {
  const [isSaved, setIsSaved] = useState(question.is_saved)
  const [solutionVisible, setSolutionVisible] = useState(showSolution)
  const [solutionContent, setSolutionContent] = useState('')
  const [cqAnswers, setCqAnswers] = useState({})

  const handleSave = async () => {
    try {
      const response = await questionsAPI.saveQuestion(question.id)
      setIsSaved(response.data.action === 'saved')
      toast.success(response.data.message)
    } catch (error) {
      toast.error('Failed to save question')
    }
  }

  const handleReport = async () => {
    const reason = prompt('Please provide a reason for reporting this question (optional):')
    if (reason === null) return
    
    try {
      const response = await questionsAPI.reportQuestion(question.id, reason)
      toast.success(response.data.message)
    } catch (error) {
      toast.error('Failed to report question')
    }
  }

  const handleMCQOptionClick = async (option) => {
    if (quizMode) {
      onAnswerSelect?.(question.id, option)
      return
    }

    if (solutionVisible) return

    try {
      const response = await questionsAPI.getSolution(question.id)
      setSolutionContent(response.data.html)
      setSolutionVisible(true)
    } catch (error) {
      if (error.response?.status === 403) {
        // Handle upgrade prompt
        toast.error('Upgrade to premium to view solutions')
      }
    }
  }

  const handleCQToggle = async (subQuestion) => {
    if (cqAnswers[subQuestion]) {
      // Toggle visibility
      return
    }

    try {
      const response = await questionsAPI.getCQAnswer(question.id, subQuestion)
      setCqAnswers(prev => ({
        ...prev,
        [subQuestion]: response.data.html
      }))
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Upgrade to premium to view answers')
      }
    }
  }

  return (
    <div className="bg-dark-card p-4 sm:p-6 rounded-xl border border-dark-border relative transition-colors duration-300">
      {!quizMode && (
        <div className="absolute top-4 right-4 flex items-center space-x-2">
          <button
            onClick={handleSave}
            className="text-gray-500 hover:text-yellow-400 transition-colors duration-200"
            title="Save Question"
          >
            {isSaved ? (
              <BookmarkSolidIcon className="w-6 h-6" />
            ) : (
              <BookmarkIcon className="w-6 h-6" />
            )}
          </button>
          <button
            onClick={handleReport}
            className="text-gray-500 hover:text-red-500 transition-colors duration-200"
            title="Report Question"
          >
            <ExclamationTriangleIcon className="w-6 h-6" />
          </button>
        </div>
      )}

      {question.question_type === 'MCQ' ? (
        <MCQQuestion 
          question={question}
          index={index}
          quizMode={quizMode}
          selectedAnswer={selectedAnswer}
          onOptionClick={handleMCQOptionClick}
          solutionVisible={solutionVisible}
          solutionContent={solutionContent}
          isPremium={isPremium}
        />
      ) : (
        <CQQuestion 
          question={question}
          index={index}
          quizMode={quizMode}
          onToggle={handleCQToggle}
          cqAnswers={cqAnswers}
          isPremium={isPremium}
        />
      )}
    </div>
  )
}

function MCQQuestion({ question, index, quizMode, selectedAnswer, onOptionClick, solutionVisible, solutionContent, isPremium }) {
  return (
    <>
      <div className="text-lg font-semibold mb-2 text-gray-200 flex items-start">
        <span className="mr-3 text-gray-500">{index}.</span>
        <div className="flex-1 pr-16">
          {question.question_image_url && (
            <img 
              src={question.question_image_url} 
              alt="Question" 
              className="max-w-full h-auto mb-4 rounded-lg border border-dark-border" 
            />
          )}
          <div className="prose prose-invert max-w-none text-gray-300">
            {question.question_text}
          </div>
        </div>
      </div>

      {!quizMode && question.board && (
        <div className="text-sm text-gray-500 mb-6 ml-8">
          Tag: {question.board.tag || question.board.name.substring(0, 2).toUpperCase()} {question.year % 100}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
        {['A', 'B', 'C', 'D'].map((option) => {
          const optionText = question[`option_${option.toLowerCase()}`]
          const optionImage = question[`option_${option.toLowerCase()}_image_url`]
          
          if (!optionText && !optionImage) return null

          const isSelected = selectedAnswer === option
          const isCorrect = question.correct_answer === option
          const showResult = solutionVisible && !quizMode

          let buttonClasses = "flex items-start w-full text-left p-4 rounded-lg transition-colors duration-200 "
          
          if (quizMode) {
            buttonClasses += isSelected 
              ? "bg-neon-blue text-black border-2 border-neon-blue" 
              : "bg-dark-bg border border-dark-border text-gray-300 hover:border-neon-blue"
          } else if (showResult) {
            if (isCorrect) {
              buttonClasses += "border-green-500/50 bg-green-500/10 text-gray-300"
            } else if (isSelected) {
              buttonClasses += "border-red-500/50 bg-red-500/10 text-gray-300"
            } else {
              buttonClasses += "bg-dark-bg border border-dark-border text-gray-300"
            }
          } else {
            buttonClasses += "bg-dark-bg border border-dark-border text-gray-300 hover:border-neon-blue"
          }

          return (
            <button
              key={option}
              className={buttonClasses}
              onClick={() => onOptionClick(option)}
              disabled={showResult}
            >
              <span className="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded-full border border-current text-sm font-bold mr-4">
                {option}
              </span>
              <div className="flex-1">
                {optionImage && (
                  <img 
                    src={optionImage} 
                    alt={`Option ${option}`} 
                    className="max-w-full h-auto mb-2 rounded-md" 
                  />
                )}
                <span className="prose prose-invert max-w-none">{optionText}</span>
              </div>
            </button>
          )
        })}
      </div>

      {solutionVisible && (
        <div className="mt-6 p-4 bg-dark-bg rounded-lg border border-dark-border">
          <div dangerouslySetInnerHTML={{ __html: solutionContent }} />
        </div>
      )}
    </>
  )
}

function CQQuestion({ question, index, quizMode, onToggle, cqAnswers, isPremium }) {
  const [openAnswers, setOpenAnswers] = useState({})

  const toggleAnswer = (subQuestion) => {
    if (!quizMode) {
      onToggle(subQuestion)
    }
    setOpenAnswers(prev => ({
      ...prev,
      [subQuestion]: !prev[subQuestion]
    }))
  }

  return (
    <>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-yellow-400 mb-2">Stimulus (উদ্দীপক)</h3>
        <div className="text-lg font-semibold text-gray-200 flex items-start">
          <span className="mr-3 text-gray-500">{index}.</span>
          <div className="flex-1 pr-16">
            {question.question_image_url && (
              <img 
                src={question.question_image_url} 
                alt="Question" 
                className="max-w-full h-auto my-2 rounded-lg border border-dark-border" 
              />
            )}
            <div className="prose prose-invert max-w-none text-gray-300">
              {question.question_text}
            </div>
          </div>
        </div>
        {!quizMode && question.board && (
          <div className="text-sm text-gray-500 mt-2 ml-8">
            Tag: {question.board.tag || question.board.name.substring(0, 2).toUpperCase()} {question.year % 100}
          </div>
        )}
      </div>

      <div className="space-y-1 mt-4">
        {['a', 'b', 'c', 'd'].map((char) => {
          const questionText = question[`question_${char}`]
          if (!questionText) return null

          const bengaliChar = { a: 'ক', b: 'খ', c: 'গ', d: 'ঘ' }[char]
          const isOpen = openAnswers[char]

          return (
            <div key={char} className="border-t border-dark-border first:border-t-0">
              <button
                className="flex items-center justify-between w-full text-left p-4 rounded-lg hover:bg-dark-border/50"
                onClick={() => toggleAnswer(char)}
              >
                <span className="font-semibold text-lg text-gray-200">
                  {bengaliChar}. {questionText}
                </span>
                {!quizMode && (
                  <svg 
                    className={`w-6 h-6 text-gray-400 transform transition-transform duration-300 flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </button>
              
              {!quizMode && isOpen && cqAnswers[char] && (
                <div className="px-4 pb-4">
                  <div 
                    className="prose prose-invert max-w-none text-gray-300"
                    dangerouslySetInnerHTML={{ __html: cqAnswers[char] }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </>
  )
}