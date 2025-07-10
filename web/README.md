# SnapValue Web

A Next.js web application that replicates a mobile TikTok-like social media app for item appraisal and browsing. This is the web version that preserves all the designs and functionality from the mobile app.

## Features

- **TikTok-style Feed**: Vertical scrolling feed for browsing item appraisals
- **Camera Integration**: Web camera functionality for real-time item photography and AI analysis
- **Social Features**: User profiles, following, likes, comments, and sharing
- **Responsive Design**: Works seamlessly on both mobile and desktop
- **Dark Theme**: Modern dark UI with blue accents matching the mobile app
- **Real-time Messaging**: Chat system for user communication
- **Browse & Search**: Grid view for exploring categorized items

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **UI**: Custom components with modern design patterns

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── browse/            # Browse items page
│   ├── camera/            # Camera appraisal page
│   ├── liked/             # Liked posts page
│   ├── messages/          # Chat/messaging page
│   ├── profile/           # User profile page
│   ├── saved/             # Saved posts page
│   └── settings/          # Settings page
├── components/            # Reusable UI components
│   ├── AppLayout.tsx      # Main layout wrapper
│   ├── BottomNavigation.tsx # Mobile bottom nav
│   ├── SidebarNavigation.tsx # Desktop sidebar nav
│   ├── Feed.tsx           # TikTok-style feed
│   └── ItemPost.tsx       # Individual post component
└── globals.css            # Global styles and CSS variables
```

## Key Components

### Feed System
- Vertical scrolling with snap-to-post behavior
- Interactive post actions (like, comment, share, save)
- Real-time engagement stats
- User information and item details overlay

### Camera Integration
- Web camera access with environment facing preference
- Real-time photo capture and processing
- AI analysis simulation with estimated values
- Share functionality for captured appraisals

### Navigation
- Responsive navigation that adapts to screen size
- Bottom tab bar for mobile devices
- Sidebar navigation for desktop
- Smooth transitions between pages

### Design System
- Dark theme with consistent color palette
- Blue (#007AFF) as primary accent color
- Typography hierarchy with system fonts
- Smooth animations and micro-interactions

## Mobile App Compatibility

This web version replicates all the key features and designs from the mobile React Native app:

- ✅ TikTok-style vertical feed
- ✅ Camera functionality for item appraisal
- ✅ Social features (likes, comments, follows)
- ✅ User profiles with stats
- ✅ Real-time messaging
- ✅ Browse and search functionality
- ✅ Dark theme with blue accents
- ✅ Responsive design for all devices

## Placeholder Content

The app currently uses placeholder data and images. To add real content:

1. Replace placeholder images in `/public/`
2. Connect to your backend API for real data
3. Implement authentication system
4. Add real camera processing and AI analysis

## Development

- The app uses TypeScript for type safety
- Tailwind CSS for styling with custom design tokens
- ESLint for code quality
- Next.js Image component for optimized images
- Custom hooks for camera and media functionality

## Deployment

Deploy to Vercel (recommended):

```bash
npm run build
```

Or deploy to any platform that supports Next.js applications.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on both mobile and desktop
5. Submit a pull request

## License

This project is licensed under the MIT License.
