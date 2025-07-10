'use client';

import React from 'react';
import { Home, Search, Camera, MessageCircle, User, Settings, Heart, Bookmark } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const mainNavigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Browse', href: '/browse', icon: Search },
  { name: 'Camera', href: '/camera', icon: Camera },
  { name: 'Messages', href: '/messages', icon: MessageCircle },
  { name: 'Profile', href: '/profile', icon: User },
];

const secondaryNavigation = [
  { name: 'Liked', href: '/liked', icon: Heart },
  { name: 'Saved', href: '/saved', icon: Bookmark },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function SidebarNavigation() {
  const pathname = usePathname();

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-zinc-900 border-r border-zinc-800">
      <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
        {/* Logo */}
        <div className="flex items-center flex-shrink-0 px-4">
          <h1 className="text-2xl font-bold text-blue-500">SnapValue</h1>
        </div>
        
        {/* Main Navigation */}
        <nav className="mt-8 flex-1 px-2 space-y-1">
          {mainNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`group flex items-center px-2 py-3 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-zinc-700 hover:text-white'
                }`}
              >
                <Icon 
                  size={20} 
                  className={`mr-3 flex-shrink-0 ${
                    item.name === 'Camera' && !isActive ? 'text-blue-500' : ''
                  }`}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
        
        {/* Secondary Navigation */}
        <nav className="px-2 space-y-1">
          {secondaryNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-zinc-700 hover:text-white'
                }`}
              >
                <Icon size={18} className="mr-3 flex-shrink-0" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
