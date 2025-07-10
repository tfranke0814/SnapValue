'use client';

import React, { useEffect, useRef } from 'react';
import ItemPost from './ItemPost';

// Mock data for demonstration
const mockPosts = [
  {
    id: '1',
    user: {
      name: 'Sarah Johnson',
      username: '@sarahj',
      avatar: '/placeholder-avatar.jpg',
    },
    item: {
      name: 'Vintage Rolex Watch',
      description: 'Found this vintage Rolex in my grandfather\'s attic. Looking to get it appraised!',
      estimatedValue: '$15,000 - $25,000',
      category: 'Watches',
      images: ['/placeholder-watch.jpg'],
    },
    stats: {
      likes: 1234,
      comments: 89,
      shares: 45,
    },
    isLiked: false,
    isSaved: false,
  },
  {
    id: '2',
    user: {
      name: 'Mike Chen',
      username: '@mikechen',
      avatar: '/placeholder-avatar-2.jpg',
    },
    item: {
      name: 'First Edition Pokemon Cards',
      description: 'Complete set of first edition Pokemon cards in mint condition. What do you think they\'re worth?',
      estimatedValue: '$8,000 - $12,000',
      category: 'Collectibles',
      images: ['/placeholder-cards.jpg'],
    },
    stats: {
      likes: 2341,
      comments: 156,
      shares: 78,
    },
    isLiked: true,
    isSaved: true,
  },
  {
    id: '3',
    user: {
      name: 'Emma Davis',
      username: '@emmad',
      avatar: '/placeholder-avatar-3.jpg',
    },
    item: {
      name: 'Antique Chinese Vase',
      description: 'Beautiful antique vase passed down through generations. Dynasty markings on the bottom.',
      estimatedValue: '$5,000 - $8,000',
      category: 'Antiques',
      images: ['/placeholder-vase.jpg'],
    },
    stats: {
      likes: 567,
      comments: 34,
      shares: 23,
    },
    isLiked: false,
    isSaved: false,
  },
];

export default function Feed() {
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const feed = feedRef.current;
    if (!feed) return;

    // Auto-scroll to snap to posts
    const handleScroll = () => {
      const scrollTop = feed.scrollTop;
      const windowHeight = window.innerHeight;
      const snapIndex = Math.round(scrollTop / windowHeight);
      
      // Smooth scroll to the nearest post
      feed.scrollTo({
        top: snapIndex * windowHeight,
        behavior: 'smooth',
      });
    };

    let scrollTimeout: NodeJS.Timeout;
    const debouncedScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(handleScroll, 150);
    };

    feed.addEventListener('scroll', debouncedScroll);
    return () => {
      feed.removeEventListener('scroll', debouncedScroll);
      clearTimeout(scrollTimeout);
    };
  }, []);

  return (
    <div
      ref={feedRef}
      className="h-screen overflow-y-scroll snap-y snap-mandatory hide-scrollbar"
    >
      {mockPosts.map((post) => (
        <ItemPost key={post.id} {...post} />
      ))}
    </div>
  );
}
