import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { authAPI } from '../../services/api'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState('email') // email, otp, details
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const { register, handleSubmit, formState: { errors }, watch } = useForm()

  const handleEmailSubmit = async (data) => {
    setIsLoading(true)
    try {
      await authAPI.startRegistration({ email: data.email })
      setEmail(data.email)
      setStep('otp')
      toast.success('OTP sent to your email')
    } catch (error) {
      if (error.response?.data?.action === 'redirect') {
        toast.error(error.response.data.message)
        setTimeout(() => navigate('/auth/login'), 2000)
      } else {
        toast.error(error.response?.data?.message || 'Failed to send OTP')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleOTPSubmit = async (data) => {
    setIsLoading(true)
    try {
      await authAPI.verifyOTP(data.otp)
      setStep('details')
      toast.success('OTP verified successfully')
    } catch (error) {
      toast.error(error.response?.data?.message || 'Invalid OTP')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDetailsSubmit = async (data) => {
    if (data.password !== data.confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    setIsLoading(true)
    try {
      await authAPI.completeRegistration({
        name: data.name,
        password: data.password
      })
      toast.success('Registration successful!')
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.response?.data?.message || 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSocialLogin = (provider) => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/${provider}/login`
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-dark-card p-8 rounded-xl shadow-2xl border border-dark-border">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white">Create an Account</h1>
            <p className="text-gray-400 mt-2">
              {step === 'email' && 'Enter your email to get started.'}
              {step === 'otp' && `An OTP was sent to ${email}.`}
              {step === 'details' && 'OTP verified! Please create your account.'}
            </p>
          </div>

          {step === 'email' && (
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
                {isLoading ? 'Sending...' : 'Continue'}
              </button>
            </form>
          )}

          {step === 'otp' && (
            <form onSubmit={handleSubmit(handleOTPSubmit)} className="space-y-6">
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
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-3 disabled:opacity-50"
              >
                {isLoading ? 'Verifying...' : 'Verify OTP'}
              </button>
            </form>
          )}

          {step === 'details' && (
            <form onSubmit={handleSubmit(handleDetailsSubmit)} className="space-y-6">
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  Full Name
                </label>
                <input
                  {...register('name', { required: 'Name is required' })}
                  type="text"
                  className="form-input w-full py-3 px-4"
                  placeholder="Enter your full name"
                />
                {errors.name && (
                  <p className="text-red-400 text-sm mt-1">{errors.name.message}</p>
                )}
              </div>
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  Password
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
                  placeholder="Create a password"
                />
                {errors.password && (
                  <p className="text-red-400 text-sm mt-1">{errors.password.message}</p>
                )}
              </div>
              <div>
                <label className="block text-gray-300 text-sm font-bold mb-2">
                  Confirm Password
                </label>
                <input
                  {...register('confirmPassword', { required: 'Please confirm your password' })}
                  type="password"
                  className="form-input w-full py-3 px-4"
                  placeholder="Confirm your password"
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
                {isLoading ? 'Creating Account...' : 'Complete Registration'}
              </button>
            </form>
          )}

          {step === 'email' && (
            <div className="mt-6">
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-600" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="bg-dark-card px-2 text-gray-500">or register with</span>
                </div>
              </div>
              
              <div className="space-y-3">
                <button
                  onClick={() => handleSocialLogin('google')}
                  className="w-full flex items-center justify-center py-3 px-4 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
                >
                  <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5 mr-3" />
                  <span className="font-semibold text-white">Continue with Google</span>
                </button>
                
                <button
                  onClick={() => handleSocialLogin('facebook')}
                  className="w-full flex items-center justify-center py-3 px-4 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
                >
                  <svg className="w-5 h-5 mr-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v2.385z" />
                  </svg>
                  <span className="font-semibold text-white">Continue with Facebook</span>
                </button>
              </div>
            </div>
          )}

          <div className="text-center mt-6">
            <p className="text-sm text-gray-400">
              Already have an account?{' '}
              <Link to="/auth/login" className="font-semibold text-sky-400 hover:text-sky-300">
                Login here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}