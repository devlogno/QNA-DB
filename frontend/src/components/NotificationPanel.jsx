import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { formatDistanceToNow } from 'date-fns'

export default function NotificationPanel({ open, setOpen }) {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    if (open) {
      fetchNotifications()
      markAsRead()
    }
  }, [open])

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/api/notifications')
      setNotifications(response.data.notifications)
      setUnreadCount(response.data.unread_count)
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    }
  }

  const markAsRead = async () => {
    try {
      await api.post('/api/notifications/mark-read')
      setUnreadCount(0)
    } catch (error) {
      console.error('Failed to mark notifications as read:', error)
    }
  }

  if (!open) return null

  return (
    <div className="absolute right-0 mt-2 w-80 bg-dark-card border border-dark-border rounded-lg shadow-xl z-20">
      <div className="p-4 font-bold border-b border-dark-border flex justify-between items-center">
        <span>Notifications</span>
        {unreadCount > 0 && (
          <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
            {unreadCount}
          </span>
        )}
      </div>
      <div className="max-h-96 overflow-y-auto">
        {notifications.length > 0 ? (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className="p-4 border-b border-dark-border hover:bg-dark-border cursor-pointer"
              onClick={() => {
                if (notification.link_url) {
                  window.location.href = notification.link_url
                }
                setOpen(false)
              }}
            >
              <p className="text-sm text-gray-200">{notification.message}</p>
              <p className="text-xs text-gray-500 mt-1">
                {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
              </p>
            </div>
          ))
        ) : (
          <p className="text-center text-gray-400 p-4">No notifications yet.</p>
        )}
      </div>
    </div>
  )
}