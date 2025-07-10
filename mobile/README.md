# SnapValue Mobile App

A modern React Native app that uses AI to appraise and value items through camera capture. Built with Expo and featuring a TikTok-inspired UI design.

## 🚀 Features

- **AI-Powered Appraisals**: Capture photos of items and get instant AI-powered value estimates
- **Modern UI**: TikTok-inspired design with smooth animations and gradients
- **Camera Integration**: Full-screen camera experience with viewfinder overlay
- **Social Features**: For You feed, Following feed, and messaging system
- **User Profiles**: Comprehensive profile management with stats and collections
- **Real-time Chat**: Messaging system for user interactions

## 📱 Screenshots

The app features a clean, modern interface with:
- Home feed with item discoveries
- Following feed for social interactions
- Full-screen camera capture
- Item preview and appraisal results
- Messaging and chat functionality
- User profile management

## 🛠️ Tech Stack

- **React Native** - Mobile app framework
- **Expo** - Development platform and build tools
- **React Navigation** - Navigation library
- **Expo Linear Gradient** - Gradient components
- **React Native Vector Icons** - Icon library
- **TypeScript** - Type safety (configured)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (version 16 or higher)
- **npm** or **yarn** package manager
- **Expo CLI**: `npm install -g @expo/cli`
- **Expo Go** app on your mobile device (for testing)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tfranke0814/SnapValue.git
   cd SnapValue/mobile
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npx expo start
   ```

4. **Run on your device**
   - Install **Expo Go** from the App Store (iOS) or Google Play Store (Android)
   - Scan the QR code displayed in your terminal with Expo Go
   - The app will load on your device

## 🔧 Development Setup

### For iOS Development
```bash
# Install iOS dependencies (macOS only)
cd ios && pod install && cd ..

# Run on iOS simulator
npx expo run:ios
```

### For Android Development
```bash
# Run on Android emulator
npx expo run:android
```

### Environment Setup
The app uses mock data for development. In production, you'll need to:

1. Set up AI/ML services for item recognition
2. Configure backend APIs for user management
3. Set up real-time messaging infrastructure
4. Configure camera permissions and storage

## 📁 Project Structure

```
mobile/
├── src/
│   ├── components/          # Reusable UI components
│   ├── constants/
│   │   └── colors.js       # Color system and theme
│   └── screens/            # App screens
│       ├── CameraScreen.js     # Camera capture
│       ├── PreviewScreen.js    # Photo preview
│       ├── ResultScreen.js     # Appraisal results
│       ├── ForYouScreen.js     # Home feed
│       ├── FriendsScreen.js    # Following feed
│       ├── MessagesScreen.js   # Message list
│       ├── ChatScreen.js       # Individual chat
│       └── ProfileScreen.js    # User profile
├── assets/                 # Images and static assets
├── App.js                 # Main app component
├── package.json           # Dependencies
└── README.md             # This file
```

## 🎨 Design System

The app uses a comprehensive design system with:

- **Color Palette**: Dark theme with orange accents
- **Typography**: Consistent font weights and sizes
- **Spacing**: Systematic padding and margins
- **Components**: Reusable UI elements with consistent styling

### Key Colors
- Primary: Orange gradients (`#FF6B35`, `#FF8E53`)
- Background: Dark (`#000000`, `#1A1A1A`)
- Text: White and gray variations
- Accents: Blue for pricing, green for success states

## 🔄 Navigation

The app uses a tab-based navigation system:

1. **Home** - For You feed with item discoveries
2. **Following** - Social feed from followed users
3. **Camera** - Full-screen camera capture (center button)
4. **Inbox** - Messages and notifications
5. **Me** - User profile and settings

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## 🚀 Building for Production

### Build for iOS
```bash
npx expo build:ios
```

### Build for Android
```bash
npx expo build:android
```

### Using EAS Build (Recommended)
```bash
# Install EAS CLI
npm install -g eas-cli

# Configure EAS
eas build:configure

# Build for both platforms
eas build --platform all
```

## 🔐 Environment Variables

Create a `.env` file in the mobile directory:

```env
# API Configuration
API_BASE_URL=your_api_url
AI_SERVICE_KEY=your_ai_service_key

# Authentication
AUTH_DOMAIN=your_auth_domain
AUTH_CLIENT_ID=your_client_id

# Storage
STORAGE_BUCKET=your_storage_bucket
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🔮 Roadmap

- [ ] Real camera integration
- [ ] AI/ML model integration
- [ ] User authentication
- [ ] Backend API integration
- [ ] Push notifications
- [ ] Social features expansion
- [ ] Marketplace integration

## 📞 Contact

- **Email**: contact@snapvalue.com
- **Website**: https://snapvalue.com
- **Twitter**: @snapvalue

---

Made with ❤️ for the Google AI Startup School Hackathon 