import React, { useState } from 'react';
import {
  View,
  Image,
  TouchableOpacity,
  StyleSheet,
  Text,
  ActivityIndicator,
  Dimensions,
  Platform,
  StatusBar,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { useNavigation, useRoute } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const PreviewScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { photo } = route.params || {};
  const [loading, setLoading] = useState(false);

  // Safety check for photo parameter
  if (!photo) {
    navigation.goBack();
    return null;
  }

  const handleAppraise = async () => {
    setLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      setLoading(false);
      // Mock appraisal result
      navigation.navigate('Result', {
        photo: photo,
        appraisalResult: {
          estimatedValue: 1200,
          confidence: 0.85,
          category: 'Electronics',
          condition: 'Good',
          similarItems: [
            { price: 1100, condition: 'Fair', link: '#' },
            { price: 1300, condition: 'Excellent', link: '#' },
          ],
        },
      });
    }, 2000);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      <Image
        source={{ uri: photo.uri }}
        style={styles.preview}
        resizeMode="contain"
      />

      {/* Overlay controls */}
      <View style={styles.controls}>
        {/* Top bar */}
        <View style={styles.topBar}>
          <TouchableOpacity
            style={styles.controlButton}
            onPress={() => navigation.goBack()}
          >
            <Icon name="close" size={24} color={COLORS.white} />
          </TouchableOpacity>
          
          <Text style={styles.titleText}>Preview</Text>
          
          <View style={styles.placeholder} />
        </View>

        {/* Bottom bar */}
        <View style={styles.bottomBar}>
          <TouchableOpacity
            style={styles.retakeButton}
            onPress={() => navigation.goBack()}
          >
            <Icon name="replay" size={24} color={COLORS.white} />
            <Text style={styles.buttonText}>Retake</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.appraiseButton,
              loading && styles.appraiseButtonDisabled,
            ]}
            onPress={handleAppraise}
            disabled={loading}
          >
            {loading ? (
              <>
                <ActivityIndicator color={COLORS.white} size="small" />
                <Text style={[styles.buttonText, { marginLeft: 8 }]}>Analyzing...</Text>
              </>
            ) : (
              <>
                <Icon name="auto-awesome" size={24} color={COLORS.white} />
                <Text style={styles.buttonText}>Get Appraisal</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Processing overlay */}
      {loading && (
        <View style={styles.processingOverlay}>
          <LinearGradient
            colors={['transparent', COLORS.overlayDark]}
            style={styles.processingGradient}
          >
            <View style={styles.processingContent}>
              <Icon name="auto-awesome" size={48} color={COLORS.accent_orange} />
              <Text style={styles.processingText}>AI is analyzing your item...</Text>
              <Text style={styles.processingSubtext}>This may take a few moments</Text>
            </View>
          </LinearGradient>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.black,
  },
  preview: {
    flex: 1,
    width: screenWidth,
    height: screenHeight,
  },
  controls: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'space-between',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 20,
  },
  controlButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.glassDark,
    justifyContent: 'center',
    alignItems: 'center',
  },
  titleText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
  },
  placeholder: {
    width: 48,
  },
  bottomBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingBottom: Platform.OS === 'ios' ? 40 : 30,
  },
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.glassDark,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    minWidth: 100,
    justifyContent: 'center',
  },
  appraiseButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accent_orange,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
    minWidth: 140,
    justifyContent: 'center',
    shadowColor: COLORS.accent_orange,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  appraiseButtonDisabled: {
    backgroundColor: COLORS.gray600,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  processingOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  processingContent: {
    alignItems: 'center',
    backgroundColor: COLORS.glassDark,
    borderRadius: 20,
    padding: 32,
    minWidth: 200,
  },
  processingText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    marginTop: 16,
    textAlign: 'center',
  },
  processingSubtext: {
    fontSize: 14,
    color: COLORS.gray300,
    marginTop: 8,
    textAlign: 'center',
  },
});

export default PreviewScreen; 