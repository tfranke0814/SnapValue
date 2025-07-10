import React from 'react';
import AppLayout from '@/components/AppLayout';
import { Heart } from 'lucide-react';

export default function LikedPage() {
  const mockLikedPosts = Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    user: `User ${i + 1}`,
    item: `Item ${i + 1}`,
    value: `$${(Math.random() * 5000 + 500).toFixed(0)}`,
    likes: Math.floor(Math.random() * 1000) + 10,
  }));

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center space-x-3 mb-8">
            <Heart size={28} className="text-red-500" />
            <h1 className="text-2xl font-bold">Liked Posts</h1>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {mockLikedPosts.map((post) => (
              <div key={post.id} className="bg-zinc-900 rounded-lg overflow-hidden">
                <div className="aspect-square bg-zinc-800 flex items-center justify-center">
                  <span className="text-gray-500">{post.item}</span>
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">by {post.user}</span>
                    <Heart size={16} className="text-red-500 fill-red-500" />
                  </div>
                  <h3 className="font-semibold text-sm mb-1">{post.item}</h3>
                  <div className="flex items-center justify-between">
                    <p className="text-green-500 text-sm font-semibold">{post.value}</p>
                    <span className="text-xs text-gray-400">{post.likes} likes</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {mockLikedPosts.length === 0 && (
            <div className="text-center py-12">
              <Heart size={48} className="mx-auto mb-4 text-gray-600" />
              <h3 className="text-xl font-semibold mb-2">No liked posts yet</h3>
              <p className="text-gray-400">Start liking posts to see them here</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
