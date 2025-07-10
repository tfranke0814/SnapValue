import React from 'react';
import AppLayout from '@/components/AppLayout';
import { User, Bell, Shield, Eye, Globe, HelpCircle, LogOut } from 'lucide-react';

export default function SettingsPage() {
  const settingsSections = [
    {
      title: 'Account',
      items: [
        { icon: User, label: 'Profile Settings', description: 'Update your profile information' },
        { icon: Bell, label: 'Notifications', description: 'Manage your notification preferences' },
        { icon: Shield, label: 'Privacy & Security', description: 'Control your privacy settings' },
      ],
    },
    {
      title: 'Preferences',
      items: [
        { icon: Eye, label: 'Display', description: 'Theme and display options' },
        { icon: Globe, label: 'Language & Region', description: 'Set your language and location' },
      ],
    },
    {
      title: 'Support',
      items: [
        { icon: HelpCircle, label: 'Help & Support', description: 'Get help and contact support' },
      ],
    },
  ];

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-2xl mx-auto p-6">
          <h1 className="text-2xl font-bold mb-8">Settings</h1>
          
          <div className="space-y-8">
            {settingsSections.map((section, sectionIndex) => (
              <div key={sectionIndex}>
                <h2 className="text-lg font-semibold text-gray-300 mb-4">{section.title}</h2>
                <div className="space-y-2">
                  {section.items.map((item, itemIndex) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={itemIndex}
                        className="w-full text-left p-4 bg-zinc-900 hover:bg-zinc-800 rounded-lg transition-colors flex items-center space-x-4"
                      >
                        <div className="w-10 h-10 bg-zinc-700 rounded-lg flex items-center justify-center">
                          <Icon size={20} className="text-gray-300" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-medium">{item.label}</h3>
                          <p className="text-sm text-gray-400">{item.description}</p>
                        </div>
                        <div className="text-gray-400">›</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
            
            {/* Logout button */}
            <div className="pt-4 border-t border-zinc-800">
              <button className="w-full text-left p-4 bg-red-900/20 hover:bg-red-900/30 rounded-lg transition-colors flex items-center space-x-4 text-red-400">
                <div className="w-10 h-10 bg-red-900/30 rounded-lg flex items-center justify-center">
                  <LogOut size={20} />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">Sign Out</h3>
                  <p className="text-sm text-red-300">Sign out of your account</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
