'use client';

import React, { useState, useRef, useCallback } from 'react';
import AppLayout from '@/components/AppLayout';
import Image from 'next/image';
import { Camera, RotateCcw, Upload, X } from 'lucide-react';

export default function CameraPage() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Unable to access camera. Please check permissions.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setIsStreaming(false);
    }
  }, []);

  const capturePhoto = useCallback(() => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        const imageData = canvas.toDataURL('image/jpeg', 0.9);
        setCapturedImage(imageData);
        setIsProcessing(true);
        
        // Simulate AI processing
        setTimeout(() => {
          setIsProcessing(false);
        }, 2000);
      }
    }
  }, []);

  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
    setIsProcessing(false);
  }, []);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setCapturedImage(e.target?.result as string);
        setIsProcessing(true);
        
        // Simulate AI processing
        setTimeout(() => {
          setIsProcessing(false);
        }, 2000);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  return (
    <AppLayout>
      <div className="min-h-screen bg-black text-white">
        {!capturedImage ? (
          <div className="relative w-full h-screen">
            {/* Camera view */}
            <div className="relative w-full h-full overflow-hidden">
              {isStreaming ? (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-zinc-900 flex items-center justify-center">
                  <div className="text-center">
                    <Camera size={64} className="mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-400 mb-6">Camera not active</p>
                    <button
                      onClick={startCamera}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-full font-semibold transition-colors"
                    >
                      Start Camera
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {/* Camera controls */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
              <div className="flex items-center justify-center space-x-8">
                {/* Upload button */}
                <label className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center cursor-pointer hover:bg-white/30 transition-colors">
                  <Upload size={24} />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
                
                {/* Capture button */}
                <button
                  onClick={capturePhoto}
                  disabled={!isStreaming}
                  className="w-20 h-20 bg-white rounded-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 transition-colors"
                >
                  <div className="w-16 h-16 bg-white border-4 border-black rounded-full" />
                </button>
                
                {/* Stop camera button */}
                <button
                  onClick={stopCamera}
                  className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center hover:bg-red-500/30 transition-colors"
                >
                  <X size={24} className="text-red-500" />
                </button>
              </div>
              
              <div className="text-center mt-4">
                <p className="text-white text-sm">Position your item in the frame and tap to capture</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="relative w-full h-screen">
            {/* Captured image */}
            <div className="relative w-full h-full">
              <Image
                src={capturedImage}
                alt="Captured item"
                fill
                className="object-cover"
              />
              
              {isProcessing && (
                <div className="absolute inset-0 bg-black/75 flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-white text-lg font-semibold">Analyzing your item...</p>
                    <p className="text-gray-300 text-sm mt-2">AI is processing the image</p>
                  </div>
                </div>
              )}
            </div>
            
            {/* Results overlay */}
            {!isProcessing && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-6">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 mb-4">
                  <h3 className="text-xl font-bold text-white mb-2">Analysis Complete!</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-300">Category:</span>
                      <span className="text-white font-semibold">Vintage Watch</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Estimated Value:</span>
                      <span className="text-green-500 font-bold">$2,500 - $4,000</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Confidence:</span>
                      <span className="text-blue-500 font-semibold">87%</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-4">
                  <button
                    onClick={retakePhoto}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-3 rounded-lg font-semibold transition-colors flex items-center justify-center"
                  >
                    <RotateCcw size={20} className="mr-2" />
                    Retake
                  </button>
                  <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-semibold transition-colors">
                    Share Result
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
        
        <canvas ref={canvasRef} className="hidden" />
      </div>
    </AppLayout>
  );
}
