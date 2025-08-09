import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { 
  HomeIcon, 
  NewspaperIcon, 
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ClockIcon,
  ChartBarIcon,
  TrophyIcon,
  DocumentIcon,
  CpuChipIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  CogIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline'
import NotificationPanel from './NotificationPanel'
import MobileMenu from './MobileMenu'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'News', href: '/news', icon: NewspaperIcon },
  { name: 'Community', href: '/community', icon: ChatBubbleLeftRightIcon },
  { name: 'Browse', href: '/browse', icon: MagnifyingGlassIcon },
  { name: 'Practice Quiz', href: '/quiz/create', icon: DocumentTextIcon },
  { name: 'History', href: '/history', icon: ClockIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Leaderboard', href: '/leaderboard', icon: TrophyIcon },
  { name: 'Notes', href: '/notes', icon: DocumentIcon },
  { name: 'AI Solver', href: '/ai-solver', icon: CpuChipIcon },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [notificationOpen, setNotificationOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="flex h-screen bg-dark-bg">
      {/* Mobile menu */}
      <MobileMenu 
        open={sidebarOpen} 
        setOpen={setSidebarOpen}
        navigation={navigation}
        user={user}
        onLogout={handleLogout}
      />

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0">
        <div className="flex flex-col flex-grow bg-dark-card border-r border-dark-border pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <Link to="/" className="flex items-center space-x-2">
              <div className="p-1 bg-neon-blue rounded-md">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="black">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5-10-5-10 5z"/>
                </svg>
              </div>
              <span className="text-2xl font-bold text-white">Proshno</span>
            </Link>
          </div>
          <div className="mt-8 flex-grow flex flex-col">
            <nav className="flex-1 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname.startsWith(item.href)
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-200 ${
                      isActive
                        ? 'bg-dark-border text-white'
                        : 'text-gray-300 hover:bg-dark-border hover:text-white'
                    }`}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                )
              })}
              
              {user?.is_admin && (
                <Link
                  to="/admin"
                  className="group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-300 hover:bg-dark-border hover:text-white border-t border-dark-border mt-2 pt-4"
                >
                  <CogIcon className="mr-3 h-5 w-5" />
                  Admin Panel
                </Link>
              )}
            </nav>
            
            <div className="px-2 space-y-1">
              <Link
                to="/pricing"
                className="group flex items-center justify-center px-2 py-3 text-sm font-bold rounded-md bg-neon-blue text-black hover:opacity-90 transition-opacity"
              >
                <svg className="mr-3 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-12v4m-2-2h4m5 4v4m-2-2h4M5 3a2 2 0 00-2 2v1m16 0V5a2 2 0 00-2-2h-1m-4 16l2 2l2-2m-4-4l2 2l2-2m-4 4V3" />
                </svg>
                Upgrade Plan
              </Link>
              <button
                onClick={handleLogout}
                className="group flex items-center w-full px-2 py-2 text-sm font-medium rounded-md text-gray-400 hover:bg-dark-border hover:text-white"
              >
                <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64 flex flex-col flex-1">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 flex-shrink-0 items-center gap-x-4 border-b border-dark-border bg-dark-card px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-400 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1"></div>
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              {/* Notifications */}
              <div className="relative">
                <button
                  type="button"
                  className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-300"
                  onClick={() => setNotificationOpen(!notificationOpen)}
                >
                  <BellIcon className="h-6 w-6" />
                  {/* Notification dot - will be managed by NotificationPanel */}
                </button>
                <NotificationPanel 
                  open={notificationOpen} 
                  setOpen={setNotificationOpen} 
                />
              </div>

              {/* Profile dropdown */}
              <Link to="/profile" className="flex items-center space-x-3">
                <img
                  className="h-10 w-10 rounded-full object-cover border-2 border-neon-blue"
                  src={user?.profile_pic_url}
                  alt={user?.name}
                />
                <span className="hidden sm:block text-white font-semibold">
                  {user?.name}
                </span>
              </Link>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}