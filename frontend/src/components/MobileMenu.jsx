import React from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { Link } from 'react-router-dom'
import { XMarkIcon, CogIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'

export default function MobileMenu({ open, setOpen, navigation, user, onLogout }) {
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50 lg:hidden" onClose={setOpen}>
        <Transition.Child
          as={Fragment}
          enter="transition-opacity ease-linear duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="transition-opacity ease-linear duration-300"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>

        <div className="fixed inset-0 flex">
          <Transition.Child
            as={Fragment}
            enter="transition ease-in-out duration-300 transform"
            enterFrom="-translate-x-full"
            enterTo="translate-x-0"
            leave="transition ease-in-out duration-300 transform"
            leaveFrom="translate-x-0"
            leaveTo="-translate-x-full"
          >
            <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
              <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-dark-card px-6 pb-4">
                <div className="flex h-16 shrink-0 items-center justify-between">
                  <Link to="/" className="flex items-center space-x-2">
                    <div className="p-1 bg-neon-blue rounded-md">
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="black">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5-10-5-10 5z"/>
                      </svg>
                    </div>
                    <span className="text-2xl font-bold text-white">Proshno</span>
                  </Link>
                  <button
                    type="button"
                    className="-m-2.5 p-2.5 text-gray-400"
                    onClick={() => setOpen(false)}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
                <nav className="flex flex-1 flex-col">
                  <ul role="list" className="flex flex-1 flex-col gap-y-7">
                    <li>
                      <ul role="list" className="-mx-2 space-y-1">
                        {navigation.map((item) => (
                          <li key={item.name}>
                            <Link
                              to={item.href}
                              className="group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold text-gray-300 hover:text-white hover:bg-dark-border"
                              onClick={() => setOpen(false)}
                            >
                              <item.icon className="h-6 w-6 shrink-0" />
                              {item.name}
                            </Link>
                          </li>
                        ))}
                        
                        {user?.is_admin && (
                          <li className="border-t border-dark-border pt-2">
                            <Link
                              to="/admin"
                              className="group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold text-gray-300 hover:text-white hover:bg-dark-border"
                              onClick={() => setOpen(false)}
                            >
                              <CogIcon className="h-6 w-6 shrink-0" />
                              Admin Panel
                            </Link>
                          </li>
                        )}
                      </ul>
                    </li>
                    <li className="mt-auto space-y-1">
                      <Link
                        to="/pricing"
                        className="group flex items-center justify-center gap-x-3 rounded-md p-3 text-sm font-bold bg-neon-blue text-black hover:opacity-90 transition-opacity"
                        onClick={() => setOpen(false)}
                      >
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-12v4m-2-2h4m5 4v4m-2-2h4M5 3a2 2 0 00-2 2v1m16 0V5a2 2 0 00-2-2h-1m-4 16l2 2l2-2m-4-4l2 2l2-2m-4 4V3" />
                        </svg>
                        Upgrade Plan
                      </Link>
                      <button
                        onClick={() => {
                          setOpen(false)
                          onLogout()
                        }}
                        className="group flex w-full gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold text-gray-400 hover:text-white hover:bg-dark-border"
                      >
                        <ArrowRightOnRectangleIcon className="h-6 w-6 shrink-0" />
                        Logout
                      </button>
                    </li>
                  </ul>
                </nav>
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  )
}