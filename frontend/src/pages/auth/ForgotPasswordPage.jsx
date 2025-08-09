import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { authAPI } from '../../services/api'
import toast from 'react-hot-toast'

export default function ForgotPasswordPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState('email') // email, reset
  const [isLoading, setIsLoading] = useState(false)
  
  const { register, handleSubmit, formState: { errors }, watch } = useForm()

  const handleEmailSubmit = async (data) => {
    setIsLoading(true)
    try {
      await authAPI.forgotPassword(data.email)
      setStep('reset')
      toast.success('OTP sent to your email')
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to send OTP')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetSubmit = async (data) => {
    if (data.password !== data.confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    setIsLoading(true)
    try {
      await authAPI.resetPassword({
        otp: data.otp,
        password: data.password
      })
      toast.success('Password reset successfully!')
      navigate('/auth/login')
    } catch (error) {
      toast.error(error.response?.data?.message || 'Password reset failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-dark-card p-8 rounded-xl shadow-2xl border border-dark-border">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white">Reset Your Password</h1>
            <p className="text-gray-400 mt-2">
              {step === 'email' 
                ? 'Enter your email to receive a verification code.'
                : 'Check your email for the OTP.'
              }
            </p>
          </div>

          {step === 'email' ? (
            <form onSubmit={handleSubmit(handleEmailSubmit)} className="space-y-6">
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  Email Address
                </label>
                <input
                  {...register('email', { 
                    required: 'Email is required',
                    pattern: {
                      value: /^\S+@\S+$/i,
                      message: 'Invalid email address'
                    }
                  })}
                  type="email"
                  className="form-input w-full py-3 px-4"
                  placeholder="your.email@example.com"
                />
                {errors.email && (
                  <p className="text-red-400 text-sm mt-1">{errors.email.message}</p>
                )}
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-3 disabled:opacity-50"
              >
                {isLoading ? 'Sending...' : 'Send Verification Code'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmit(handleResetSubmit)} className="space-y-6">
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  Verification Code
                </label>
                <input
                  {...register('otp', { required: 'OTP is required' })}
                  type="text"
                  className="form-input w-full py-3 px-4 text-center tracking-widest"
                  placeholder="------"
                  maxLength="6"
                />
                {errors.otp && (
                  <p className="text-red-400 text-sm mt-1">{errors.otp.message}</p>
                )}
              </div>
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  New Password
                </label>
                <input
                  {...register('password', { 
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters'
                    }
                  })}
                  type="password"
                  className="form-input w-full py-3 px-4"
                  placeholder="Enter new password"
                />
                {errors.password && (
                  <p className="text-red-400 text-sm mt-1">{errors.password.message}</p>
                )}
              </div>
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  Confirm New Password
                </label>
                <input
                  {...register('confirmPassword', { required: 'Please confirm your password' })}
                  type="password"
                  className="form-input w-full py-3 px-4"
                  placeholder="Confirm new password"
                />
                {errors.confirmPassword && (
                  <p className="text-red-400 text-sm mt-1">{errors.confirmPassword.message}</p>
                )}
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-3 disabled:opacity-50"
              >
                {isLoading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          )}

          <div className="text-center mt-6">
            <Link to="/auth/login" className="text-sm text-sky-400 hover:text-sky-300">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}