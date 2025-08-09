import React from 'react'
import { Link } from 'react-router-dom'
import { ChevronRightIcon } from '@heroicons/react/24/outline'

export default function Breadcrumb({ items }) {
  return (
    <nav className="text-sm font-medium mb-6" aria-label="Breadcrumb">
      <ol className="list-none p-0 flex flex-wrap items-center">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <ChevronRightIcon className="w-3 h-3 mx-3 text-gray-500" />
            )}
            {index === items.length - 1 ? (
              <span className="text-white font-semibold">{item.name}</span>
            ) : (
              <Link to={item.href} className="text-gray-400 hover:text-white">
                {item.name}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}