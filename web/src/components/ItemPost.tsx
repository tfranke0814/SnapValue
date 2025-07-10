'use client';

import React from 'react';
import { Heart, MessageCircle, Share, Bookmark, MoreHorizontal } from 'lucide-react';
import Image from 'next/image';

interface ItemPostProps {
  id: string;
  user: {
    name: string;
    username: string;
    avatar: string;
  };
  item: {
    name: string;
    description: string;
    estimatedValue: string;
    category: string;
    images: string[];
  };
  stats: {
    likes: number;
    comments: number;
    shares: number;
  };
  isLiked: boolean;
  isSaved: boolean;
}

export default function ItemPost({ 
  user, 
  item, 
  stats, 
  isLiked, 
  isSaved 
}: ItemPostProps) {
  const handleLike = () => {
    // Handle like functionality
  };

  const handleComment = () => {
    // Handle comment functionality
  };

  const handleShare = () => {
    // Handle share functionality
  };

  const handleSave = () => {
    // Handle save functionality
  };

  return (
    <div className="relative w-full h-screen snap-start bg-black">
      {/* Main image */}
      <div className="relative w-full h-full">
        <Image
          src={item.images[0] || '/placeholder-item.jpg'}
          alt={item.name}
          fill
          className="object-cover"
          priority
        />
        
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
      </div>
      
      {/* Right side actions */}
      <div className="absolute right-4 bottom-32 flex flex-col items-center space-y-6">
        {/* Like button */}
        <button
          onClick={handleLike}
          className="flex flex-col items-center space-y-1 group"
        >
          <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
            <Heart
              size={24}
              className={`${isLiked ? 'fill-red-500 text-red-500' : 'text-white'}`}
            />
          </div>
          <span className="text-white text-xs font-medium">
            {stats.likes > 1000 ? `${(stats.likes / 1000).toFixed(1)}k` : stats.likes}
          </span>
        </button>
        
        {/* Comment button */}
        <button
          onClick={handleComment}
          className="flex flex-col items-center space-y-1 group"
        >
          <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
            <MessageCircle size={24} className="text-white" />
          </div>
          <span className="text-white text-xs font-medium">
            {stats.comments > 1000 ? `${(stats.comments / 1000).toFixed(1)}k` : stats.comments}
          </span>
        </button>
        
        {/* Share button */}
        <button
          onClick={handleShare}
          className="flex flex-col items-center space-y-1 group"
        >
          <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
            <Share size={24} className="text-white" />
          </div>
          <span className="text-white text-xs font-medium">
            {stats.shares > 1000 ? `${(stats.shares / 1000).toFixed(1)}k` : stats.shares}
          </span>
        </button>
        
        {/* Save button */}
        <button
          onClick={handleSave}
          className="flex flex-col items-center space-y-1 group"
        >
          <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
            <Bookmark
              size={24}
              className={`${isSaved ? 'fill-yellow-500 text-yellow-500' : 'text-white'}`}
            />
          </div>
        </button>
      </div>
      
      {/* Bottom content */}
      <div className="absolute bottom-4 left-4 right-20 text-white">
        {/* User info */}
        <div className="flex items-center space-x-3 mb-3">
          <Image
            src={user.avatar || '/placeholder-avatar.jpg'}
            alt={user.name}
            width={40}
            height={40}
            className="rounded-full"
          />
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="font-semibold">{user.username}</span>
              <button className="text-blue-500 text-sm font-medium">Follow</button>
            </div>
            <span className="text-gray-300 text-sm">{user.name}</span>
          </div>
          <button className="text-white">
            <MoreHorizontal size={20} />
          </button>
        </div>
        
        {/* Item info */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-lg font-bold">{item.name}</span>
            <span className="bg-blue-500 text-white px-2 py-1 rounded-full text-xs">
              {item.category}
            </span>
          </div>
          
          <p className="text-gray-200 text-sm line-clamp-2">{item.description}</p>
          
          <div className="flex items-center space-x-4">
            <div className="bg-green-500 text-white px-3 py-1 rounded-full">
              <span className="text-sm font-semibold">Est. Value: {item.estimatedValue}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
