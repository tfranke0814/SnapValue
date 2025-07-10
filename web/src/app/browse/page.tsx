import React from 'react';
import AppLayout from '@/components/AppLayout';

export default function BrowsePage() {
  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white p-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold mb-6">Browse Items</h1>
          
          {/* Category filters */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['All', 'Watches', 'Collectibles', 'Antiques', 'Art', 'Jewelry', 'Electronics'].map((category) => (
              <button
                key={category}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  category === 'All'
                    ? 'bg-blue-500 text-white'
                    : 'bg-zinc-800 text-gray-300 hover:bg-zinc-700'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
          
          {/* Grid of items */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((item) => (
              <div key={item} className="bg-zinc-900 rounded-lg overflow-hidden">
                <div className="aspect-square bg-zinc-800 flex items-center justify-center">
                  <span className="text-gray-500">Image {item}</span>
                </div>
                <div className="p-3">
                  <h3 className="font-semibold text-sm mb-1">Item {item}</h3>
                  <p className="text-xs text-gray-400 mb-2">Category</p>
                  <p className="text-green-500 text-sm font-semibold">$X,XXX</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
