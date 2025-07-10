import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Dimensions,
  Platform,
  StatusBar,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { LinearGradient } from 'expo-linear-gradient';

const { width: screenWidth } = Dimensions.get('window');
const ITEM_WIDTH = (screenWidth - 48) / 3;

// Mock data for user profile
const MOCK_USER = {
  username: 'johndoe',
  avatar: 'https://picsum.photos/100/100?random=11',
  bio: 'Passionate about vintage collectibles and rare finds. Always looking for unique pieces with great stories.',
  verified: true,
  memberSince: '2023',
  stats: {
    listings: 24,
    followers: 1234,
    following: 567,
    sold: 18,
  },
};

// Mock data for items
const MOCK_ITEMS = {
  listings: [
    {
      id: '1',
      image: 'https://picsum.photos/150/150?random=12',
      price: 15000,
      title: 'Vintage Rolex',
      status: 'active',
    },
    {
      id: '2',
      image: 'https://picsum.photos/150/150?random=13',
      price: 2500,
      title: 'Antique Vase',
      status: 'sold',
    },
    {
      id: '3',
      image: 'https://picsum.photos/150/150?random=14',
      price: 1200,
      title: 'Designer Handbag',
      status: 'active',
    },
    {
      id: '4',
      image: 'https://picsum.photos/150/150?random=15',
      price: 850,
      title: 'Vintage Camera',
      status: 'active',
    },
    {
      id: '5',
      image: 'https://picsum.photos/150/150?random=16',
      price: 3200,
      title: 'Art Deco Lamp',
      status: 'pending',
    },
    {
      id: '6',
      image: 'https://picsum.photos/150/150?random=17',
      price: 650,
      title: 'Collectible Toy',
      status: 'active',
    },
  ],
  appraisals: [
    {
      id: '1',
      image: 'https://picsum.photos/150/150?random=18',
      value: 12000,
      date: '2024-03-15',
      confidence: 0.92,
    },
    {
      id: '2',
      image: 'https://picsum.photos/150/150?random=19',
      value: 3500,
      date: '2024-03-14',
      confidence: 0.87,
    },
    {
      id: '3',
      image: 'https://picsum.photos/150/150?random=20',
      value: 750,
      date: '2024-03-13',
      confidence: 0.95,
    },
  ],
  liked: [
    {
      id: '1',
      image: 'https://picsum.photos/150/150?random=21',
      price: 8000,
      title: 'Vintage Camera',
      seller: 'vintagecollector',
    },
    {
      id: '2',
      image: 'https://picsum.photos/150/150?random=22',
      price: 4500,
      title: 'Art Deco Lamp',
      seller: 'artdealer',
    },
    {
      id: '3',
      image: 'https://picsum.photos/150/150?random=23',
      price: 2800,
      title: 'Vintage Guitar',
      seller: 'musicstore',
    },
  ],
};

const ProfileScreen = () => {
  const [activeTab, setActiveTab] = useState('listings');

  const renderGridItem = (item, type) => {
    return (
      <TouchableOpacity
        key={item.id}
        style={styles.gridItem}
        onPress={() => {
          // TODO: Navigate to item detail
          console.log('View item:', item);
        }}
        activeOpacity={0.8}
      >
        <Image source={{ uri: item.image }} style={styles.itemImage} />
        
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.8)']}
          style={styles.itemOverlay}
        >
          <View style={styles.itemInfo}>
            {type === 'listings' && item.status === 'sold' && (
              <View style={styles.soldBadge}>
                <Text style={styles.soldText}>SOLD</Text>
              </View>
            )}
            
            <Text style={styles.itemPrice}>
              ${(type === 'appraisals' ? item.value : item.price).toLocaleString()}
            </Text>
            
            {type === 'appraisals' && (
              <View style={styles.confidenceBadge}>
                <Text style={styles.confidenceText}>
                  {Math.round(item.confidence * 100)}%
                </Text>
              </View>
            )}
            
            {type === 'liked' && (
              <Text style={styles.sellerText}>@{item.seller}</Text>
            )}
          </View>
        </LinearGradient>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.white} />
      
      <ScrollView>
        {/* Profile Header */}
        <View style={styles.header}>
          <LinearGradient
            colors={COLORS.gradient.blue}
            style={styles.headerGradient}
          >
            <View style={styles.headerContent}>
              <View style={styles.avatarContainer}>
                <Image source={{ uri: MOCK_USER.avatar }} style={styles.avatar} />
                {MOCK_USER.verified && (
                  <View style={styles.verifiedBadge}>
                    <Icon name="verified" size={16} color={COLORS.white} />
                  </View>
                )}
              </View>
              
              <View style={styles.userInfo}>
                <Text style={styles.username}>@{MOCK_USER.username}</Text>
                <Text style={styles.memberSince}>Member since {MOCK_USER.memberSince}</Text>
              </View>
            </View>
          </LinearGradient>
          
          <View style={styles.profileDetails}>
            <Text style={styles.bio}>{MOCK_USER.bio}</Text>
            
            {/* Stats */}
            <View style={styles.stats}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{MOCK_USER.stats.listings}</Text>
                <Text style={styles.statLabel}>Listings</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{MOCK_USER.stats.sold}</Text>
                <Text style={styles.statLabel}>Sold</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{MOCK_USER.stats.followers}</Text>
                <Text style={styles.statLabel}>Followers</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{MOCK_USER.stats.following}</Text>
                <Text style={styles.statLabel}>Following</Text>
              </View>
            </View>

            {/* Edit Profile Button */}
            <TouchableOpacity style={styles.editButton}>
              <Icon name="edit" size={20} color={COLORS.primary} />
              <Text style={styles.editButtonText}>Edit Profile</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Content Tabs */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'listings' && styles.activeTab]}
            onPress={() => setActiveTab('listings')}
          >
            <View style={[styles.tabIconContainer, activeTab === 'listings' && styles.activeTabIcon]}>
              <Icon
                name="store"
                size={20}
                color={activeTab === 'listings' ? COLORS.text_inverse : COLORS.text_light}
              />
            </View>
            <Text style={[styles.tabLabel, activeTab === 'listings' && styles.activeTabLabel]}>
              Listings
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.tab, activeTab === 'appraisals' && styles.activeTab]}
            onPress={() => setActiveTab('appraisals')}
          >
            <View style={[styles.tabIconContainer, activeTab === 'appraisals' && styles.activeTabIcon]}>
              <Icon
                name="auto-awesome"
                size={20}
                color={activeTab === 'appraisals' ? COLORS.white : COLORS.gray500}
              />
            </View>
            <Text style={[styles.tabLabel, activeTab === 'appraisals' && styles.activeTabLabel]}>
              Appraisals
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.tab, activeTab === 'liked' && styles.activeTab]}
            onPress={() => setActiveTab('liked')}
          >
            <View style={[styles.tabIconContainer, activeTab === 'liked' && styles.activeTabIcon]}>
              <Icon
                name="favorite"
                size={20}
                color={activeTab === 'liked' ? COLORS.white : COLORS.gray500}
              />
            </View>
            <Text style={[styles.tabLabel, activeTab === 'liked' && styles.activeTabLabel]}>
              Liked
            </Text>
          </TouchableOpacity>
        </View>

        {/* Content Grid */}
        <View style={styles.gridContainer}>
          {MOCK_ITEMS[activeTab].map(item => renderGridItem(item, activeTab))}
        </View>
        
        <View style={styles.bottomPadding} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray50,
  },
  header: {
    backgroundColor: COLORS.white,
    marginBottom: 16,
  },
  headerGradient: {
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    position: 'relative',
    marginRight: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: COLORS.white,
  },
  verifiedBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.success_light,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  userInfo: {
    flex: 1,
  },
  username: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 4,
  },
  memberSince: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '500',
  },
  profileDetails: {
    padding: 20,
  },
  bio: {
    fontSize: 16,
    color: COLORS.gray600,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    backgroundColor: COLORS.gray50,
    borderRadius: 16,
    padding: 16,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.black,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.gray500,
    fontWeight: '500',
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.gray100,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.gray200,
  },
  editButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    borderRadius: 16,
    padding: 8,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 12,
  },
  activeTab: {
    backgroundColor: COLORS.primary,
  },
  tabIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  activeTabIcon: {
    backgroundColor: COLORS.primary_light,
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '500',
    color: COLORS.gray500,
  },
  activeTabLabel: {
    color: COLORS.white,
    fontWeight: '600',
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    justifyContent: 'space-between',
  },
  gridItem: {
    width: ITEM_WIDTH,
    height: ITEM_WIDTH,
    marginBottom: 12,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: COLORS.gray200,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  itemImage: {
    width: '100%',
    height: '100%',
    backgroundColor: COLORS.gray200,
  },
  itemOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: '50%',
    justifyContent: 'flex-end',
  },
  itemInfo: {
    padding: 8,
  },
  soldBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: COLORS.error,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  soldText: {
    color: COLORS.text_inverse,
    fontSize: 10,
    fontWeight: '700',
  },
  itemPrice: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 2,
  },
  confidenceBadge: {
    backgroundColor: COLORS.success,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  confidenceText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: '600',
  },
  sellerText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: '500',
    opacity: 0.8,
  },
  bottomPadding: {
    height: 100,
  },
});

export default ProfileScreen; 