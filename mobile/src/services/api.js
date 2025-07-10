import axios from 'axios';
import { Platform } from 'react-native';

// Helper to get correct base URL depending on platform/emulator
const getDefaultBaseUrl = () => {
  if (Platform.OS === 'android') {
    // Android emulator uses 10.0.2.2 to reach host machine
    return 'http://10.0.2.2:8000';
  }
  // iOS simulator can use localhost directly, but if that fails, try machine IP
  // For iOS simulator, we can also use the machine's local IP
  return 'http://127.0.0.1:8000';
};

export const BASE_URL = getDefaultBaseUrl();

console.log('API Base URL:', BASE_URL);

// --- Helper API calls ------------------------------------------------------

export const submitAppraisal = async (imageUri) => {
  console.log('Submitting appraisal for image:', imageUri);
  
  try {
    const formData = new FormData();
    
    // React Native requires this specific format
    formData.append('image_file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'photo.jpg',
    });

    console.log('FormData created, sending to:', `${BASE_URL}/api/v1/appraisal/submit`);

    const response = await axios.post(`${BASE_URL}/api/v1/appraisal/submit`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Accept': 'application/json',
      },
      timeout: 30000, // 30 second timeout
    });

    console.log('Appraisal submission response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error submitting appraisal:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
    }
    throw new Error(`Failed to submit appraisal: ${error.message}`);
  }
};

export const checkAppraisalStatus = async (appraisalId) => {
  console.log('Checking status for appraisal:', appraisalId);
  
  try {
    const response = await axios.get(`${BASE_URL}/api/v1/appraisal/${appraisalId}/status`);
    console.log('Status response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error checking appraisal status:', error);
    throw new Error(`Failed to check appraisal status: ${error.message}`);
  }
};

export const getAppraisalResult = async (appraisalId) => {
  console.log('Getting result for appraisal:', appraisalId);
  
  try {
    const response = await axios.get(`${BASE_URL}/api/v1/appraisal/${appraisalId}/result`);
    console.log('Result response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getting appraisal result:', error);
    throw new Error(`Failed to get appraisal result: ${error.message}`);
  }
};

// --- Higher-level helper ----------------------------------------------------

export const submitAppraisalAndWait = async (imageUri, { maxAttempts = 15, intervalMs = 2000 } = {}) => {
  console.log('Starting full appraisal process for:', imageUri);
  
  try {
    // Submit the appraisal
    const submission = await submitAppraisal(imageUri);
    const { appraisal_id } = submission;
    console.log('Appraisal submitted with ID:', appraisal_id);

    // Poll for completion
    let attempts = 0;
    while (attempts < maxAttempts) {
      console.log(`Checking appraisal status, attempt ${attempts + 1}/${maxAttempts}`);
      
      const status = await checkAppraisalStatus(appraisal_id);
      
      if (status.status === 'completed') {
        console.log('Appraisal completed, fetching results...');
        const result = await getAppraisalResult(appraisal_id);
        console.log('Final result received:', result);
        return result;
      }
      
      // Wait before next attempt
      console.log(`Status: ${status.status}, waiting ${intervalMs}ms before retry...`);
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
      attempts += 1;
    }
    
    throw new Error('Appraisal timed out – please try again');
  } catch (error) {
    console.error('Full appraisal process failed:', error);
    throw error;
  }
}; 