import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MaterialIcons } from '@expo/vector-icons';
import { View, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

// Import screens
import ForYouScreen from './src/screens/ForYouScreen';
import FriendsScreen from './src/screens/FriendsScreen';
import CameraScreen from './src/screens/CameraScreen';
import PreviewScreen from './src/screens/PreviewScreen';
import ResultScreen from './src/screens/ResultScreen';
import MessagesScreen from './src/screens/MessagesScreen';
import ChatScreen from './src/screens/ChatScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import { COLORS } from './src/constants/colors';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Custom Tab Bar Button for Camera
function CustomTabBarButton({ children, onPress }) {
  return (
    <TouchableOpacity
      style={{
        height: '100%',
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
      }}
      onPress={onPress}
    >
      <View
        style={{
          width: 32,
          height: 32,
          backgroundColor: COLORS.white,
          borderRadius: 8,
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <MaterialIcons name="add" size={24} color={COLORS.black} />
      </View>
    </TouchableOpacity>
  );
}

// Camera Stack Navigator
function CameraStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CameraMain" component={CameraScreen} />
      <Stack.Screen name="Preview" component={PreviewScreen} />
      <Stack.Screen name="Result" component={ResultScreen} />
    </Stack.Navigator>
  );
}

// Messages Stack Navigator
function MessagesStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="MessagesMain" component={MessagesScreen} />
      <Stack.Screen name="Chat" component={ChatScreen} />
    </Stack.Navigator>
  );
}

// Main Tab Navigator
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route, navigation }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'ForYou') {
            iconName = focused ? 'home' : 'home';
          } else if (route.name === 'Friends') {
            iconName = focused ? 'group' : 'group';
          } else if (route.name === 'Camera') {
            // This won't be used since we have custom button
            iconName = 'add';
          } else if (route.name === 'Messages') {
            iconName = focused ? 'chat-bubble' : 'chat-bubble-outline';
          } else if (route.name === 'Profile') {
            iconName = focused ? 'person' : 'person-outline';
          }

          // Don't render icon for camera as it has custom button
          if (route.name === 'Camera') {
            return null;
          }

          return <MaterialIcons name={iconName} size={24} color={color} />;
        },
        tabBarActiveTintColor: COLORS.white,
        tabBarInactiveTintColor: COLORS.gray400,
        tabBarStyle: ((route) => {
          const routeName = route.state
            ? route.state.routes[route.state.index].name
            : route.params?.screen || 'CameraMain';

          if (route.name === 'Camera' && ['CameraMain', 'Preview', 'Result'].includes(routeName)) {
            return { display: 'none' };
          }
          return {
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: COLORS.black,
            height: Platform.OS === 'ios' ? 85 : 60,
            borderTopWidth: 0,
            paddingBottom: Platform.OS === 'ios' ? 30 : 10,
            paddingTop: 5,
          };
        })(route),
        headerShown: false,
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '500',
          marginTop: 2,
        },
        tabBarItemStyle: {
          paddingTop: 5,
          height: Platform.OS === 'ios' ? 50 : 45,
        },
      })}
    >
      <Tab.Screen 
        name="ForYou" 
        component={ForYouScreen} 
        options={{ tabBarLabel: 'Home' }} 
      />
      <Tab.Screen 
        name="Friends" 
        component={FriendsScreen} 
        options={{ tabBarLabel: 'Following' }} 
      />
      <Tab.Screen 
        name="Camera" 
        component={CameraStack} 
        options={{
          tabBarLabel: '',
          tabBarButton: (props) => (
            <CustomTabBarButton {...props} />
          ),
        }}
      />
      <Tab.Screen 
        name="Messages" 
        component={MessagesStack} 
        options={{ tabBarLabel: 'Inbox' }} 
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen} 
        options={{ tabBarLabel: 'Me' }} 
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <MainTabs />
    </NavigationContainer>
  );
} 