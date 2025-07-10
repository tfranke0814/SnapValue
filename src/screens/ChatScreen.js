import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { useRoute } from '@react-navigation/native';
import { useNavigation } from '@react-navigation/native';

// Mock data for messages
const MOCK_MESSAGES = [
  {
    id: '1',
    text: 'Hi, I\'m interested in your vintage watch.',
    timestamp: '2:25 PM',
    sender: 'user',
  },
  {
    id: '2',
    text: 'Hello! Yes, it\'s still available. Are you looking to make an offer?',
    timestamp: '2:26 PM',
    sender: 'other',
  },
  {
    id: '3',
    text: 'Would you take $14,000 for the watch?',
    timestamp: '2:30 PM',
    sender: 'user',
  },
  {
    id: '4',
    text: 'That\'s a bit low for me. How about $15,500?',
    timestamp: '2:32 PM',
    sender: 'other',
  },
  {
    id: '5',
    text: 'Let me think about it. Can I see more photos?',
    timestamp: '2:35 PM',
    sender: 'user',
  },
  // Add more mock messages as needed
];

const Message = ({ message, isLastMessage }) => {
  const isUser = message.sender === 'user';

  return (
    <View
      style={[
        styles.messageContainer,
        isUser ? styles.userMessage : styles.otherMessage,
      ]}
    >
      <View
        style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.otherBubble,
        ]}
      >
        <Text 
          style={[
            styles.messageText,
            { color: isUser ? COLORS.white : COLORS.black }
          ]}
        >
          {message.text}
        </Text>
      </View>
      <Text 
        style={[
          styles.timestamp,
          isUser ? styles.userTimestamp : styles.otherTimestamp,
        ]}
      >
        {message.timestamp}
      </Text>
    </View>
  );
};

const ChatScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const [message, setMessage] = useState('');
  const flatListRef = useRef(null);
  const { userName } = route.params || {};

  const handleSend = () => {
    if (message.trim()) {
      // TODO: Implement sending message to backend
      console.log('Sending message:', message);
      setMessage('');
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.white} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Icon name="arrow-back" size={24} color={COLORS.black} />
        </TouchableOpacity>
        
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>@{userName || 'User'}</Text>
          <Text style={styles.headerSubtitle}>Online</Text>
        </View>
        
        <TouchableOpacity style={styles.moreButton}>
          <Icon name="more-vert" size={24} color={COLORS.black} />
        </TouchableOpacity>
      </View>
      
      <KeyboardAvoidingView
        style={styles.chatContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={MOCK_MESSAGES}
          renderItem={({ item, index }) => (
            <Message
              message={item}
              isLastMessage={index === MOCK_MESSAGES.length - 1}
            />
          )}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messagesList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
          onLayout={() => flatListRef.current?.scrollToEnd()}
          showsVerticalScrollIndicator={false}
        />

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={message}
            onChangeText={setMessage}
            placeholder="Type a message..."
            placeholderTextColor={COLORS.gray400}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[styles.sendButton, !message.trim() && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={!message.trim()}
          >
            <Icon
              name="send"
              size={24}
              color={message.trim() ? COLORS.white : COLORS.gray400}
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
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
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 16,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray200,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.black,
  },
  headerSubtitle: {
    fontSize: 12,
    color: COLORS.success,
    marginTop: 2,
    fontWeight: '500',
  },
  moreButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatContainer: {
    flex: 1,
  },
  messagesList: {
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  messageContainer: {
    marginVertical: 6,
    maxWidth: '80%',
  },
  userMessage: {
    alignSelf: 'flex-end',
  },
  otherMessage: {
    alignSelf: 'flex-start',
  },
  messageBubble: {
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  userBubble: {
    backgroundColor: COLORS.primary,
    borderBottomRightRadius: 4,
  },
  otherBubble: {
    backgroundColor: COLORS.white,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  timestamp: {
    fontSize: 11,
    marginTop: 4,
    fontWeight: '500',
  },
  userTimestamp: {
    color: COLORS.gray500,
    textAlign: 'right',
  },
  otherTimestamp: {
    color: COLORS.gray500,
    textAlign: 'left',
  },
  inputContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray200,
    alignItems: 'center',
  },
  input: {
    flex: 1,
    backgroundColor: COLORS.gray100,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginRight: 8,
    fontSize: 16,
    maxHeight: 120,
    minHeight: 44,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  sendButtonDisabled: {
    backgroundColor: COLORS.gray300,
    shadowOpacity: 0,
    elevation: 0,
  },
});

export default ChatScreen; 