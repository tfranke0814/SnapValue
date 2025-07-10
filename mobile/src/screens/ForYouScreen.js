import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  Image,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { LinearGradient } from 'expo-linear-gradient';

// Mock data for the feed
const MOCK_ITEMS = [
  {
    id: '1',
    image: 'https://picsum.photos/400/600?random=1',
    title: 'Vintage Rolex Watch',
    price: 15000,
    seller: {
      username: 'luxurydealer',
      avatar: 'https://picsum.photos/50/50?random=1',
    },
    likes: 1234,
    comments: 89,
  },
  {
    id: '2',
    image: 'https://picsum.photos/400/600?random=2',
    title: 'Antique Vase',
    price: 2500,
    seller: {
      username: 'antiquecollector',
      avatar: 'https://picsum.photos/50/50?random=2',
    },
    likes: 856,
    comments: 45,
  },
  {
    id: '3',
    image: 'https://picsum.photos/400/600?random=3',
    title: 'Designer Handbag',
    price: 1200,
    seller: {
      username: 'fashionista',
      avatar: 'https://picsum.photos/50/50?random=3',
    },
    likes: 567,
    comments: 32,
  },
];

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const ItemCard = ({ item }) => {
  const [liked, setLiked] = useState(false);

  return (
    <View style={styles.itemCard}>
      <Image source={{ uri: item.image }} style={styles.itemImage} />
      {/* Gradient overlay for readability */}
      <LinearGradient
        colors={['transparent', 'rgba(0,0,0,0.8)']}
        style={styles.gradientOverlay}
      />
      
      {/* Right side interaction buttons */}
      <View style={styles.interactionButtons}>
        <View style={styles.sellerInfo}>
          <Image source={{ uri: item.seller.avatar }} style={styles.sellerAvatar} />
        </View>
        
        <TouchableOpacity 
          style={styles.interactionButton}
          onPress={() => setLiked(!liked)}
        >
          <Icon 
            name={liked ? 'favorite' : 'favorite-border'} 
            size={30} 
            color={liked ? COLORS.accent_red : 'white'} 
          />
          <Text style={styles.interactionText}>{item.likes}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.interactionButton}>
          <Icon name="chat-bubble-outline" size={30} color="white" />
          <Text style={styles.interactionText}>{item.comments}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.interactionButton}>
          <Icon name="share" size={30} color="white" />
        </TouchableOpacity>
      </View>

      {/* Item info overlay */}
      <View style={styles.itemInfo}>
        <Text style={styles.sellerUsername}>@{item.seller.username}</Text>
        <Text style={styles.itemTitle}>{item.title}</Text>
        <Text style={styles.itemPrice}>${item.price.toLocaleString()}</Text>
        <TouchableOpacity style={styles.makeOfferButton}>
          <Text style={styles.makeOfferText}>Make Offer</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const ForYouScreen = () => {
  return (
    <View style={styles.container}>
      <FlatList
        data={MOCK_ITEMS}
        renderItem={({ item }) => <ItemCard item={item} />}
        keyExtractor={item => item.id}
        snapToInterval={screenHeight}
        decelerationRate="fast"
        showsVerticalScrollIndicator={false}
        pagingEnabled
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.black,
  },
  itemCard: {
    width: screenWidth,
    height: screenHeight,
    position: 'relative',
  },
  itemImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  gradientOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: '40%',
  },
  interactionButtons: {
    position: 'absolute',
    right: 10,
    bottom: 150,
    alignItems: 'center',
  },
  sellerInfo: {
    marginBottom: 20,
  },
  sellerAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  interactionButton: {
    alignItems: 'center',
    marginVertical: 8,
  },
  interactionText: {
    color: COLORS.white,
    marginTop: 4,
    backgroundColor: 'rgba(0,0,0,0.4)',
    paddingHorizontal: 4,
    borderRadius: 4,
  },
  itemInfo: {
    position: 'absolute',
    bottom: 80,
    left: 10,
    right: 80,
    padding: 10,
  },
  sellerUsername: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  itemTitle: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  itemPrice: {
    color: COLORS.primary,
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  makeOfferButton: {
    backgroundColor: COLORS.accent_orange,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 25,
    alignSelf: 'flex-start',
  },
  makeOfferText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ForYouScreen; 