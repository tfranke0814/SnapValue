from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.base_service import BaseService
from app.services.vision_service import VisionService
from app.services.embedding_service import EmbeddingService
from app.utils.exceptions import AIProcessingError, ValidationError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry
import vertexai
from vertexai.agent_engines import AgentEngine
from app.core.config import settings

logger = get_logger(__name__)

class AIService(BaseService):
    """Main AI service that orchestrates vision and embedding services"""
    
    def __init__(self, db: Optional[Session] = None):
        super().__init__(db)
        self.vision_service = VisionService(db)
        self.embedding_service = EmbeddingService(db)
        
        if not all([settings.VERTEX_AI_PROJECT, settings.VERTEX_AI_LOCATION, settings.VERTEX_AI_REASONING_ENGINE_ID]):
            raise ValueError("Vertex AI settings are not configured in the environment.")
        
        vertexai.init(
            project=settings.VERTEX_AI_PROJECT,
            location=settings.VERTEX_AI_LOCATION,
        )
        
        self.agent_engine = AgentEngine.get(settings.VERTEX_AI_REASONING_ENGINE_ID)
    
    def _parse_agent_response(self, response: Any) -> Dict:
        """
        Parses the raw response from the Vertex AI agent into a structured dictionary.
        
        Args:
            response: The response object from agent_engine.query().
            
        Returns:
            A dictionary with structured appraisal data.
        """
        try:
            # Assuming response is an object with a 'text' attribute containing a JSON string
            # or a simple string. This part is highly dependent on the actual agent output format.
            if hasattr(response, 'text'):
                content = response.text
            else:
                content = str(response)

            # TODO: Implement robust parsing based on the agent's actual output format.
            # This is a placeholder implementation.
            # For now, we'll just return the raw text.
            # A real implementation would parse JSON, extract entities, etc.
            return {
                "raw_response": content,
                "estimated_value": "parsing_pending",
                "details": "parsing_pending"
            }
        except Exception as e:
            logger.error(f"Failed to parse agent response: {response}. Error: {e}")
            return {
                "raw_response": str(response),
                "error": "Failed to parse agent response."
            }

    def get_appraisal_from_agent(
        self,
        image_uri: str,
        user_query: str = "Analyze the item in the image and provide an estimated appraisal value and key details."
    ) -> Dict:
        """
        Analyzes an image using the Vertex AI Agent Engine.

        Args:
            image_uri: The GCS URI of the image to analyze.
            user_query: The user's query to the agent.

        Returns:
            A dictionary containing the agent's parsed response.
        """
        if not image_uri:
            raise ValidationError("GCS image URI is required for agent analysis.")

        log_service_call("AIService", "get_appraisal_from_agent", image_uri=image_uri, query=user_query)

        try:
            # The prompt needs to clearly instruct the agent what to do and where to find the image.
            # This assumes the agent has been configured to understand such prompts.
            prompt = f"{user_query} The image for appraisal is located at the following GCS URI: {image_uri}"

            response = self.agent_engine.query(prompt)
            
            parsed_response = self._parse_agent_response(response)
            
            log_service_result("AIService", "get_appraisal_from_agent", parsed_response)
            return parsed_response

        except Exception as e:
            logger.error(f"Error calling Vertex AI Agent Engine: {e}")
            raise AIProcessingError("Failed to get appraisal from AI agent.") from e

    def validate_input(self, data) -> bool:
        """Validate input for AI processing"""
        if not isinstance(data, dict):
            return False
        
        # Must have either file_content or image_uri
        return 'file_content' in data or 'image_uri' in data
    
    def process(self, data: Dict) -> Dict:
        """Process AI analysis - main entry point"""
        if not self.validate_input(data):
            raise AIProcessingError("Invalid input data for AI processing")
        
        # The new flow requires an image_uri for the agent
        image_uri = data.get('image_uri')
        if not image_uri:
            # Note: The current implementation does not handle direct file_content uploads
            # for the agent. The appraisal_service is responsible for uploading to GCS first.
            raise AIProcessingError("image_uri is required for AI agent processing.")

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
        The main 'process' method no longer calls this for agent-based appraisal.
        
        Complete image analysis pipeline
        
        Args:
            file_content: Image content as bytes
            image_uri: URI of image (for GCS images)
            analysis_options: Options for analysis
            
        Returns:
            Dictionary with complete analysis results
        """
        logger.warning("The 'analyze_image_complete' method is deprecated for agent-based appraisals.")
        if analysis_options is None:
            analysis_options = {}
        
        log_service_call("AIService", "analyze_image_complete", 
                        has_content=file_content is not None,
                        has_uri=image_uri is not None)
        
        try:
            # Step 1: Vision analysis
            vision_features = analysis_options.get('vision_features', 
                                                 ['objects', 'labels', 'text', 'faces', 'properties'])
            
            vision_results = self.vision_service.analyze_image(
                file_content=file_content,
                image_uri=image_uri,
                features=vision_features
            )
            
            # Step 2: Extract features for embedding
            extracted_features = self.vision_service.extract_features_for_similarity(vision_results)
            
            # Step 3: Generate embeddings
            embeddings = {}
            
            # Generate text embeddings from features
            if analysis_options.get('generate_text_embeddings', True):
                embeddings.update(self.embedding_service.generate_embeddings_for_features(extracted_features))
            
            # Generate multimodal embeddings
            if analysis_options.get('generate_multimodal_embeddings', True):
                multimodal_embedding = self.embedding_service.generate_multimodal_embeddings(
                    image_content=file_content,
                    image_uri=image_uri,
                    text=extracted_features.get('text_content')
                )
                embeddings['multimodal'] = multimodal_embedding
            
            # Step 4: Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(vision_results, embeddings)
            
            # Step 5: Prepare comprehensive results
            results = {
                'vision_analysis': vision_results,
                'extracted_features': extracted_features,
                'embeddings': embeddings,
                'confidence_scores': confidence_scores,
                'processing_metadata': {
                    'processed_at': datetime.utcnow().isoformat(),
                    'vision_features_analyzed': len(vision_results),
                    'embedding_types_generated': len(embeddings),
                    'total_objects_detected': len(vision_results.get('objects', [])),
                    'total_labels_detected': len(vision_results.get('labels', [])),
                    'text_detected': bool(vision_results.get('text', {}).get('full_text')),
                    'faces_detected': len(vision_results.get('faces', []))
                }
            }
            
            log_service_result("AIService", "analyze_image_complete", True, 
                             vision_features=len(vision_results),
                             embedding_types=len(embeddings))
            
            return results
            
        except Exception as e:
            self.log_error(e, "analyze_image_complete")
            raise AIProcessingError(f"Complete image analysis failed: {str(e)}")
    
    def _calculate_confidence_scores(self, vision_results: Dict, embeddings: Dict) -> Dict:
        """Calculate confidence scores for analysis results"""
        try:
            confidence_scores = {
                'overall_confidence': 0.0,
                'vision_confidence': 0.0,
                'embedding_confidence': 0.0,
                'feature_confidence': {},
                'quality_indicators': {}
            }
            
            # Vision confidence
            vision_confidences = []
            
            # Object detection confidence
            if 'objects' in vision_results:
                object_confidences = [obj['confidence'] for obj in vision_results['objects']]
                if object_confidences:
                    confidence_scores['feature_confidence']['objects'] = sum(object_confidences) / len(object_confidences)
                    vision_confidences.append(confidence_scores['feature_confidence']['objects'])
            
            # Label detection confidence
            if 'labels' in vision_results:
                label_confidences = [label['confidence'] for label in vision_results['labels']]
                if label_confidences:
                    confidence_scores['feature_confidence']['labels'] = sum(label_confidences) / len(label_confidences)
                    vision_confidences.append(confidence_scores['feature_confidence']['labels'])
            
            # Face detection confidence
            if 'faces' in vision_results:
                face_confidences = [face['confidence'] for face in vision_results['faces']]
                if face_confidences:
                    confidence_scores['feature_confidence']['faces'] = sum(face_confidences) / len(face_confidences)
                    vision_confidences.append(confidence_scores['feature_confidence']['faces'])
            
            # Overall vision confidence
            if vision_confidences:
                confidence_scores['vision_confidence'] = sum(vision_confidences) / len(vision_confidences)
            
            # Embedding confidence (based on availability and quality)
            embedding_score = 0.0
            if 'multimodal' in embeddings:
                embedding_score += 0.4
            if 'combined' in embeddings:
                embedding_score += 0.3
            if 'objects' in embeddings:
                embedding_score += 0.2
            if 'labels' in embeddings:
                embedding_score += 0.1
            
            confidence_scores['embedding_confidence'] = embedding_score
            
            # Quality indicators
            confidence_scores['quality_indicators'] = {
                'has_clear_objects': len(vision_results.get('objects', [])) > 0,
                'has_descriptive_labels': len(vision_results.get('labels', [])) > 2,
                'has_text_content': bool(vision_results.get('text', {}).get('full_text')),
                'has_faces': len(vision_results.get('faces', [])) > 0,
                'has_multimodal_embedding': 'multimodal' in embeddings,
                'object_detection_quality': 'high' if confidence_scores['feature_confidence'].get('objects', 0) > 0.7 else 'medium' if confidence_scores['feature_confidence'].get('objects', 0) > 0.5 else 'low'
            }
            
            # Overall confidence
            confidence_scores['overall_confidence'] = (
                confidence_scores['vision_confidence'] * 0.6 +
                confidence_scores['embedding_confidence'] * 0.4
            )
            
            return confidence_scores
            
        except Exception as e:
            self.log_error(e, "_calculate_confidence_scores")
            return {'overall_confidence': 0.0, 'error': str(e)}
    
    def find_similar_items(
        self,
        query_embeddings: Dict,
        candidate_items: List[Dict],
        similarity_threshold: float = 0.7,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find similar items based on embeddings
        
        Args:
            query_embeddings: Query embeddings
            candidate_items: List of candidate items with embeddings
            similarity_threshold: Minimum similarity threshold
            top_k: Maximum number of results to return
            
        Returns:
            List of similar items with similarity scores
        """
        log_service_call("AIService", "find_similar_items", 
                        candidates=len(candidate_items),
                        threshold=similarity_threshold,
                        top_k=top_k)
        
        try:
            # Use multimodal embedding if available, otherwise use combined
            query_embedding = None
            if 'multimodal' in query_embeddings:
                query_embedding = query_embeddings['multimodal'].get('image_embedding')
            elif 'combined' in query_embeddings:
                query_embedding = query_embeddings['combined']['embeddings'][0]['values']
            
            if not query_embedding:
                raise AIProcessingError("No suitable query embedding found")
            
            # Prepare candidate embeddings
            candidate_embeddings = []
            for item in candidate_items:
                if 'embeddings' in item:
                    embedding = None
                    if 'multimodal' in item['embeddings']:
                        embedding = item['embeddings']['multimodal'].get('image_embedding')
                    elif 'combined' in item['embeddings']:
                        embedding = item['embeddings']['combined']['embeddings'][0]['values']
                    
                    if embedding:
                        candidate_embeddings.append({
                            'id': item.get('id'),
                            'embedding': embedding,
                            'data': item
                        })
            
            # Find similar embeddings
            similar_items = self.embedding_service.find_similar_embeddings(
                query_embedding,
                candidate_embeddings,
                similarity_threshold,
                top_k
            )
            
            log_service_result("AIService", "find_similar_items", True, 
                             matches=len(similar_items))
            
            return similar_items
            
        except Exception as e:
            self.log_error(e, "find_similar_items")
            raise AIProcessingError(f"Similar item search failed: {str(e)}")
    
    def batch_analyze_images(self, image_batch: List[Dict]) -> List[Dict]:
        """
        Analyze a batch of images
        
        Args:
            image_batch: List of image data dictionaries
            
        Returns:
            List of analysis results
        """
        log_service_call("AIService", "batch_analyze_images", 
                        batch_size=len(image_batch))
        
        results = []
        
        try:
            for i, image_data in enumerate(image_batch):
                try:
                    result = self.analyze_image_complete(
                        file_content=image_data.get('file_content'),
                        image_uri=image_data.get('image_uri'),
                        analysis_options=image_data.get('analysis_options', {})
                    )
                    
                    results.append({
                        'index': i,
                        'id': image_data.get('id'),
                        'success': True,
                        'result': result
                    })
                    
                except Exception as e:
                    self.log_error(e, f"batch_analyze_images_item_{i}")
                    results.append({
                        'index': i,
                        'id': image_data.get('id'),
                        'success': False,
                        'error': str(e)
                    })
            
            log_service_result("AIService", "batch_analyze_images", True, 
                             processed=len(results),
                             successful=len([r for r in results if r['success']]))
            
            return results
            
        except Exception as e:
            self.log_error(e, "batch_analyze_images")
            raise AIProcessingError(f"Batch image analysis failed: {str(e)}")
    
    def validate_analysis_results(self, results: Dict) -> Dict:
        """
        Validate analysis results and provide quality assessment
        
        Args:
            results: Analysis results to validate
            
        Returns:
            Validation results
        """
        log_service_call("AIService", "validate_analysis_results")
        
        try:
            validation = {
                'is_valid': True,
                'issues': [],
                'quality_score': 0.0,
                'recommendations': []
            }
            
            # Check vision analysis
            if 'vision_analysis' not in results:
                validation['is_valid'] = False
                validation['issues'].append("Missing vision analysis")
            else:
                vision_analysis = results['vision_analysis']
                
                # Check for detected objects
                if not vision_analysis.get('objects'):
                    validation['issues'].append("No objects detected")
                    validation['recommendations'].append("Consider retaking photo with clearer objects")
                
                # Check for labels
                if not vision_analysis.get('labels'):
                    validation['issues'].append("No labels detected")
                    validation['recommendations'].append("Image may be too dark or unclear")
                
                # Check confidence scores
                if 'confidence_scores' in results:
                    overall_confidence = results['confidence_scores'].get('overall_confidence', 0)
                    if overall_confidence < 0.5:
                        validation['issues'].append(f"Low confidence score: {overall_confidence:.2f}")
                        validation['recommendations'].append("Consider retaking photo with better lighting")
                    validation['quality_score'] = overall_confidence
            
            # Check embeddings
            if 'embeddings' not in results:
                validation['is_valid'] = False
                validation['issues'].append("Missing embeddings")
            
            log_service_result("AIService", "validate_analysis_results", True, 
                             is_valid=validation['is_valid'],
                             quality_score=validation['quality_score'])
            
            return validation
            
        except Exception as e:
            self.log_error(e, "validate_analysis_results")
            return {
                'is_valid': False,
                'issues': [f"Validation failed: {str(e)}"],
                'quality_score': 0.0,
                'recommendations': []
            }
    
    def health_check(self) -> bool:
        """Health check for AI service"""
        try:
            # Check both underlying services
            vision_health = self.vision_service.health_check()
            embedding_health = self.embedding_service.health_check()
            
            return vision_health and embedding_health
        except Exception as e:
            self.log_error(e, "health_check")
            return False

    def get_appraisal(self, image_gcs_path: str) -> dict:
        """
        Gets an appraisal for an image from the Vertex AI Agent.

        Args:
            image_gcs_path: The GCS path to the image (e.g., gs://bucket-name/folder/image.jpg)

        Returns:
            A dictionary containing the appraisal result.
        """
        # NOTE: The current agent design does not support passing the image path.
        # This prompt will need to be updated once the agent is redesigned
        # to accept the image_gcs_path as a parameter for its tools.
        prompt = f"Give an estimate price with your reasoning for the item in the image."

        response_stream = self.agent_engine.stream_query(
            message=prompt,
        )

        full_response = ""
        for event in response_stream:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        full_response += part.text
        
        # This is a placeholder for parsing the final response.
        # The actual parsing logic will depend on the agent's final output format.
        return {"appraisal_text": full_response}

def get_ai_service():
    return AIService()

# Register service
registry.register("ai_service", AIService, singleton=False)