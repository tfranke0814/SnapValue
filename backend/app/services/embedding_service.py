import json
import numpy as np
from typing import Dict, List, Optional, Any, Union
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic
from google.cloud.exceptions import GoogleCloudError
import vertexai
from vertexai.language_models import TextEmbeddingModel
from vertexai.vision_models import MultimodalEmbeddingModel

from app.core.config import settings
from app.services.base_service import BaseService
from app.utils.exceptions import ExternalServiceError, ConfigurationError, AIProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry

logger = get_logger(__name__)

class EmbeddingService(BaseService):
    """Vertex AI service for generating embeddings"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.text_model = None
        self.multimodal_model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Vertex AI client and models"""
        try:
            # Check if credentials are configured
            if not settings.VERTEX_AI_PROJECT:
                raise ConfigurationError("VERTEX_AI_PROJECT not configured")
            
            # Initialize Vertex AI
            vertexai.init(
                project=settings.VERTEX_AI_PROJECT,
                location=settings.VERTEX_AI_LOCATION
            )
            
            # Initialize models
            self.text_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
            self.multimodal_model = MultimodalEmbeddingModel.from_pretrained("multimodalembedding@001")
            
            log_service_call("EmbeddingService", "initialize_client", 
                           project=settings.VERTEX_AI_PROJECT,
                           location=settings.VERTEX_AI_LOCATION)
            
        except Exception as e:
            self.log_error(e, "initialize_client")
            raise ConfigurationError(f"Failed to initialize Vertex AI: {str(e)}")
    
    def validate_input(self, data) -> bool:
        """Validate input for embedding generation"""
        if not isinstance(data, dict):
            return False
        
        # Must have either text or image data
        return 'text' in data or 'image_content' in data or 'image_uri' in data
    
    def process(self, data: Dict) -> Dict:
        """Process embedding generation - main entry point"""
        if not self.validate_input(data):
            raise AIProcessingError("Invalid input data for embedding generation")
        
        results = {}
        
        # Generate text embeddings if text provided
        if 'text' in data:
            results['text_embeddings'] = self.generate_text_embeddings(data['text'])
        
        # Generate multimodal embeddings if image provided
        if 'image_content' in data or 'image_uri' in data:
            results['multimodal_embeddings'] = self.generate_multimodal_embeddings(
                image_content=data.get('image_content'),
                image_uri=data.get('image_uri'),
                text=data.get('text')
            )
        
        return results
    
    def generate_text_embeddings(self, text: Union[str, List[str]]) -> Dict:
        """
        Generate text embeddings using Vertex AI
        
        Args:
            text: Text or list of texts to embed
            
        Returns:
            Dictionary with embedding results
        """
        log_service_call("EmbeddingService", "generate_text_embeddings", 
                        text_count=len(text) if isinstance(text, list) else 1)
        
        try:
            # Ensure text is a list
            if isinstance(text, str):
                texts = [text]
            else:
                texts = text
            
            # Generate embeddings
            embeddings = self.text_model.get_embeddings(texts)
            
            # Extract embedding vectors
            embedding_vectors = []
            for embedding in embeddings:
                embedding_vectors.append({
                    'values': embedding.values,
                    'statistics': embedding.statistics.__dict__ if hasattr(embedding, 'statistics') else {}
                })
            
            result = {
                'embeddings': embedding_vectors,
                'model': 'textembedding-gecko@003',
                'dimension': len(embedding_vectors[0]['values']) if embedding_vectors else 0,
                'count': len(embedding_vectors)
            }
            
            log_service_result("EmbeddingService", "generate_text_embeddings", True, 
                             count=len(embedding_vectors),
                             dimension=result['dimension'])
            
            return result
            
        except GoogleCloudError as e:
            self.log_error(e, "generate_text_embeddings")
            raise ExternalServiceError("Vertex AI", f"Text embedding generation failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "generate_text_embeddings")
            raise AIProcessingError(f"Text embedding generation failed: {str(e)}")
    
    def generate_multimodal_embeddings(
        self,
        image_content: Optional[bytes] = None,
        image_uri: Optional[str] = None,
        text: Optional[str] = None
    ) -> Dict:
        """
        Generate multimodal embeddings using Vertex AI
        
        Args:
            image_content: Image content as bytes
            image_uri: URI of image (for GCS images)
            text: Optional text to include in embedding
            
        Returns:
            Dictionary with embedding results
        """
        log_service_call("EmbeddingService", "generate_multimodal_embeddings", 
                        has_image=bool(image_content or image_uri),
                        has_text=bool(text))
        
        try:
            from vertexai.vision_models import Image
            
            # Prepare image
            if image_content:
                image = Image(image_bytes=image_content)
            elif image_uri:
                image = Image(image_uri=image_uri)
            else:
                raise AIProcessingError("Either image_content or image_uri must be provided")
            
            # Generate embeddings
            if text:
                embeddings = self.multimodal_model.get_embeddings(
                    image=image,
                    contextual_text=text
                )
            else:
                embeddings = self.multimodal_model.get_embeddings(image=image)
            
            result = {
                'image_embedding': embeddings.image_embedding,
                'text_embedding': embeddings.text_embedding if hasattr(embeddings, 'text_embedding') else None,
                'model': 'multimodalembedding@001',
                'dimension': len(embeddings.image_embedding) if embeddings.image_embedding else 0
            }
            
            log_service_result("EmbeddingService", "generate_multimodal_embeddings", True, 
                             dimension=result['dimension'])
            
            return result
            
        except GoogleCloudError as e:
            self.log_error(e, "generate_multimodal_embeddings")
            raise ExternalServiceError("Vertex AI", f"Multimodal embedding generation failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "generate_multimodal_embeddings")
            raise AIProcessingError(f"Multimodal embedding generation failed: {str(e)}")
    
    def generate_embeddings_for_features(self, features: Dict) -> Dict:
        """
        Generate embeddings for extracted features
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Dictionary with feature embeddings
        """
        log_service_call("EmbeddingService", "generate_embeddings_for_features", 
                        feature_types=list(features.keys()))
        
        try:
            embeddings = {}
            
            # Generate embeddings for different feature types
            if 'objects' in features and features['objects']:
                object_text = ', '.join(features['objects'])
                embeddings['objects'] = self.generate_text_embeddings(object_text)
            
            if 'labels' in features and features['labels']:
                label_text = ', '.join(features['labels'])
                embeddings['labels'] = self.generate_text_embeddings(label_text)
            
            if 'text_content' in features and features['text_content']:
                embeddings['text_content'] = self.generate_text_embeddings(features['text_content'])
            
            # Generate combined feature embedding
            combined_features = []
            if 'objects' in features:
                combined_features.extend(features['objects'])
            if 'labels' in features:
                combined_features.extend(features['labels'])
            if 'text_content' in features and features['text_content']:
                combined_features.append(features['text_content'])
            
            if combined_features:
                combined_text = ', '.join(combined_features)
                embeddings['combined'] = self.generate_text_embeddings(combined_text)
            
            log_service_result("EmbeddingService", "generate_embeddings_for_features", True, 
                             embedding_types=list(embeddings.keys()))
            
            return embeddings
            
        except Exception as e:
            self.log_error(e, "generate_embeddings_for_features")
            raise AIProcessingError(f"Feature embedding generation failed: {str(e)}")
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.log_error(e, "calculate_similarity")
            return 0.0
    
    def find_similar_embeddings(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Dict],
        threshold: float = 0.5,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find similar embeddings to a query embedding
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings with metadata
            threshold: Minimum similarity threshold
            top_k: Maximum number of results to return
            
        Returns:
            List of similar embeddings with similarity scores
        """
        log_service_call("EmbeddingService", "find_similar_embeddings", 
                        candidates=len(candidate_embeddings),
                        threshold=threshold,
                        top_k=top_k)
        
        try:
            similarities = []
            
            for candidate in candidate_embeddings:
                if 'embedding' not in candidate:
                    continue
                
                similarity = self.calculate_similarity(query_embedding, candidate['embedding'])
                
                if similarity >= threshold:
                    similarities.append({
                        'similarity': similarity,
                        'data': candidate,
                        'id': candidate.get('id')
                    })
            
            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:top_k]
            
            log_service_result("EmbeddingService", "find_similar_embeddings", True, 
                             matches=len(results))
            
            return results
            
        except Exception as e:
            self.log_error(e, "find_similar_embeddings")
            return []
    
    def batch_generate_embeddings(self, items: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for a batch of items
        
        Args:
            items: List of items to generate embeddings for
            
        Returns:
            List of items with embeddings added
        """
        log_service_call("EmbeddingService", "batch_generate_embeddings", 
                        batch_size=len(items))
        
        results = []
        
        try:
            for item in items:
                try:
                    embeddings = self.process(item)
                    results.append({
                        **item,
                        'embeddings': embeddings
                    })
                except Exception as e:
                    self.log_error(e, f"batch_generate_embeddings_item_{item.get('id', 'unknown')}")
                    results.append({
                        **item,
                        'embeddings': None,
                        'error': str(e)
                    })
            
            log_service_result("EmbeddingService", "batch_generate_embeddings", True, 
                             processed=len(results))
            
            return results
            
        except Exception as e:
            self.log_error(e, "batch_generate_embeddings")
            raise AIProcessingError(f"Batch embedding generation failed: {str(e)}")
    
    def health_check(self) -> bool:
        """Health check for embedding service"""
        try:
            # Check if models are initialized
            return self.text_model is not None and self.multimodal_model is not None
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("embedding_service", EmbeddingService, singleton=True)