"""
Mock AI Service for development - bypasses Google Cloud dependencies
"""
from typing import Dict, Optional, List
from datetime import datetime
import uuid
import time

from app.services.base_service import BaseService
from app.utils.logging import get_logger

logger = get_logger(__name__)

class MockAIService(BaseService):
    """Mock AI Service for development that doesn't require Google Cloud"""
    
    def __init__(self, db=None):
        super().__init__(db)
        logger.info("Initialized MockAIService for development")
    
    def get_appraisal_from_agent(
        self,
        image_uri: str,
        user_query: str = "Analyze the item in the image and provide an estimated appraisal value and key details."
    ) -> Dict:
        """
        Mock implementation for getting an appraisal from the Vertex AI Agent Engine.
        Returns a predefined, structured response to simulate a successful agent call.
        """
        logger.info(f"Performing mock agent appraisal for image URI: {image_uri}")
        
        # Simulate a short delay to mimic network latency
        time.sleep(0.2)
        
        # Return a structured mock response that the AppraisalService expects
        return {
            "raw_response": "Based on the analysis, the estimated value is $450. The price range is likely between $420 and $480. This is a popular model in good condition.",
            "estimated_value": 450.00,
            "price_range": {
                "min": 420.00,
                "max": 480.00
            },
            "confidence_score": 0.88,
            "currency": "USD",
            "details": "This appears to be a recent smartphone model, likely an iPhone 12, in good cosmetic condition. The market for this device is active.",
            "agent_id": "mock-agent-v1"
        }

    def validate_input(self, data) -> bool:
        """Validate input for AI processing"""
        return isinstance(data, dict) and ('file_content' in data or 'image_uri' in data)
    
    def process(self, data: Dict) -> Dict:
        """Process data - main entry point"""
        image_uri = data.get('image_uri')
        if not image_uri:
            raise ValueError("image_uri is required for mock agent processing.")
            
        return self.get_appraisal_from_agent(
            image_uri=image_uri,
            user_query=data.get('user_query', "Provide an appraisal for the item in the image.")
        )
    
    def analyze_image_complete(
        self,
        file_content: Optional[bytes] = None,
        image_uri: Optional[str] = None,
        analysis_options: Optional[Dict] = None
    ) -> Dict:
        """
        DEPRECATED: This method is deprecated in favor of get_appraisal_from_agent.
        It is kept for potential backward compatibility or for a different analysis path.
        
        Complete image analysis with mock data
        """
        logger.warning("The 'analyze_image_complete' method is deprecated for agent-based appraisals.")
        logger.info("Performing mock image analysis")
        
        # Simulate processing time
        time.sleep(0.5)
        
        # Return mock analysis results
        return {
            'vision_analysis': {
                'objects': [
                    {'name': 'phone', 'confidence': 0.95, 'bounding_box': [0.1, 0.1, 0.8, 0.8]},
                    {'name': 'electronic device', 'confidence': 0.88, 'bounding_box': [0.1, 0.1, 0.8, 0.8]}
                ],
                'labels': [
                    {'description': 'Mobile phone', 'confidence': 0.95},
                    {'description': 'Electronics', 'confidence': 0.90},
                    {'description': 'Technology', 'confidence': 0.85}
                ],
                'text': {
                    'full_text': 'iPhone 12',
                    'blocks': [
                        {'text': 'iPhone', 'confidence': 0.92},
                        {'text': '12', 'confidence': 0.89}
                    ]
                },
                'faces': [],
                'colors': [
                    {'color': 'black', 'percentage': 60},
                    {'color': 'silver', 'percentage': 40}
                ]
            },
            'embeddings': {
                'feature_vector': [0.1, 0.2, 0.3, 0.4, 0.5] * 20,  # Mock 100-dim vector
                'model_version': 'mock-v1.0',
                'extraction_method': 'mock_features'
            },
            'extracted_features': {
                'dominant_objects': ['phone', 'electronic device'],
                'text_detected': ['iPhone', '12'],
                'color_profile': 'dark_metallic',
                'estimated_category': 'electronics',
                'brand_detected': 'Apple',
                'model_detected': 'iPhone 12'
            },
            'confidence_score': 0.92,
            'processing_time': 0.5,
            'analysis_id': str(uuid.uuid4()),
            'processed_at': datetime.utcnow().isoformat()
        }
    
    def extract_features(self, file_content: bytes, options: Optional[Dict] = None) -> Dict:
        """Extract features from image - mock implementation"""
        return {
            'features': [0.1, 0.2, 0.3, 0.4, 0.5] * 20,
            'feature_count': 100,
            'extraction_method': 'mock_cnn'
        }
    
    def detect_objects(self, file_content: bytes, options: Optional[Dict] = None) -> List[Dict]:
        """Detect objects in image - mock implementation"""
        return [
            {'name': 'phone', 'confidence': 0.95, 'bounding_box': [0.1, 0.1, 0.8, 0.8]},
            {'name': 'electronic device', 'confidence': 0.88, 'bounding_box': [0.1, 0.1, 0.8, 0.8]}
        ]
    
    def analyze_text(self, file_content: bytes, options: Optional[Dict] = None) -> Dict:
        """Analyze text in image - mock implementation"""
        return {
            'full_text': 'iPhone 12',
            'blocks': [
                {'text': 'iPhone', 'confidence': 0.92},
                {'text': '12', 'confidence': 0.89}
            ]
        }
    
    def health_check(self) -> bool:
        """Health check for mock AI service"""
        return True