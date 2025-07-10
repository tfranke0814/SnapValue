import React from 'react';
import AppLayout from '@/components/AppLayout';
import Feed from '@/components/Feed';

export default function HomePage() {
  return (
    <AppLayout>
      <Feed />
    </AppLayout>
  );
}
