import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col items-center justify-center text-center px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white mb-6 animate-fade-in">
          Question Everything. Master Anything.
        </h1>
        <p className="text-lg sm:text-xl text-gray-300 mb-10 max-w-2xl mx-auto animate-fade-in">
          Your ultimate resource for board questions, MCQs, and CQs. Prepare smarter, not harder.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in">
          {!user ? (
            <>
              <Link
                to="/auth/login"
                className="bg-sky-600 hover:bg-sky-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition-all duration-300 transform hover:scale-105"
              >
                Login
              </Link>
              <Link
                to="/auth/register"
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition-all duration-300 transform hover:scale-105"
              >
                Register
              </Link>
            </>
          ) : (
            <Link
              to="/dashboard"
              className="bg-neon-blue hover:opacity-90 text-black font-bold py-3 px-8 rounded-lg shadow-lg transition-all duration-300 transform hover:scale-105 glow-effect"
            >
              Go to Dashboard
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}