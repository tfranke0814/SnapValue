from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime
import json

from app.utils.logging import get_logger
from app.utils.exceptions import AIProcessingError

logger = get_logger(__name__)

class AIResultProcessor:
    """Utility class for processing AI analysis results"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'objects': 0.5,
            'labels': 0.6,
            'faces': 0.7,
            'text': 0.8
        }
    
    def filter_results_by_confidence(self, results: Dict, thresholds: Optional[Dict] = None) -> Dict:
        """Filter AI results by confidence thresholds"""
        if thresholds is None:
            thresholds = self.confidence_thresholds
        
        filtered_results = {}
        
        try:
            # Filter objects
            if 'objects' in results:
                threshold = thresholds.get('objects', 0.5)
                filtered_results['objects'] = [
                    obj for obj in results['objects']
                    if obj.get('confidence', 0) >= threshold
                ]
            
            # Filter labels
            if 'labels' in results:
                threshold = thresholds.get('labels', 0.6)
                filtered_results['labels'] = [
                    label for label in results['labels']
                    if label.get('confidence', 0) >= threshold
                ]
            
            # Filter faces
            if 'faces' in results:
                threshold = thresholds.get('faces', 0.7)
                filtered_results['faces'] = [
                    face for face in results['faces']
                    if face.get('confidence', 0) >= threshold
                ]
            
            # Copy other results as-is
            for key, value in results.items():
                if key not in ['objects', 'labels', 'faces']:
                    filtered_results[key] = value
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to filter results by confidence: {e}")
            return results
    
    def extract_categories(self, vision_results: Dict) -> List[str]:
        """Extract item categories from vision analysis"""
        categories = set()
        
        try:
            # Extract from objects
            if 'objects' in vision_results:
                for obj in vision_results['objects']:
                    categories.add(obj['name'].lower())
            
            # Extract from labels
            if 'labels' in vision_results:
                for label in vision_results['labels']:
                    categories.add(label['description'].lower())
            
            return list(categories)
            
        except Exception as e:
            logger.error(f"Failed to extract categories: {e}")
            return []
    
    def generate_description(self, vision_results: Dict) -> str:
        """Generate human-readable description from vision results"""
        try:
            description_parts = []
            
            # Add object information
            if 'objects' in vision_results and vision_results['objects']:
                objects = [obj['name'] for obj in vision_results['objects'][:3]]
                description_parts.append(f"Contains {', '.join(objects)}")
            
            # Add label information
            if 'labels' in vision_results and vision_results['labels']:
                labels = [label['description'] for label in vision_results['labels'][:3]]
                description_parts.append(f"Features {', '.join(labels)}")
            
            # Add text information
            if 'text' in vision_results and vision_results['text'].get('full_text'):
                text_length = len(vision_results['text']['full_text'])
                if text_length > 0:
                    description_parts.append(f"Contains text ({text_length} characters)")
            
            # Add face information
            if 'faces' in vision_results and vision_results['faces']:
                face_count = len(vision_results['faces'])
                description_parts.append(f"Contains {face_count} face(s)")
            
            return '. '.join(description_parts) if description_parts else "Image analyzed"
            
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return "Image analyzed"
    
    def calculate_item_value_indicators(self, vision_results: Dict) -> Dict:
        """Calculate indicators that might affect item value"""
        indicators = {
            'condition_indicators': {},
            'authenticity_indicators': {},
            'rarity_indicators': {},
            'quality_score': 0.0
        }
        
        try:
            # Condition indicators
            text_content = vision_results.get('text', {}).get('full_text', '').lower()
            
            # Look for condition keywords
            condition_keywords = {
                'excellent': ['mint', 'perfect', 'excellent', 'pristine', 'new'],
                'good': ['good', 'fine', 'nice', 'clean'],
                'fair': ['used', 'worn', 'fair', 'average'],
                'poor': ['damaged', 'broken', 'poor', 'cracked', 'torn']
            }
            
            for condition, keywords in condition_keywords.items():
                if any(keyword in text_content for keyword in keywords):
                    indicators['condition_indicators'][condition] = True
            
            # Authenticity indicators
            auth_keywords = ['authentic', 'genuine', 'original', 'certified', 'serial']
            if any(keyword in text_content for keyword in auth_keywords):
                indicators['authenticity_indicators']['has_auth_markers'] = True
            
            # Brand detection from labels
            if 'labels' in vision_results:
                brand_labels = [label['description'] for label in vision_results['labels'] 
                              if 'brand' in label['description'].lower() or 'logo' in label['description'].lower()]
                if brand_labels:
                    indicators['authenticity_indicators']['brand_detected'] = True
            
            # Rarity indicators
            objects = vision_results.get('objects', [])
            if objects:
                # Unique or rare object types
                rare_objects = ['antique', 'vintage', 'collectible', 'rare', 'limited']
                for obj in objects:
                    if any(rare_word in obj['name'].lower() for rare_word in rare_objects):
                        indicators['rarity_indicators']['rare_object_detected'] = True
            
            # Calculate quality score
            quality_factors = []
            
            # Image clarity (based on confidence scores)
            if 'objects' in vision_results:
                avg_confidence = np.mean([obj['confidence'] for obj in vision_results['objects']])
                quality_factors.append(avg_confidence)
            
            if 'labels' in vision_results:
                avg_confidence = np.mean([label['confidence'] for label in vision_results['labels']])
                quality_factors.append(avg_confidence)
            
            indicators['quality_score'] = np.mean(quality_factors) if quality_factors else 0.0
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate value indicators: {e}")
            return indicators
    
    def merge_analysis_results(self, results_list: List[Dict]) -> Dict:
        """Merge multiple analysis results into a single result"""
        try:
            merged = {
                'objects': [],
                'labels': [],
                'faces': [],
                'text': {'full_text': '', 'text_blocks': []},
                'properties': {},
                'web': {},
                'summary': {}
            }
            
            # Merge objects
            all_objects = []
            for result in results_list:
                if 'objects' in result:
                    all_objects.extend(result['objects'])
            
            # Remove duplicates and sort by confidence
            seen_objects = set()
            for obj in sorted(all_objects, key=lambda x: x['confidence'], reverse=True):
                if obj['name'] not in seen_objects:
                    merged['objects'].append(obj)
                    seen_objects.add(obj['name'])
            
            # Merge labels
            all_labels = []
            for result in results_list:
                if 'labels' in result:
                    all_labels.extend(result['labels'])
            
            # Remove duplicates and sort by confidence
            seen_labels = set()
            for label in sorted(all_labels, key=lambda x: x['confidence'], reverse=True):
                if label['description'] not in seen_labels:
                    merged['labels'].append(label)
                    seen_labels.add(label['description'])
            
            # Merge text
            all_text = []
            for result in results_list:
                if 'text' in result and result['text'].get('full_text'):
                    all_text.append(result['text']['full_text'])
            
            merged['text']['full_text'] = ' '.join(all_text)
            
            # Merge other fields (take from first result)
            for result in results_list:
                for key in ['faces', 'properties', 'web']:
                    if key in result and result[key] and not merged[key]:
                        merged[key] = result[key]
            
            # Generate new summary
            merged['summary'] = {
                'total_objects': len(merged['objects']),
                'total_labels': len(merged['labels']),
                'has_text': bool(merged['text']['full_text']),
                'total_faces': len(merged['faces']),
                'top_labels': [label['description'] for label in merged['labels'][:5]],
                'top_objects': [obj['name'] for obj in merged['objects'][:5]]
            }
            
            return merged
            
        except Exception as e:
            logger.error(f"Failed to merge analysis results: {e}")
            return results_list[0] if results_list else {}
    
    def standardize_embeddings(self, embeddings: Dict) -> Dict:
        """Standardize embeddings for consistent storage and comparison"""
        try:
            standardized = {}
            
            for embedding_type, embedding_data in embeddings.items():
                if embedding_type == 'multimodal':
                    # Handle multimodal embeddings
                    if 'image_embedding' in embedding_data:
                        standardized[f"{embedding_type}_image"] = {
                            'vector': embedding_data['image_embedding'],
                            'dimension': len(embedding_data['image_embedding']),
                            'model': embedding_data.get('model', 'unknown')
                        }
                    
                    if 'text_embedding' in embedding_data:
                        standardized[f"{embedding_type}_text"] = {
                            'vector': embedding_data['text_embedding'],
                            'dimension': len(embedding_data['text_embedding']),
                            'model': embedding_data.get('model', 'unknown')
                        }
                
                elif 'embeddings' in embedding_data:
                    # Handle text embeddings
                    for i, emb in enumerate(embedding_data['embeddings']):
                        if 'values' in emb:
                            standardized[f"{embedding_type}_{i}"] = {
                                'vector': emb['values'],
                                'dimension': len(emb['values']),
                                'model': embedding_data.get('model', 'unknown')
                            }
            
            return standardized
            
        except Exception as e:
            logger.error(f"Failed to standardize embeddings: {e}")
            return embeddings
    
    def extract_searchable_features(self, analysis_results: Dict) -> Dict:
        """Extract features suitable for search and matching"""
        features = {
            'categories': [],
            'keywords': [],
            'colors': [],
            'text_content': '',
            'has_faces': False,
            'object_count': 0,
            'confidence_score': 0.0
        }
        
        try:
            vision_results = analysis_results.get('vision_analysis', {})
            
            # Extract categories
            features['categories'] = self.extract_categories(vision_results)
            
            # Extract keywords from labels and objects
            keywords = set()
            
            if 'objects' in vision_results:
                for obj in vision_results['objects']:
                    keywords.add(obj['name'].lower())
                features['object_count'] = len(vision_results['objects'])
            
            if 'labels' in vision_results:
                for label in vision_results['labels']:
                    keywords.add(label['description'].lower())
            
            features['keywords'] = list(keywords)
            
            # Extract colors
            if 'properties' in vision_results:
                colors = vision_results['properties'].get('dominant_colors', [])
                features['colors'] = [color['color'] for color in colors[:3]]
            
            # Extract text content
            if 'text' in vision_results:
                features['text_content'] = vision_results['text'].get('full_text', '')
            
            # Check for faces
            if 'faces' in vision_results:
                features['has_faces'] = len(vision_results['faces']) > 0
            
            # Overall confidence score
            if 'confidence_scores' in analysis_results:
                features['confidence_score'] = analysis_results['confidence_scores'].get('overall_confidence', 0.0)
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract searchable features: {e}")
            return features

# Utility functions
def filter_ai_results(results: Dict, confidence_thresholds: Optional[Dict] = None) -> Dict:
    """Filter AI results by confidence thresholds"""
    processor = AIResultProcessor()
    return processor.filter_results_by_confidence(results, confidence_thresholds)

def extract_item_categories(vision_results: Dict) -> List[str]:
    """Extract item categories from vision analysis"""
    processor = AIResultProcessor()
    return processor.extract_categories(vision_results)

def generate_item_description(vision_results: Dict) -> str:
    """Generate human-readable description from vision results"""
    processor = AIResultProcessor()
    return processor.generate_description(vision_results)

def calculate_value_indicators(vision_results: Dict) -> Dict:
    """Calculate indicators that might affect item value"""
    processor = AIResultProcessor()
    return processor.calculate_item_value_indicators(vision_results)

def standardize_embedding_data(embeddings: Dict) -> Dict:
    """Standardize embeddings for consistent storage"""
    processor = AIResultProcessor()
    return processor.standardize_embeddings(embeddings)

def extract_search_features(analysis_results: Dict) -> Dict:
    """Extract features suitable for search and matching"""
    processor = AIResultProcessor()
    return processor.extract_searchable_features(analysis_results)