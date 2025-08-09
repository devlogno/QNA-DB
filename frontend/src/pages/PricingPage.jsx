import React from 'react'

export default function PricingPage() {
  return (
    <div className="max-w-4xl mx-auto text-center">
      <h1 className="text-4xl font-bold text-white mb-4">Choose Your Plan</h1>
      <p className="text-lg text-gray-400 mb-8">
        Unlock unlimited access to all features and accelerate your learning.
      </p>

      <div className="bg-dark-card p-8 rounded-lg shadow-md border border-dark-border">
        <h2 className="text-2xl font-semibold text-blue-400 mb-4">
          Payment Gateway Coming Soon!
        </h2>
        <p className="text-gray-300">
          We are currently working on integrating a secure payment system. 
          Premium subscription plans will be available shortly. Thank you for your patience!
        </p>
      </div>
    </div>
  )
}