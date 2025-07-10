'use client';

import React from 'react';
import { Home, Search, Camera, MessageCircle, User } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Browse', href: '/browse', icon: Search },
  { name: 'Camera', href: '/camera', icon: Camera },
  { name: 'Messages', href: '/messages', icon: MessageCircle },
  { name: 'Profile', href: '/profile', icon: User },
];

export default function BottomNavigation() {
  const pathname = usePathname();

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 z-50 md:hidden">
      <div className="flex items-center justify-around py-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex flex-col items-center py-2 px-4 transition-colors ${
                isActive 
                  ? 'text-blue-500' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Icon 
                size={24} 
                fill={isActive ? 'currentColor' : 'none'}
                className={item.name === 'Camera' ? 'text-white bg-blue-500 rounded-full p-1 w-8 h-8' : ''}
              />
              <span className="text-xs mt-1">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
