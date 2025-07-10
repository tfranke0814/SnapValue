import React from 'react';
import BottomNavigation from './BottomNavigation';
import SidebarNavigation from './SidebarNavigation';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-black">
      <SidebarNavigation />
      
      {/* Main content */}
      <div className="md:pl-64">
        <main className="pb-16 md:pb-0">
          {children}
        </main>
      </div>
      
      <BottomNavigation />
    </div>
  );
}
