'use client';

import React, { useState } from 'react';
import AppLayout from '@/components/AppLayout';
import { Settings, Grid, Bookmark, Heart, MapPin, Calendar } from 'lucide-react';
import Image from 'next/image';

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('posts');

  const tabs = [
    { id: 'posts', label: 'Posts', icon: Grid },
    { id: 'liked', label: 'Liked', icon: Heart },
    { id: 'saved', label: 'Saved', icon: Bookmark },
  ];

  const mockPosts = Array.from({ length: 12 }, (_, i) => ({
    id: i + 1,
    image: '/placeholder-item.jpg',
    value: `$${(Math.random() * 5000 + 500).toFixed(0)}`,
    likes: Math.floor(Math.random() * 1000) + 10,
  }));

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-4xl mx-auto">
          {/* Profile Header */}
          <div className="p-6 border-b border-zinc-800">
            <div className="flex items-start space-x-6">
              {/* Profile Picture */}
              <div className="relative">
                <Image
                  src="/placeholder-avatar.jpg"
                  alt="Profile"
                  width={120}
                  height={120}
                  className="rounded-full"
                />
                <div className="absolute bottom-2 right-2 w-6 h-6 bg-green-500 rounded-full border-2 border-black"></div>
              </div>
              
              {/* Profile Info */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h1 className="text-2xl font-bold">Sarah Johnson</h1>
                    <p className="text-gray-400">@sarahj</p>
                  </div>
                  <button className="flex items-center space-x-2 bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded-lg transition-colors">
                    <Settings size={18} />
                    <span>Edit Profile</span>
                  </button>
                </div>
                
                {/* Stats */}
                <div className="flex space-x-8 mb-4">
                  <div className="text-center">
                    <div className="text-xl font-bold">127</div>
                    <div className="text-gray-400 text-sm">Posts</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">2.1k</div>
                    <div className="text-gray-400 text-sm">Followers</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">1.8k</div>
                    <div className="text-gray-400 text-sm">Following</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold">$45k</div>
                    <div className="text-gray-400 text-sm">Total Value</div>
                  </div>
                </div>
                
                {/* Bio */}
                <div className="space-y-2">
                  <p className="text-gray-200">Vintage collector & appraisal enthusiast 🔍</p>
                  <p className="text-gray-200">Sharing rare finds and hidden treasures</p>
                  <div className="flex items-center space-x-4 text-gray-400 text-sm">
                    <div className="flex items-center space-x-1">
                      <MapPin size={14} />
                      <span>San Francisco, CA</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar size={14} />
                      <span>Joined March 2024</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="border-b border-zinc-800">
            <div className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-6 py-4 border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-500'
                        : 'border-transparent text-gray-400 hover:text-white'
                    }`}
                  >
                    <Icon size={18} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Content */}
          <div className="p-6">
            {activeTab === 'posts' && (
              <div className="grid grid-cols-3 gap-1">
                {mockPosts.map((post) => (
                  <div key={post.id} className="relative aspect-square bg-zinc-800 rounded-lg overflow-hidden group cursor-pointer">
                    <div className="w-full h-full bg-zinc-700 flex items-center justify-center">
                      <span className="text-gray-500">Item {post.id}</span>
                    </div>
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <div className="text-center text-white">
                        <div className="flex items-center space-x-2 justify-center mb-1">
                          <Heart size={16} />
                          <span className="text-sm">{post.likes}</span>
                        </div>
                        <div className="text-xs text-green-400">{post.value}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {activeTab === 'liked' && (
              <div className="text-center py-12">
                <Heart size={48} className="mx-auto mb-4 text-gray-600" />
                <h3 className="text-xl font-semibold mb-2">No liked posts yet</h3>
                <p className="text-gray-400">Start liking posts to see them here</p>
              </div>
            )}
            
            {activeTab === 'saved' && (
              <div className="text-center py-12">
                <Bookmark size={48} className="mx-auto mb-4 text-gray-600" />
                <h3 className="text-xl font-semibold mb-2">No saved posts yet</h3>
                <p className="text-gray-400">Save posts to view them later</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
