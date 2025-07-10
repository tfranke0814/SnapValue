import React from 'react';
import {
  View,
  Text,
  FlatList,
  Image,
  TouchableOpacity,
  StyleSheet,
  Platform,
  StatusBar,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { useNavigation } from '@react-navigation/native';

// Mock data for conversations
const MOCK_CONVERSATIONS = [
  {
    id: '1',
    user: {
      username: 'luxurydealer',
      avatar: 'https://picsum.photos/50/50?random=8',
    },
    lastMessage: {
      text: 'Would you take $14,000 for the watch?',
      timestamp: '2:30 PM',
      unread: true,
    },
  },
  {
    id: '2',
    user: {
      username: 'antiquecollector',
      avatar: 'https://picsum.photos/50/50?random=9',
    },
    lastMessage: {
      text: 'Thanks for the offer! Let me think about it.',
      timestamp: 'Yesterday',
      unread: false,
    },
  },
  {
    id: '3',
    user: {
      username: 'fashionista',
      avatar: 'https://picsum.photos/50/50?random=10',
    },
    lastMessage: {
      text: 'Is this item still available?',
      timestamp: '2 days ago',
      unread: false,
    },
  },
  {
    id: '4',
    user: {
      username: 'vintagecollector',
      avatar: 'https://picsum.photos/50/50?random=11',
    },
    lastMessage: {
      text: 'Great condition! When can we meet?',
      timestamp: '3 days ago',
      unread: false,
    },
  },
];

const ConversationItem = ({ conversation }) => {
  const navigation = useNavigation();

  return (
    <TouchableOpacity
      style={styles.conversationItem}
      onPress={() => navigation.navigate('Chat', {
        userName: conversation.user.username,
        userAvatar: conversation.user.avatar,
      })}
      activeOpacity={0.7}
    >
      <View style={styles.avatarContainer}>
        <Image
          source={{ uri: conversation.user.avatar }}
          style={styles.avatar}
        />
        {conversation.lastMessage.unread && (
          <View style={styles.onlineIndicator} />
        )}
      </View>
      
      <View style={styles.conversationContent}>
        <View style={styles.conversationHeader}>
          <Text style={styles.username}>@{conversation.user.username}</Text>
          <View style={styles.timestampContainer}>
            <Text style={styles.timestamp}>{conversation.lastMessage.timestamp}</Text>
            {conversation.lastMessage.unread && (
              <View style={styles.unreadDot} />
            )}
          </View>
        </View>
        
        <View style={styles.messagePreview}>
          <Text
            style={[
              styles.messageText,
              conversation.lastMessage.unread && styles.unreadMessage,
            ]}
            numberOfLines={1}
          >
            {conversation.lastMessage.text}
          </Text>
        </View>
      </View>
      
      <Icon name="chevron-right" size={20} color={COLORS.gray400} />
    </TouchableOpacity>
  );
};

const MessagesScreen = () => {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.gray50} />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Messages</Text>
          <Text style={styles.headerSubtitle}>{MOCK_CONVERSATIONS.length} conversations</Text>
        </View>
        
        <TouchableOpacity style={styles.searchButton}>
          <Icon name="search" size={24} color={COLORS.gray600} />
        </TouchableOpacity>
      </View>

      {/* Conversations List */}
      <FlatList
        data={MOCK_CONVERSATIONS}
        renderItem={({ item }) => <ConversationItem conversation={item} />}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray50,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 20,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray200,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.black,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.gray500,
    marginTop: 2,
  },
  searchButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    paddingTop: 16,
  },
  conversationItem: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    alignItems: 'center',
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  avatarContainer: {
    position: 'relative',
    marginRight: 12,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: COLORS.gray200,
  },
  onlineIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: COLORS.success,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  conversationContent: {
    flex: 1,
  },
  conversationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  username: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.black,
  },
  timestampContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timestamp: {
    fontSize: 12,
    color: COLORS.gray500,
    fontWeight: '500',
  },
  messagePreview: {
    paddingRight: 20,
  },
  messageText: {
    fontSize: 14,
    color: COLORS.gray600,
    lineHeight: 20,
  },
  unreadMessage: {
    color: COLORS.black,
    fontWeight: '600',
  },
  unreadDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.primary,
    marginLeft: 8,
  },
});

export default MessagesScreen; 