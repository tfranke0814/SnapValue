import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
  Platform,
  StatusBar,
  Alert,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { useNavigation, useRoute } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';

const { width: screenWidth } = Dimensions.get('window');

const ResultScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { photo, appraisalResult } = route.params || {};

  // Safety check for required parameters
  if (!photo || !appraisalResult) {
    navigation.goBack();
    return null;
  }

  const handleListItem = () => {
    // Show options for listing the item
    Alert.alert(
      'List Your Item',
      'Choose how you want to list this item:',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Create Listing',
          onPress: () => {
            // TODO: Navigate to listing creation screen when implemented
            Alert.alert(
              'Coming Soon!',
              'Listing creation feature will be available soon. For now, you can save this appraisal or share it with others.',
              [{ text: 'OK' }]
            );
          },
        },
        {
          text: 'Save Appraisal',
          onPress: () => {
            Alert.alert(
              'Appraisal Saved!',
              'Your appraisal has been saved to your profile.',
              [{ text: 'OK' }]
            );
          },
        },
      ]
    );
  };

  const handleGoBack = () => {
    navigation.goBack();
  };

  const handleRetakePhoto = () => {
    // Navigate back to camera screen
    navigation.navigate('CameraMain');
  };

  const handleGoHome = () => {
    // Navigate to main tabs (Home screen)
    navigation.navigate('ForYou');
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.white} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={handleGoBack}
        >
          <Icon name="arrow-back" size={24} color={COLORS.black} />
        </TouchableOpacity>
        
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Appraisal Complete</Text>
          <Text style={styles.headerSubtitle}>AI Analysis Results</Text>
        </View>
        
        <TouchableOpacity style={styles.shareButton}>
          <Icon name="share" size={24} color={COLORS.black} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {/* Item Image */}
        <View style={styles.imageContainer}>
          <Image
            source={{ uri: photo.uri }}
            style={styles.itemImage}
            resizeMode="cover"
          />
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.3)']}
            style={styles.imageOverlay}
          />
        </View>

        {/* Estimated Value */}
        <View style={styles.valueContainer}>
          <View style={styles.valueHeader}>
            <Icon name="auto-awesome" size={32} color={COLORS.accent_orange} />
            <Text style={styles.valueLabel}>Estimated Value</Text>
          </View>
          
          <Text style={styles.valueAmount}>
            ${appraisalResult.estimatedValue.toLocaleString()}
          </Text>
          
          <View style={styles.confidenceContainer}>
            <View style={styles.confidenceBar}>
              <LinearGradient
                colors={COLORS.gradient.success}
                style={[
                  styles.confidenceFill,
                  { width: `${appraisalResult.confidence * 100}%` }
                ]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              />
            </View>
            <Text style={styles.confidenceText}>
              {Math.round(appraisalResult.confidence * 100)}% Confidence
            </Text>
          </View>
        </View>

        {/* Item Details */}
        <View style={styles.detailsContainer}>
          <Text style={styles.sectionTitle}>Item Details</Text>
          
          <View style={styles.detailRow}>
            <View style={styles.detailIcon}>
              <Icon name="category" size={20} color={COLORS.primary} />
            </View>
            <Text style={styles.detailLabel}>Category</Text>
            <Text style={styles.detailValue}>{appraisalResult.category}</Text>
          </View>
          
          <View style={styles.detailRow}>
            <View style={styles.detailIcon}>
              <Icon name="star" size={20} color={COLORS.accent_orange} />
            </View>
            <Text style={styles.detailLabel}>Condition</Text>
            <Text style={styles.detailValue}>{appraisalResult.condition}</Text>
          </View>
        </View>

        {/* Similar Items */}
         <View style={styles.similarItemsContainer}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Similar Items</Text>
            <Text style={styles.sectionSubtitle}>Market comparisons</Text>
          </View>
          
          {appraisalResult.similarItems.map((item, index) => (
            <View key={index} style={styles.similarItem}>
              <View style={styles.similarItemLeft}>
                <View style={styles.similarItemIcon}>
                  <Icon name="trending-up" size={16} color={COLORS.success} />
                </View>
                <View style={styles.similarItemInfo}>
                  <Text style={styles.similarItemCondition}>
                    {item.condition} Condition
                  </Text>
                  <Text style={styles.similarItemPrice}>
                    ${item.price.toLocaleString()}
                  </Text>
                </View>
              </View>
              
              <TouchableOpacity style={styles.viewButton}>
                <Text style={styles.viewButtonText}>View</Text>
                <Icon name="chevron-right" size={16} color={COLORS.primary} />
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtonsContainer}>
          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={handleRetakePhoto}
          >
            <Icon name="camera-alt" size={20} color={COLORS.primary} />
            <Text style={styles.secondaryButtonText}>Retake Photo</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={handleGoHome}
          >
            <Icon name="home" size={20} color={COLORS.primary} />
            <Text style={styles.secondaryButtonText}>Go Home</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.bottomPadding} />
      </ScrollView>

      {/* Bottom Action Button */}
      <View style={styles.bottomContainer}>
        <TouchableOpacity 
          style={styles.listItemButton}
          onPress={handleListItem}
        >
          <LinearGradient
            colors={COLORS.gradient.orange}
            style={styles.listItemGradient}
          >
            <Icon name="add-circle-outline" size={24} color={COLORS.white} />
            <Text style={styles.listItemText}>List this Item</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
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
    color: COLORS.gray500,
    marginTop: 2,
  },
  shareButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
  },
  imageContainer: {
    position: 'relative',
    marginBottom: 20,
  },
  itemImage: {
    width: screenWidth,
    height: screenWidth,
    backgroundColor: COLORS.gray200,
  },
  imageOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: '30%',
  },
  valueContainer: {
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  valueHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  valueLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.black,
    marginLeft: 8,
  },
  valueAmount: {
    fontSize: 42,
    fontWeight: '800',
    color: COLORS.primary_dark,
    marginBottom: 20,
  },
  confidenceContainer: {
    width: '100%',
    alignItems: 'center',
  },
  confidenceBar: {
    width: '100%',
    height: 12,
    backgroundColor: COLORS.gray200,
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 12,
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 6,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.success_light,
  },
  detailsContainer: {
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.black,
    marginBottom: 16,
  },
  sectionHeader: {
    marginBottom: 16,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: COLORS.gray500,
    marginTop: 4,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  detailIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  detailLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.gray600,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.black,
  },
  similarItemsContainer: {
    backgroundColor: COLORS.white,
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  similarItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray100,
  },
  similarItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  similarItemIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.gray100,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  similarItemInfo: {
    marginLeft: 12,
  },
  similarItemCondition: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gray600,
    marginBottom: 4,
  },
  similarItemPrice: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.black,
  },
  viewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.gray100,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  viewButtonText: {
    color: COLORS.primary,
    fontSize: 12,
    fontWeight: '600',
    marginRight: 4,
  },
  actionButtonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginHorizontal: 16,
    marginBottom: 16,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    flex: 0.48,
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  secondaryButtonText: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  bottomPadding: {
    height: 100,
  },
  bottomContainer: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    paddingBottom: 32,
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray200,
  },
  listItemButton: {
    borderRadius: 16,
    shadowColor: COLORS.accent_orange,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  listItemGradient: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 16,
  },
  listItemText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: '700',
    marginLeft: 8,
  },
});

export default ResultScreen; 