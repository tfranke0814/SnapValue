'use client';

import React, { useState } from 'react';
import AppLayout from '@/components/AppLayout';
import { Search, Send, MoreVertical } from 'lucide-react';
import Image from 'next/image';

interface Message {
  id: string;
  text: string;
  timestamp: string;
  isOwn: boolean;
}

interface Chat {
  id: string;
  user: {
    name: string;
    username: string;
    avatar: string;
    isOnline: boolean;
  };
  lastMessage: string;
  timestamp: string;
  unread: number;
}

export default function MessagesPage() {
  const [selectedChat, setSelectedChat] = useState<string | null>(null);
  const [messageText, setMessageText] = useState('');

  const mockChats: Chat[] = [
    {
      id: '1',
      user: {
        name: 'Mike Chen',
        username: '@mikechen',
        avatar: '/placeholder-avatar-2.jpg',
        isOnline: true,
      },
      lastMessage: 'Hey, interested in your vintage watch!',
      timestamp: '2m ago',
      unread: 2,
    },
    {
      id: '2',
      user: {
        name: 'Emma Davis',
        username: '@emmad',
        avatar: '/placeholder-avatar-3.jpg',
        isOnline: false,
      },
      lastMessage: 'That vase looks authentic. Where did you find it?',
      timestamp: '1h ago',
      unread: 0,
    },
    {
      id: '3',
      user: {
        name: 'Alex Thompson',
        username: '@alexthompson',
        avatar: '/placeholder-avatar.jpg',
        isOnline: true,
      },
      lastMessage: 'Thanks for the appraisal! 🙏',
      timestamp: '3h ago',
      unread: 0,
    },
  ];

  const mockMessages: Message[] = [
    {
      id: '1',
      text: 'Hey, interested in your vintage watch!',
      timestamp: '2:30 PM',
      isOwn: false,
    },
    {
      id: '2',
      text: 'Is it still available?',
      timestamp: '2:31 PM',
      isOwn: false,
    },
    {
      id: '3',
      text: 'Hi! Yes, it\'s still available. Are you looking to purchase or just curious about the appraisal?',
      timestamp: '2:45 PM',
      isOwn: true,
    },
    {
      id: '4',
      text: 'I\'m definitely interested in purchasing. Could you tell me more about its condition and history?',
      timestamp: '2:46 PM',
      isOwn: false,
    },
  ];

  const handleSendMessage = () => {
    if (messageText.trim()) {
      // Handle sending message
      setMessageText('');
    }
  };

  return (
    <AppLayout>
      <div className="h-screen bg-black text-white flex">
        {/* Chat List */}
        <div className={`w-full md:w-80 bg-zinc-900 border-r border-zinc-800 flex flex-col ${selectedChat ? 'hidden md:flex' : 'flex'}`}>
          {/* Header */}
          <div className="p-4 border-b border-zinc-800">
            <h1 className="text-xl font-bold mb-4">Messages</h1>
            <div className="relative">
              <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search conversations..."
                className="w-full bg-zinc-800 text-white placeholder-gray-400 pl-10 pr-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          {/* Chat List */}
          <div className="flex-1 overflow-y-auto">
            {mockChats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => setSelectedChat(chat.id)}
                className={`p-4 border-b border-zinc-800 cursor-pointer hover:bg-zinc-800 transition-colors ${
                  selectedChat === chat.id ? 'bg-zinc-800' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <Image
                      src={chat.user.avatar}
                      alt={chat.user.name}
                      width={48}
                      height={48}
                      className="rounded-full"
                    />
                    {chat.user.isOnline && (
                      <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-zinc-900"></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold truncate">{chat.user.name}</h3>
                      <span className="text-xs text-gray-400">{chat.timestamp}</span>
                    </div>
                    <p className="text-sm text-gray-400 truncate">{chat.lastMessage}</p>
                  </div>
                  {chat.unread > 0 && (
                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-xs font-semibold">{chat.unread}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Chat Window */}
        <div className={`flex-1 flex flex-col ${selectedChat ? 'flex' : 'hidden md:flex'}`}>
          {selectedChat ? (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-900">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setSelectedChat(null)}
                    className="md:hidden text-blue-500 mr-2"
                  >
                    ←
                  </button>
                  <div className="relative">
                    <Image
                      src="/placeholder-avatar-2.jpg"
                      alt="Mike Chen"
                      width={40}
                      height={40}
                      className="rounded-full"
                    />
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border border-zinc-900"></div>
                  </div>
                  <div>
                    <h2 className="font-semibold">Mike Chen</h2>
                    <p className="text-sm text-green-500">Online</p>
                  </div>
                </div>
                <button className="text-gray-400 hover:text-white">
                  <MoreVertical size={20} />
                </button>
              </div>
              
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {mockMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isOwn ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.isOwn
                          ? 'bg-blue-500 text-white'
                          : 'bg-zinc-800 text-white'
                      }`}
                    >
                      <p className="text-sm">{message.text}</p>
                      <p
                        className={`text-xs mt-1 ${
                          message.isOwn ? 'text-blue-100' : 'text-gray-400'
                        }`}
                      >
                        {message.timestamp}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Message Input */}
              <div className="p-4 border-t border-zinc-800 bg-zinc-900">
                <div className="flex items-center space-x-3">
                  <input
                    type="text"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 bg-zinc-800 text-white placeholder-gray-400 px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <button
                    onClick={handleSendMessage}
                    className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg transition-colors"
                  >
                    <Send size={20} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-black">
              <div className="text-center">
                <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Send size={24} className="text-gray-400" />
                </div>
                <h2 className="text-xl font-semibold mb-2">No conversation selected</h2>
                <p className="text-gray-400">Choose a conversation to start messaging</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
