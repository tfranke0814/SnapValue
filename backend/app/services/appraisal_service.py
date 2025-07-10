from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
from fastapi import UploadFile
import uuid
import asyncio

from app.services.base_service import BaseService
from app.services.image_service import ImageService
from app.services.storage_factory import get_storage_service
from app.core.config import settings
from app.models.appraisal import Appraisal, AppraisalStatus as ModelAppraisalStatus
from app.models.user import User
from app.utils.async_tasks import (
    submit_appraisal_task, TaskPriority, ProgressTracker
)
from app.utils.status_tracking import (
    AppraisalStatus, ProcessingStep, create_appraisal_status, 
    get_appraisal_status, StepTracker
)
from app.utils.result_caching import cache_appraisal_result, get_cached_appraisal
from app.utils.exceptions import ValidationError, DatabaseError, AIProcessingError, FileProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result, set_correlation_id
from app.core.registry import registry

logger = get_logger(__name__)

class AppraisalService(BaseService):
    """Main service for orchestrating the complete appraisal process"""
    
    def __init__(self, db: Optional[Session] = None):
        super().__init__(db)
        self.image_service = ImageService(db)
        self.storage_service = get_storage_service(db)
        
        # Use mock services in development to avoid Google Cloud dependencies
        if settings.is_development:
            from app.mocks.mock_ai_service import MockAIService
            from app.mocks.mock_market_service import MockMarketService
            from app.mocks.mock_price_service import MockPriceService
            
            self.ai_service = MockAIService(db)
            self.market_service = MockMarketService(db)
            self.price_service = MockPriceService(db)
            logger.info("Using mock services for development")
        else:
            from app.services.ai_service import AIService
            from app.services.market_service import MarketService
            from app.services.price_service import PriceService
            
            self.ai_service = AIService(db)
            self.market_service = MarketService(db)
            self.price_service = PriceService(db)
            logger.info("Using production services")
        
        # Processing configuration
        self.max_concurrent_appraisals = 5
        self.default_timeout = 300  # 5 minutes
        self.enable_caching = True
    
    def validate_input(self, data) -> bool:
        """Validate input for appraisal processing"""
        if not isinstance(data, dict):
            return False
        
        # Must have either file_content or image_url
        return 'file_content' in data or 'image_url' in data
    
    def process(self, data: Dict) -> Dict:
        """Process appraisal - main entry point"""
        if not self.validate_input(data):
            raise ValidationError("Invalid input data for appraisal processing")
        
        return self.submit_appraisal(
            data.get('file_content'),
            data.get('filename'),
            data.get('user_id'),
            data.get('image_url'),
            data.get('options', {})
        )
    
    async def submit_appraisal_from_upload(
        self,
        image_file: Optional[UploadFile] = None,
        user_id: Optional[int] = None,
        image_url: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Submit an appraisal from FastAPI UploadFile
        
        Args:
            image_file: FastAPI UploadFile object
            user_id: User ID submitting the appraisal
            image_url: Alternative image URL
            options: Processing options
            
        Returns:
            Dictionary with appraisal submission details
        """
        if options is None:
            options = {}
        
        log_service_call("AppraisalService", "submit_appraisal_from_upload", 
                        has_file=bool(image_file), has_url=bool(image_url), user_id=user_id)
        
        try:
            file_content = None
            filename = None
            
            # Handle file upload if provided
            if image_file:
                file_content = await image_file.read()
                filename = image_file.filename
                # Reset file position for potential future reads
                await image_file.seek(0)
            
            # Call main submission method
            return self.submit_appraisal(
                file_content=file_content,
                filename=filename,
                user_id=user_id,
                image_url=image_url,
                options=options
            )
            
        except Exception as e:
            self.log_error(e, "submit_appraisal_from_upload")
            raise
    
    def submit_appraisal(
        self,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        user_id: Optional[int] = None,
        image_url: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Submit an appraisal for processing
        
        Args:
            file_content: Image file content
            filename: Original filename
            user_id: User ID submitting the appraisal
            image_url: Alternative image URL
            options: Processing options
            
        Returns:
            Dictionary with appraisal submission details
        """
        if options is None:
            options = {}
        
        log_service_call("AppraisalService", "submit_appraisal", 
                        has_file=bool(file_content), has_url=bool(image_url), user_id=user_id)
        
        try:
            # Generate appraisal ID and correlation ID
            appraisal_id = str(uuid.uuid4())
            correlation_id = str(uuid.uuid4())
            
            # Set correlation ID for logging
            set_correlation_id(correlation_id)
            
            # Create status tracker
            status_info = create_appraisal_status(appraisal_id, str(user_id) if user_id else None, correlation_id)
            
            # Store file if provided
            image_path = None
            storage_result = None
            if file_content and filename:
                try:
                    storage_result = self.storage_service.upload_file(
                        file_content=file_content,
                        filename=filename,
                        metadata={
                            'appraisal_id': appraisal_id,
                            'correlation_id': correlation_id
                        },
                        folder='images',
                        user_id=user_id
                    )
                    image_path = storage_result.get('relative_path') or storage_result.get('blob_name')
                    logger.info(f"File stored successfully for appraisal {appraisal_id}: {image_path}")
                except Exception as e:
                    logger.error(f"Failed to store file for appraisal {appraisal_id}: {e}")
                    # Continue processing with image_url if available
                    if not image_url:
                        raise FileProcessingError(f"Failed to store image file: {str(e)}")
            
            # Create database record
            db_appraisal = self._create_appraisal_record(appraisal_id, user_id, filename, options, image_path, image_url)
            
            # For development: process synchronously to avoid async task manager issues
            task_id = str(uuid.uuid4())
            
            if settings.is_development:
                # Process immediately in development
                try:
                    final_result = self._process_appraisal_sync(
                        appraisal_id, file_content, filename, image_url, options
                    )
                    # Update database with results immediately
                    self._finalize_appraisal_sync(appraisal_id, final_result)
                except Exception as e:
                    logger.error(f"Development appraisal processing failed: {e}")
                    self._handle_processing_error_sync(appraisal_id, e)
            else:
                # Production: use async task processing
                task_id = asyncio.run(submit_appraisal_task(
                    "complete_appraisal",
                    self._process_appraisal_async,
                    args=(appraisal_id, file_content, filename, image_url, options),
                    priority=TaskPriority.NORMAL,
                    timeout=self.default_timeout,
                    correlation_id=correlation_id
                ))
            
            result = {
                'appraisal_id': appraisal_id,
                'task_id': task_id,
                'status': AppraisalStatus.SUBMITTED,
                'submitted_at': datetime.utcnow().isoformat(),
                'estimated_completion_minutes': 2,
                'correlation_id': correlation_id
            }
            
            log_service_result("AppraisalService", "submit_appraisal", True, 
                             appraisal_id=appraisal_id, task_id=task_id)
            
            return result
            
        except Exception as e:
            self.log_error(e, "submit_appraisal")
            raise
    
    def _process_appraisal_sync(
        self,
        appraisal_id: str,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        image_url: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Synchronous appraisal processing pipeline for development
        """
        try:
            logger.info(f"Starting synchronous appraisal processing: {appraisal_id}")
            
            # Step 1: AI Analysis (using mock service in development)
            ai_analysis = self.ai_service.analyze_image_complete(
                file_content=file_content,
                image_uri=image_url if not file_content else None,
                analysis_options=options.get('ai_options', {})
            )
            
            # Step 2: Market Analysis
            market_analysis = self.market_service.analyze_item_market_value(
                ai_analysis['embeddings'],
                ai_analysis['extracted_features'],
                options.get('category'),
                options.get('market_options', {})
            )
            
            # Step 3: Compile final results
            final_result = {
                'appraisal_id': appraisal_id,
                'estimated_value': market_analysis['estimated_value'],
                'currency': market_analysis.get('currency', 'USD'),
                'price_range': market_analysis['price_range'],
                'confidence_score': market_analysis['confidence_score'],
                'ai_analysis': ai_analysis,
                'market_analysis': market_analysis,
                'image_info': {
                    'image_path': image_url,
                    'image_url': image_url
                },
                'processing_metadata': {
                    'processed_at': datetime.utcnow().isoformat(),
                    'processing_version': '1.0-dev',
                    'options_used': options
                }
            }
            
            logger.info(f"Synchronous appraisal processing completed: {appraisal_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"Synchronous appraisal processing failed for {appraisal_id}: {e}")
            raise
    
    def _finalize_appraisal_sync(self, appraisal_id: str, result: Dict):
        """Finalize appraisal with results - synchronous version"""
        try:
            # Update database
            if self.db:
                updates = {
                    'status': "completed",
                    'market_price': result.get('estimated_value'),
                    'price_range_min': result.get('price_range', {}).get('min'),
                    'price_range_max': result.get('price_range', {}).get('max'),
                    'confidence_score': result.get('confidence_score'),
                    'similar_items': result.get('market_analysis', {}).get('comparable_items'),
                    'completed_at': datetime.utcnow()
                }
                self._update_appraisal_record(appraisal_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to finalize appraisal {appraisal_id}: {e}")
    
    def _handle_processing_error_sync(self, appraisal_id: str, error: Exception):
        """Handle processing error - synchronous version"""
        try:
            error_message = str(error)
            
            # Update database
            if self.db:
                updates = {
                    'status': "failed",
                    'error_message': error_message,
                    'updated_at': datetime.utcnow()
                }
                self._update_appraisal_record(appraisal_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to handle processing error for {appraisal_id}: {e}")
    
    async def _process_appraisal_async(
        self,
        appraisal_id: str,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        image_url: Optional[str] = None,
        options: Optional[Dict] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> Dict:
        """
        Async appraisal processing pipeline
        
        Args:
            appraisal_id: Appraisal ID
            file_content: Image file content
            filename: Original filename
            image_url: Alternative image URL
            options: Processing options
            progress_tracker: Progress tracker
            
        Returns:
            Complete appraisal results
        """
        try:
            logger.info(f"Starting appraisal processing: {appraisal_id}")
            
            # Initialize progress tracker
            if progress_tracker:
                await progress_tracker.update(0, "Starting appraisal processing")

            # Step 1: Image validation and upload to GCS
            image_uri = None
            with StepTracker(appraisal_id, ProcessingStep.IMAGE_VALIDATION):
                if progress_tracker:
                    await progress_tracker.update(1, "Uploading image to secure storage")
                
                if file_content and filename:
                    # This assumes storage_service is GcsStorageService in production
                    storage_result = self.storage_service.upload_file(
                        file_content=file_content,
                        filename=filename,
                        folder='images'
                    )
                    blob_name = storage_result.get('blob_name')
                    if blob_name:
                        image_uri = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"
                        public_url = storage_result.get('public_url')
                        self._update_appraisal_record(appraisal_id, {'image_path': blob_name, 'image_url': public_url})
                elif image_url:
                    # If a public URL is provided, we might need a step to download and upload to GCS
                    # For now, assume if image_url is provided, it's a GCS URI or accessible.
                    # The agent-based flow requires a GCS URI.
                    if image_url.startswith('gs://'):
                        image_uri = image_url
                    else:
                        # This path is not fully supported for agent-based analysis yet.
                        logger.warning(f"Image URL '{image_url}' is not a GCS URI. Agent analysis may fail.")
                        image_uri = image_url # Pass it along, but it might not work.

                if not image_uri:
                    raise FileProcessingError("Could not get a GCS URI for the image, which is required for appraisal.")

            # Step 2: Get appraisal from Vertex AI Agent
            agent_result = {}
            with StepTracker(appraisal_id, ProcessingStep.VISION_ANALYSIS): # Re-using step for AI call
                if progress_tracker:
                    await progress_tracker.update(5, "Getting appraisal from AI Agent")
                
                agent_result = self.ai_service.get_appraisal_from_agent(
                    image_uri=image_uri,
                    user_query="Provide an estimated appraisal value, price range, and confidence score for the item in the image."
                )
                
                # The agent's response is now the primary source of information.
                # We'll extract the key fields from its response.
                # This part needs to be robustly parsed based on the agent's actual output.
                self._update_appraisal_record(appraisal_id, {
                    'vision_results': agent_result # Store the full agent response for now
                })

            # Step 3: Compile final results from agent response
            with StepTracker(appraisal_id, ProcessingStep.RESULT_COMPILATION):
                if progress_tracker:
                    await progress_tracker.update(10, "Finalizing results")
                
                # Placeholder parsing of the agent's response.
                # This should be updated once the agent's output format is finalized.
                estimated_value = agent_result.get('estimated_value', 0)
                price_range = agent_result.get('price_range', {'min': 0, 'max': 0})
                confidence = agent_result.get('confidence_score', 0)
                
                final_result = {
                    'appraisal_id': appraisal_id,
                    'estimated_value': estimated_value,
                    'currency': agent_result.get('currency', 'USD'),
                    'price_range': price_range,
                    'confidence_score': confidence,
                    'ai_analysis': agent_result, # The entire agent response
                    'market_analysis': {}, # No longer a separate step
                    'image_info': {
                        'image_path': image_uri, # GCS URI
                        'image_url': self.db.query(Appraisal).filter(Appraisal.id == appraisal_id).first().image_url if self.db else None
                    },
                    'processing_metadata': {
                        'processed_at': datetime.utcnow().isoformat(),
                        'processing_version': '2.0-agent',
                        'options_used': options
                    }
                }
            
            # Step 4: Store results
            with StepTracker(appraisal_id, ProcessingStep.DATABASE_STORAGE):
                if progress_tracker:
                    await progress_tracker.update(11, "Storing results")
                
                await self._finalize_appraisal(appraisal_id, final_result)
            
            logger.info(f"Appraisal processing completed: {appraisal_id}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Appraisal processing failed for {appraisal_id}: {e}")
            await self._handle_processing_error(appraisal_id, e)
            raise
    
    def get_appraisal_status(self, appraisal_id: str) -> Optional[Dict]:
        """Get appraisal status"""
        log_service_call("AppraisalService", "get_appraisal_status", appraisal_id=appraisal_id)
        
        try:
            # Use database directly for simplicity in development
            if self.db:
                db_appraisal = self.db.query(Appraisal).filter(Appraisal.id == appraisal_id).first()
                if db_appraisal:
                    result = {
                        'appraisal_id': appraisal_id,
                        'status': db_appraisal.status,
                        'created_at': db_appraisal.created_at.isoformat(),
                        'updated_at': db_appraisal.updated_at.isoformat() if db_appraisal.updated_at else None,
                        'completed_at': db_appraisal.completed_at.isoformat() if db_appraisal.completed_at else None,
                        'estimated_value': float(db_appraisal.market_price) if db_appraisal.market_price else None,
                        'confidence_score': float(db_appraisal.confidence_score) if db_appraisal.confidence_score else None
                    }
                    
                    log_service_result("AppraisalService", "get_appraisal_status", True, 
                                     status=result['status'])
                    
                    return result
            
            return None
            
        except Exception as e:
            self.log_error(e, "get_appraisal_status")
            return None
    
    def get_appraisal_result(self, appraisal_id: str) -> Optional[Dict]:
        """Get completed appraisal result"""
        log_service_call("AppraisalService", "get_appraisal_result", appraisal_id=appraisal_id)
        
        try:
            if not self.db:
                return None
            
            db_appraisal = self.db.query(Appraisal).filter(Appraisal.id == appraisal_id).first()
            
            if not db_appraisal:
                return None
            
            if db_appraisal.status != "completed":
                return None
            
            # Compile result from database
            result = {
                'appraisal_id': appraisal_id,
                'estimated_value': float(db_appraisal.market_price) if db_appraisal.market_price else None,
                'price_range': {
                    'min': float(db_appraisal.price_range_min) if db_appraisal.price_range_min else None,
                    'max': float(db_appraisal.price_range_max) if db_appraisal.price_range_max else None
                },
                'confidence_score': float(db_appraisal.confidence_score) if db_appraisal.confidence_score else None,
                'vision_analysis': db_appraisal.vision_results,
                'detected_objects': db_appraisal.detected_objects,
                'embeddings': db_appraisal.embeddings,
                'similar_items': db_appraisal.similar_items,
                'image_info': {
                    'image_path': db_appraisal.image_path,
                    'image_url': db_appraisal.image_url
                },
                'created_at': db_appraisal.created_at.isoformat(),
                'completed_at': db_appraisal.completed_at.isoformat() if db_appraisal.completed_at else None
            }
            
            log_service_result("AppraisalService", "get_appraisal_result", True)
            
            return result
            
        except Exception as e:
            self.log_error(e, "get_appraisal_result")
            return None
    
    def list_user_appraisals(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List appraisals for a user"""
        log_service_call("AppraisalService", "list_user_appraisals", 
                        user_id=user_id, limit=limit, offset=offset)
        
        try:
            if not self.db:
                return []
            
            appraisals = (self.db.query(Appraisal)
                         .filter(Appraisal.user_id == user_id)
                         .order_by(Appraisal.created_at.desc())
                         .limit(limit)
                         .offset(offset)
                         .all())
            
            results = []
            for appraisal in appraisals:
                results.append({
                    'appraisal_id': appraisal.id,
                    'status': appraisal.status,
                    'estimated_value': float(appraisal.market_price) if appraisal.market_price else None,
                    'confidence_score': float(appraisal.confidence_score) if appraisal.confidence_score else None,
                    'image_url': appraisal.image_url,
                    'created_at': appraisal.created_at.isoformat(),
                    'completed_at': appraisal.completed_at.isoformat() if appraisal.completed_at else None
                })
            
            log_service_result("AppraisalService", "list_user_appraisals", True, count=len(results))
            
            return results
            
        except Exception as e:
            self.log_error(e, "list_user_appraisals")
            return []
    
    def cancel_appraisal(self, appraisal_id: str, user_id: Optional[int] = None) -> bool:
        """Cancel an appraisal"""
        log_service_call("AppraisalService", "cancel_appraisal", 
                        appraisal_id=appraisal_id, user_id=user_id)
        
        try:
            # Update status tracker
            status_info = get_appraisal_status(appraisal_id)
            if status_info:
                status_info.cancel()
            
            # Update database
            if self.db:
                query = self.db.query(Appraisal).filter(Appraisal.id == appraisal_id)
                if user_id:
                    query = query.filter(Appraisal.user_id == user_id)
                
                appraisal = query.first()
                if appraisal:
                    appraisal.status = ModelAppraisalStatus.FAILED
                    appraisal.error_message = "Cancelled by user"
                    appraisal.updated_at = datetime.utcnow()
                    self.db.commit()
            
            log_service_result("AppraisalService", "cancel_appraisal", True)
            
            return True
            
        except Exception as e:
            self.log_error(e, "cancel_appraisal")
            return False
    
    def _create_appraisal_record(self, appraisal_id: str, user_id: Optional[int], filename: Optional[str], options: Dict, image_path: Optional[str] = None, image_url: Optional[str] = None) -> Optional[Appraisal]:
        """Create initial appraisal database record"""
        try:
            if not self.db:
                return None
            
            appraisal = Appraisal(
                id=appraisal_id,
                user_id=user_id,
                status="pending",
                created_at=datetime.utcnow(),
                image_path=image_path,
                image_url=image_url
            )
            
            self.db.add(appraisal)
            self.db.commit()
            
            return appraisal
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create appraisal record: {e}")
            if self.db:
                self.db.rollback()
            return None
    
    def _update_appraisal_record(self, appraisal_id: str, updates: Dict):
        """Update appraisal database record"""
        try:
            if not self.db:
                return
            
            appraisal = self.db.query(Appraisal).filter(Appraisal.id == appraisal_id).first()
            
            if appraisal:
                for key, value in updates.items():
                    if hasattr(appraisal, key):
                        setattr(appraisal, key, value)
                
                appraisal.updated_at = datetime.utcnow()
                self.db.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to update appraisal record: {e}")
            if self.db:
                self.db.rollback()
    
    async def _finalize_appraisal(self, appraisal_id: str, result: Dict):
        """Finalize appraisal with results"""
        try:
            # Update status tracker
            status_info = get_appraisal_status(appraisal_id)
            if status_info:
                status_info.complete(result)
            
            # Update database
            if self.db:
                updates = {
                    'status': "completed",
                    'market_price': result.get('estimated_value'),
                    'price_range_min': result.get('price_range', {}).get('min'),
                    'price_range_max': result.get('price_range', {}).get('max'),
                    'confidence_score': result.get('confidence_score'),
                    'similar_items': result.get('market_analysis', {}).get('comparable_items'),
                    'completed_at': datetime.utcnow()
                }
                
                self._update_appraisal_record(appraisal_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to finalize appraisal {appraisal_id}: {e}")
    
    async def _handle_processing_error(self, appraisal_id: str, error: Exception):
        """Handle processing error"""
        try:
            error_message = str(error)
            
            # Update status tracker
            status_info = get_appraisal_status(appraisal_id)
            if status_info:
                status_info.fail(error_message, {'error_type': type(error).__name__})
            
            # Update database
            if self.db:
                updates = {
                    'status': "failed",
                    'error_message': error_message,
                    'updated_at': datetime.utcnow()
                }
                
                self._update_appraisal_record(appraisal_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to handle processing error for {appraisal_id}: {e}")
    
    def _check_cache(self, file_content: Optional[bytes], filename: Optional[str], options: Dict) -> Optional[Dict]:
        """Check for cached result"""
        try:
            if not file_content:
                return None
            
            cache_data = {
                'file_hash': self._calculate_file_hash(file_content),
                'filename': filename,
                'options': options
            }
            
            return get_cached_appraisal(cache_data)
            
        except Exception as e:
            logger.warning(f"Failed to check cache: {e}")
            return None
    
    def _cache_result(self, file_content: Optional[bytes], filename: Optional[str], options: Dict, result: Dict):
        """Cache appraisal result"""
        try:
            if not file_content:
                return
            
            cache_data = {
                'file_hash': self._calculate_file_hash(file_content),
                'filename': filename,
                'options': options
            }
            
            cache_appraisal_result(cache_data, result, tags=['appraisal'])
            
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate hash of file content"""
        import hashlib
        return hashlib.sha256(file_content).hexdigest()
    
    def health_check(self) -> bool:
        """Health check for appraisal service"""
        try:
            # Check all dependent services
            services_healthy = [
                self.image_service.health_check(),
                self.ai_service.health_check(),
                self.market_service.health_check(),
                self.price_service.health_check()
            ]
            
            return all(services_healthy)
            
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("appraisal_service", AppraisalService, singleton=False)