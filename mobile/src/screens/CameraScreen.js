import React, { useState } from 'react';
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Text,
  Alert,
  Platform,
  StatusBar,
} from 'react-native';
import { MaterialIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';

const CameraScreen = () => {
  const navigation = useNavigation();
  const [flash, setFlash] = useState(false);

  const takePicture = async () => {
    // Mock photo data for prototype
    const mockPhotoData = {
      uri: 'https://picsum.photos/400/400?random=7',
      base64: null,
    };

    Alert.alert(
      'Photo Captured!',
      'This is a prototype. In the real app, this would use the device camera.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Continue to Preview',
          onPress: () => navigation.navigate('Preview', { photo: mockPhotoData }),
        },
      ]
    );
  };

  const toggleFlash = () => {
    setFlash(!flash);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {/* Mock Camera View */}
      <LinearGradient
        colors={[COLORS.surface, COLORS.gray800, COLORS.surface]}
        style={styles.mockCameraView}
      >
        <View style={styles.mockContent}>
          <Icon name="camera-alt" size={80} color={COLORS.primary_light} />
          <Text style={styles.mockText}>Camera Preview</Text>
          <Text style={styles.mockSubtext}>
            Position your item in the frame
          </Text>
        </View>
        
        {/* Viewfinder overlay */}
        <View style={styles.viewfinder}>
          <View style={styles.viewfinderCorner} />
          <View style={[styles.viewfinderCorner, styles.topRight]} />
          <View style={[styles.viewfinderCorner, styles.bottomLeft]} />
          <View style={[styles.viewfinderCorner, styles.bottomRight]} />
        </View>
      </LinearGradient>

      {/* Camera Controls */}
      <View style={styles.controls}>
        {/* Top Controls */}
        <View style={styles.topControls}>
          <TouchableOpacity 
            style={styles.controlButton}
            onPress={() => navigation.goBack()}
          >
            <Icon name="close" size={24} color={COLORS.white} />
          </TouchableOpacity>
          
          <Text style={styles.titleText}>Capture Item</Text>
          
          <TouchableOpacity 
            style={[styles.controlButton, flash && styles.activeButton]}
            onPress={toggleFlash}
          >
            <Icon 
              name={flash ? "flash-on" : "flash-off"} 
              size={24} 
              color={flash ? COLORS.warning_light : COLORS.white}
            />
          </TouchableOpacity>
        </View>

        {/* Bottom Controls */}
        <View style={styles.bottomControls}>
          <TouchableOpacity style={styles.galleryButton}>
            <Icon name="photo-library" size={24} color={COLORS.white} />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.captureButton}
            onPress={takePicture}
          >
            <LinearGradient
              colors={COLORS.gradient.orange}
              style={styles.captureButtonInner}
            >
              <Icon name="camera" size={32} color={COLORS.white} />
            </LinearGradient>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.flipButton}>
            <Icon name="flip-camera-ios" size={24} color={COLORS.white} />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.black,
  },
  mockCameraView: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  mockContent: {
    alignItems: 'center',
    zIndex: 1,
  },
  mockText: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
    marginTop: 24,
    marginBottom: 12,
  },
  mockSubtext: {
    fontSize: 16,
    color: COLORS.gray300,
    textAlign: 'center',
    paddingHorizontal: 40,
    fontWeight: '500',
  },
  viewfinder: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 20,
  },
  viewfinderCorner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: COLORS.primary_light,
    borderWidth: 3,
    borderRightWidth: 0,
    borderBottomWidth: 0,
    borderTopLeftRadius: 8,
  },
  topRight: {
    top: 0,
    right: 0,
    borderRightWidth: 3,
    borderLeftWidth: 0,
    borderTopRightRadius: 8,
    borderTopLeftRadius: 0,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 3,
    borderTopWidth: 0,
    borderBottomLeftRadius: 8,
    borderTopLeftRadius: 0,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderTopWidth: 0,
    borderLeftWidth: 0,
    borderBottomRightRadius: 8,
    borderTopLeftRadius: 0,
  },
  controls: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'space-between',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 20,
  },
  titleText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
  },
  controlButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.glassDark,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activeButton: {
    backgroundColor: COLORS.warning_light + '40',
  },
  bottomControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingBottom: Platform.OS === 'ios' ? 40 : 30,
  },
  galleryButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.glassDark,
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: COLORS.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  captureButtonInner: {
    width: 68,
    height: 68,
    borderRadius: 34,
    justifyContent: 'center',
    alignItems: 'center',
  },
  flipButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.glassDark,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default CameraScreen; 