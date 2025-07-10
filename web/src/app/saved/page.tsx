import React from 'react';
import AppLayout from '@/components/AppLayout';
import { Bookmark } from 'lucide-react';

export default function SavedPage() {
  const mockSavedPosts = Array.from({ length: 6 }, (_, i) => ({
    id: i + 1,
    user: `User ${i + 1}`,
    item: `Saved Item ${i + 1}`,
    value: `$${(Math.random() * 5000 + 500).toFixed(0)}`,
    category: ['Watches', 'Collectibles', 'Antiques', 'Art', 'Jewelry'][Math.floor(Math.random() * 5)],
  }));

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center space-x-3 mb-8">
            <Bookmark size={28} className="text-yellow-500" />
            <h1 className="text-2xl font-bold">Saved Posts</h1>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {mockSavedPosts.map((post) => (
              <div key={post.id} className="bg-zinc-900 rounded-lg overflow-hidden">
                <div className="aspect-square bg-zinc-800 flex items-center justify-center relative">
                  <span className="text-gray-500">{post.item}</span>
                  <div className="absolute top-2 right-2">
                    <Bookmark size={20} className="text-yellow-500 fill-yellow-500" />
                  </div>
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">
                      {post.category}
                    </span>
                    <span className="text-sm text-gray-400">by {post.user}</span>
                  </div>
                  <h3 className="font-semibold text-sm mb-1">{post.item}</h3>
                  <p className="text-green-500 text-sm font-semibold">{post.value}</p>
                </div>
              </div>
            ))}
          </div>
          
          {mockSavedPosts.length === 0 && (
            <div className="text-center py-12">
              <Bookmark size={48} className="mx-auto mb-4 text-gray-600" />
              <h3 className="text-xl font-semibold mb-2">No saved posts yet</h3>
              <p className="text-gray-400">Save posts to view them later</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
