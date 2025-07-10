// User types
export interface User {
  id: string;
  name: string;
  username: string;
  avatar: string;
  bio?: string;
  isOnline?: boolean;
  stats?: {
    posts: number;
    followers: number;
    following: number;
    totalValue: number;
  };
  location?: string;
  joinedDate?: string;
}

// Item types
export interface Item {
  id: string;
  name: string;
  description: string;
  category: string;
  estimatedValue: string;
  images: string[];
  condition?: 'Poor' | 'Fair' | 'Good' | 'Very Good' | 'Excellent' | 'Like New';
  rarity?: 'Common' | 'Uncommon' | 'Rare' | 'Very Rare' | 'Ultra Rare';
  tags?: string[];
}

// Post types
export interface Post {
  id: string;
  user: User;
  item: Item;
  stats: {
    likes: number;
    comments: number;
    shares: number;
    views?: number;
  };
  isLiked: boolean;
  isSaved: boolean;
  timestamp: string;
  location?: string;
}

// Comment types
export interface Comment {
  id: string;
  user: User;
  text: string;
  timestamp: string;
  likes: number;
  isLiked: boolean;
  replies?: Comment[];
}

// Message types
export interface Message {
  id: string;
  senderId: string;
  recipientId: string;
  text: string;
  timestamp: string;
  isRead: boolean;
  type: 'text' | 'image' | 'item_share';
  attachments?: {
    type: 'image' | 'item';
    url: string;
    metadata?: Record<string, unknown>;
  }[];
}

// Chat types
export interface Chat {
  id: string;
  participants: User[];
  lastMessage: Message;
  unreadCount: number;
  updatedAt: string;
}

// Appraisal types
export interface AppraisalResult {
  item: Item;
  confidence: number;
  suggestedCategory: string;
  estimatedValueRange: {
    min: number;
    max: number;
    currency: string;
  };
  comparableItems?: Item[];
  aiNotes?: string[];
}

// Navigation types
export interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>; // Lucide icon component
  badge?: number;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Filter types
export interface ItemFilters {
  category?: string;
  priceRange?: {
    min: number;
    max: number;
  };
  condition?: Item['condition'];
  rarity?: Item['rarity'];
  location?: string;
  sortBy?: 'newest' | 'oldest' | 'price_low' | 'price_high' | 'popular';
}
