import base64
from typing import Dict, List, Optional, Any
from google.cloud import vision
from google.cloud.exceptions import GoogleCloudError
import json

from app.core.config import settings
from app.services.base_service import BaseService
from app.utils.exceptions import ExternalServiceError, ConfigurationError, AIProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry

logger = get_logger(__name__)

class VisionService(BaseService):
    """Google Cloud Vision AI service for image analysis"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Vision client"""
        try:
            # Check if credentials are configured
            if not settings.GOOGLE_CLOUD_PROJECT:
                raise ConfigurationError("GOOGLE_CLOUD_PROJECT not configured")
            
            # Initialize client
            self.client = vision.ImageAnnotatorClient()
            
            log_service_call("VisionService", "initialize_client", 
                           project=settings.GOOGLE_CLOUD_PROJECT)
            
        except Exception as e:
            self.log_error(e, "initialize_client")
            raise ConfigurationError(f"Failed to initialize Google Cloud Vision: {str(e)}")
    
    def validate_input(self, data) -> bool:
        """Validate input for vision processing"""
        if not isinstance(data, dict):
            return False
        
        # Must have either file_content or image_uri
        return 'file_content' in data or 'image_uri' in data
    
    def process(self, data: Dict) -> Dict:
        """Process image for vision analysis - main entry point"""
        if not self.validate_input(data):
            raise AIProcessingError("Invalid input data for vision processing")
        
        return self.analyze_image(
            data.get('file_content'),
            data.get('image_uri'),
            data.get('features', ['objects', 'labels', 'text', 'faces'])
        )
    
    def analyze_image(
        self,
        file_content: Optional[bytes] = None,
        image_uri: Optional[str] = None,
        features: List[str] = None
    ) -> Dict:
        """
        Comprehensive image analysis using Google Cloud Vision
        
        Args:
            file_content: Image content as bytes
            image_uri: URI of image (for GCS images)
            features: List of features to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if features is None:
            features = ['objects', 'labels', 'text', 'faces']
        
        log_service_call("VisionService", "analyze_image", 
                        features=features, has_content=file_content is not None)
        
        try:
            # Prepare image
            if file_content:
                image = vision.Image(content=file_content)
            elif image_uri:
                image = vision.Image()
                image.source.image_uri = image_uri
            else:
                raise AIProcessingError("Either file_content or image_uri must be provided")
            
            # Perform analysis
            results = {}
            
            if 'objects' in features:
                results['objects'] = self._detect_objects(image)
            
            if 'labels' in features:
                results['labels'] = self._detect_labels(image)
            
            if 'text' in features:
                results['text'] = self._detect_text(image)
            
            if 'faces' in features:
                results['faces'] = self._detect_faces(image)
            
            if 'properties' in features:
                results['properties'] = self._analyze_image_properties(image)
            
            if 'web' in features:
                results['web'] = self._detect_web_entities(image)
            
            # Add summary
            results['summary'] = self._generate_summary(results)
            
            log_service_result("VisionService", "analyze_image", True, 
                             features_analyzed=len(results))
            
            return results
            
        except GoogleCloudError as e:
            self.log_error(e, "analyze_image")
            raise ExternalServiceError("Google Cloud Vision", f"Vision analysis failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "analyze_image")
            raise AIProcessingError(f"Vision analysis failed: {str(e)}")
    
    def _detect_objects(self, image: vision.Image) -> List[Dict]:
        """Detect objects in image"""
        try:
            response = self.client.object_localization(image=image)
            objects = response.localized_object_annotations
            
            detected_objects = []
            for obj in objects:
                vertices = []
                for vertex in obj.bounding_poly.normalized_vertices:
                    vertices.append({
                        'x': vertex.x,
                        'y': vertex.y
                    })
                
                detected_objects.append({
                    'name': obj.name,
                    'confidence': obj.score,
                    'bounding_poly': vertices,
                    'mid': obj.mid if hasattr(obj, 'mid') else None
                })
            
            return detected_objects
            
        except Exception as e:
            self.log_error(e, "_detect_objects")
            return []
    
    def _detect_labels(self, image: vision.Image) -> List[Dict]:
        """Detect labels in image"""
        try:
            response = self.client.label_detection(image=image)
            labels = response.label_annotations
            
            detected_labels = []
            for label in labels:
                detected_labels.append({
                    'description': label.description,
                    'confidence': label.score,
                    'mid': label.mid,
                    'topicality': label.topicality
                })
            
            return detected_labels
            
        except Exception as e:
            self.log_error(e, "_detect_labels")
            return []
    
    def _detect_text(self, image: vision.Image) -> Dict:
        """Detect text in image"""
        try:
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                return {'full_text': '', 'text_blocks': []}
            
            # First annotation contains full text
            full_text = texts[0].description
            
            # Remaining annotations are individual text blocks
            text_blocks = []
            for text in texts[1:]:
                vertices = []
                for vertex in text.bounding_poly.vertices:
                    vertices.append({
                        'x': vertex.x,
                        'y': vertex.y
                    })
                
                text_blocks.append({
                    'text': text.description,
                    'bounding_poly': vertices
                })
            
            return {
                'full_text': full_text,
                'text_blocks': text_blocks
            }
            
        except Exception as e:
            self.log_error(e, "_detect_text")
            return {'full_text': '', 'text_blocks': []}
    
    def _detect_faces(self, image: vision.Image) -> List[Dict]:
        """Detect faces in image"""
        try:
            response = self.client.face_detection(image=image)
            faces = response.face_annotations
            
            detected_faces = []
            for face in faces:
                vertices = []
                for vertex in face.bounding_poly.vertices:
                    vertices.append({
                        'x': vertex.x,
                        'y': vertex.y
                    })
                
                detected_faces.append({
                    'confidence': face.detection_confidence,
                    'bounding_poly': vertices,
                    'emotions': {
                        'joy': face.joy_likelihood.name,
                        'sorrow': face.sorrow_likelihood.name,
                        'anger': face.anger_likelihood.name,
                        'surprise': face.surprise_likelihood.name
                    },
                    'landmarks': self._extract_face_landmarks(face.landmarks)
                })
            
            return detected_faces
            
        except Exception as e:
            self.log_error(e, "_detect_faces")
            return []
    
    def _extract_face_landmarks(self, landmarks) -> List[Dict]:
        """Extract face landmarks"""
        landmark_list = []
        for landmark in landmarks:
            landmark_list.append({
                'type': landmark.type_.name,
                'position': {
                    'x': landmark.position.x,
                    'y': landmark.position.y,
                    'z': landmark.position.z
                }
            })
        return landmark_list
    
    def _analyze_image_properties(self, image: vision.Image) -> Dict:
        """Analyze image properties"""
        try:
            response = self.client.image_properties(image=image)
            properties = response.image_properties_annotation
            
            # Extract dominant colors
            dominant_colors = []
            for color in properties.dominant_colors.colors:
                dominant_colors.append({
                    'color': {
                        'red': color.color.red,
                        'green': color.color.green,
                        'blue': color.color.blue
                    },
                    'score': color.score,
                    'pixel_fraction': color.pixel_fraction
                })
            
            return {
                'dominant_colors': dominant_colors
            }
            
        except Exception as e:
            self.log_error(e, "_analyze_image_properties")
            return {}
    
    def _detect_web_entities(self, image: vision.Image) -> Dict:
        """Detect web entities and similar images"""
        try:
            response = self.client.web_detection(image=image)
            web_detection = response.web_detection
            
            # Web entities
            web_entities = []
            for entity in web_detection.web_entities:
                web_entities.append({
                    'entity_id': entity.entity_id,
                    'description': entity.description,
                    'score': entity.score
                })
            
            # Visually similar images
            similar_images = []
            for image_info in web_detection.visually_similar_images:
                similar_images.append({
                    'url': image_info.url,
                    'score': getattr(image_info, 'score', 0)
                })
            
            return {
                'web_entities': web_entities,
                'similar_images': similar_images
            }
            
        except Exception as e:
            self.log_error(e, "_detect_web_entities")
            return {}
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of analysis results"""
        summary = {
            'total_objects': len(results.get('objects', [])),
            'total_labels': len(results.get('labels', [])),
            'has_text': bool(results.get('text', {}).get('full_text')),
            'total_faces': len(results.get('faces', [])),
            'top_labels': [],
            'top_objects': []
        }
        
        # Top labels by confidence
        labels = results.get('labels', [])
        if labels:
            sorted_labels = sorted(labels, key=lambda x: x['confidence'], reverse=True)
            summary['top_labels'] = [label['description'] for label in sorted_labels[:5]]
        
        # Top objects by confidence
        objects = results.get('objects', [])
        if objects:
            sorted_objects = sorted(objects, key=lambda x: x['confidence'], reverse=True)
            summary['top_objects'] = [obj['name'] for obj in sorted_objects[:5]]
        
        return summary
    
    def extract_features_for_similarity(self, analysis_results: Dict) -> Dict:
        """Extract features for similarity matching"""
        features = {
            'objects': [],
            'labels': [],
            'colors': [],
            'text_content': '',
            'has_faces': False
        }
        
        # Extract object names
        if 'objects' in analysis_results:
            features['objects'] = [obj['name'] for obj in analysis_results['objects']]
        
        # Extract label descriptions
        if 'labels' in analysis_results:
            features['labels'] = [label['description'] for label in analysis_results['labels']]
        
        # Extract dominant colors
        if 'properties' in analysis_results:
            colors = analysis_results['properties'].get('dominant_colors', [])
            features['colors'] = [color['color'] for color in colors[:5]]
        
        # Extract text content
        if 'text' in analysis_results:
            features['text_content'] = analysis_results['text'].get('full_text', '')
        
        # Check for faces
        if 'faces' in analysis_results:
            features['has_faces'] = len(analysis_results['faces']) > 0
        
        return features
    
    def health_check(self) -> bool:
        """Health check for vision service"""
        try:
            # Simple client check
            return self.client is not None
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("vision_service", VisionService, singleton=True)