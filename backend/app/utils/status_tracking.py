from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError

logger = get_logger(__name__)

class AppraisalStatus(str, Enum):
    """Appraisal processing status"""
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    UPLOADING = "uploading"
    PROCESSING_IMAGE = "processing_image"
    ANALYZING_AI = "analyzing_ai"
    SEARCHING_MARKET = "searching_market"
    CALCULATING_PRICE = "calculating_price"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingStep(str, Enum):
    """Individual processing steps"""
    IMAGE_VALIDATION = "image_validation"
    IMAGE_UPLOAD = "image_upload"
    METADATA_EXTRACTION = "metadata_extraction"
    VISION_ANALYSIS = "vision_analysis"
    EMBEDDING_GENERATION = "embedding_generation"
    FEATURE_EXTRACTION = "feature_extraction"
    SIMILARITY_SEARCH = "similarity_search"
    MARKET_ANALYSIS = "market_analysis"
    PRICE_CALCULATION = "price_calculation"
    RESULT_COMPILATION = "result_compilation"
    DATABASE_STORAGE = "database_storage"

@dataclass
class StepResult:
    """Result of a processing step"""
    step: ProcessingStep
    status: str  # success, failed, skipped
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, result: Any = None, error: Optional[str] = None):
        """Mark step as completed"""
        self.completed_at = datetime.utcnow()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        if error:
            self.status = "failed"
            self.error = error
        else:
            self.status = "success"
            self.result = result

@dataclass
class AppraisalStatusInfo:
    """Complete appraisal status information"""
    appraisal_id: str
    user_id: Optional[str]
    status: AppraisalStatus
    current_step: Optional[ProcessingStep] = None
    progress_percentage: float = 0.0
    
    # Timing information
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    started_processing_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion_at: Optional[datetime] = None
    
    # Processing details
    steps_completed: List[StepResult] = field(default_factory=list)
    current_step_started_at: Optional[datetime] = None
    total_steps: int = 11  # Default number of processing steps
    
    # Results and errors
    final_result: Optional[Dict] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict] = None
    
    # Metadata
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def update_status(self, status: AppraisalStatus, step: Optional[ProcessingStep] = None):
        """Update the appraisal status"""
        self.status = status
        
        if step:
            self.current_step = step
            self.current_step_started_at = datetime.utcnow()
        
        # Update progress percentage
        self.progress_percentage = self._calculate_progress()
        
        # Set processing start time
        if status != AppraisalStatus.SUBMITTED and not self.started_processing_at:
            self.started_processing_at = datetime.utcnow()
        
        # Set completion time
        if status in [AppraisalStatus.COMPLETED, AppraisalStatus.FAILED, AppraisalStatus.CANCELLED]:
            self.completed_at = datetime.utcnow()
        
        logger.info(f"Appraisal {self.appraisal_id} status updated: {status} ({self.progress_percentage:.1f}%)")
    
    def start_step(self, step: ProcessingStep) -> StepResult:
        """Start a processing step"""
        self.current_step = step
        self.current_step_started_at = datetime.utcnow()
        
        step_result = StepResult(
            step=step,
            status="running",
            started_at=self.current_step_started_at
        )
        
        self.steps_completed.append(step_result)
        self.progress_percentage = self._calculate_progress()
        
        logger.debug(f"Appraisal {self.appraisal_id} started step: {step}")
        
        return step_result
    
    def complete_step(self, step: ProcessingStep, result: Any = None, error: Optional[str] = None):
        """Complete a processing step"""
        # Find the step result
        step_result = None
        for sr in reversed(self.steps_completed):
            if sr.step == step:
                step_result = sr
                break
        
        if step_result:
            step_result.complete(result, error)
            
            if error:
                logger.warning(f"Appraisal {self.appraisal_id} step {step} failed: {error}")
            else:
                logger.debug(f"Appraisal {self.appraisal_id} completed step: {step} in {step_result.duration_ms}ms")
        
        self.progress_percentage = self._calculate_progress()
        
        # Update estimated completion time
        self._update_estimated_completion()
    
    def fail(self, error_message: str, error_details: Optional[Dict] = None):
        """Mark appraisal as failed"""
        self.status = AppraisalStatus.FAILED
        self.error_message = error_message
        self.error_details = error_details
        self.completed_at = datetime.utcnow()
        
        # Complete current step as failed if running
        if self.current_step:
            self.complete_step(self.current_step, error=error_message)
        
        logger.error(f"Appraisal {self.appraisal_id} failed: {error_message}")
    
    def complete(self, result: Dict):
        """Mark appraisal as completed"""
        self.status = AppraisalStatus.COMPLETED
        self.final_result = result
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        
        logger.info(f"Appraisal {self.appraisal_id} completed successfully")
    
    def cancel(self):
        """Cancel the appraisal"""
        self.status = AppraisalStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        logger.info(f"Appraisal {self.appraisal_id} cancelled")
    
    def _calculate_progress(self) -> float:
        """Calculate progress percentage"""
        if self.status == AppraisalStatus.COMPLETED:
            return 100.0
        
        if self.status in [AppraisalStatus.FAILED, AppraisalStatus.CANCELLED]:
            return 0.0
        
        # Count completed steps
        completed_steps = len([sr for sr in self.steps_completed if sr.status == "success"])
        
        # Add partial progress for current step
        progress = completed_steps
        if self.current_step and self.current_step_started_at:
            # Add 0.5 for step in progress
            progress += 0.5
        
        return min(100.0, (progress / self.total_steps) * 100)
    
    def _update_estimated_completion(self):
        """Update estimated completion time"""
        if not self.started_processing_at:
            return
        
        completed_steps = len([sr for sr in self.steps_completed if sr.status == "success"])
        
        if completed_steps == 0:
            return
        
        # Calculate average time per step
        total_time = sum(sr.duration_ms for sr in self.steps_completed if sr.duration_ms)
        avg_time_per_step = total_time / completed_steps
        
        # Estimate remaining time
        remaining_steps = self.total_steps - completed_steps
        estimated_remaining_ms = remaining_steps * avg_time_per_step
        
        self.estimated_completion_at = datetime.utcnow() + timedelta(milliseconds=estimated_remaining_ms)
    
    def get_duration(self) -> Optional[timedelta]:
        """Get total processing duration"""
        if self.started_processing_at and self.completed_at:
            return self.completed_at - self.started_processing_at
        elif self.started_processing_at:
            return datetime.utcnow() - self.started_processing_at
        return None
    
    def get_step_summary(self) -> Dict[str, Any]:
        """Get summary of all steps"""
        summary = {
            'total_steps': len(self.steps_completed),
            'successful_steps': len([sr for sr in self.steps_completed if sr.status == "success"]),
            'failed_steps': len([sr for sr in self.steps_completed if sr.status == "failed"]),
            'steps': []
        }
        
        for step_result in self.steps_completed:
            summary['steps'].append({
                'step': step_result.step,
                'status': step_result.status,
                'duration_ms': step_result.duration_ms,
                'error': step_result.error
            })
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'appraisal_id': self.appraisal_id,
            'user_id': self.user_id,
            'status': self.status,
            'current_step': self.current_step,
            'progress_percentage': round(self.progress_percentage, 1),
            'submitted_at': self.submitted_at.isoformat(),
            'started_processing_at': self.started_processing_at.isoformat() if self.started_processing_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_completion_at': self.estimated_completion_at.isoformat() if self.estimated_completion_at else None,
            'duration_seconds': self.get_duration().total_seconds() if self.get_duration() else None,
            'error_message': self.error_message,
            'step_summary': self.get_step_summary(),
            'correlation_id': self.correlation_id
        }

class StatusTracker:
    """Tracker for managing appraisal statuses"""
    
    def __init__(self):
        self.statuses: Dict[str, AppraisalStatusInfo] = {}
        self.cleanup_interval_hours = 24
    
    def create_appraisal_status(
        self,
        appraisal_id: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> AppraisalStatusInfo:
        """Create a new appraisal status"""
        status_info = AppraisalStatusInfo(
            appraisal_id=appraisal_id,
            user_id=user_id,
            status=AppraisalStatus.SUBMITTED,
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        self.statuses[appraisal_id] = status_info
        
        logger.info(f"Created appraisal status for {appraisal_id}")
        
        return status_info
    
    def get_status(self, appraisal_id: str) -> Optional[AppraisalStatusInfo]:
        """Get appraisal status"""
        return self.statuses.get(appraisal_id)
    
    def update_status(
        self,
        appraisal_id: str,
        status: AppraisalStatus,
        step: Optional[ProcessingStep] = None
    ) -> bool:
        """Update appraisal status"""
        if appraisal_id not in self.statuses:
            logger.warning(f"Appraisal status not found: {appraisal_id}")
            return False
        
        self.statuses[appraisal_id].update_status(status, step)
        return True
    
    def start_step(self, appraisal_id: str, step: ProcessingStep) -> Optional[StepResult]:
        """Start a processing step"""
        if appraisal_id not in self.statuses:
            return None
        
        return self.statuses[appraisal_id].start_step(step)
    
    def complete_step(
        self,
        appraisal_id: str,
        step: ProcessingStep,
        result: Any = None,
        error: Optional[str] = None
    ) -> bool:
        """Complete a processing step"""
        if appraisal_id not in self.statuses:
            return False
        
        self.statuses[appraisal_id].complete_step(step, result, error)
        return True
    
    def fail_appraisal(
        self,
        appraisal_id: str,
        error_message: str,
        error_details: Optional[Dict] = None
    ) -> bool:
        """Mark appraisal as failed"""
        if appraisal_id not in self.statuses:
            return False
        
        self.statuses[appraisal_id].fail(error_message, error_details)
        return True
    
    def complete_appraisal(self, appraisal_id: str, result: Dict) -> bool:
        """Mark appraisal as completed"""
        if appraisal_id not in self.statuses:
            return False
        
        self.statuses[appraisal_id].complete(result)
        return True
    
    def cancel_appraisal(self, appraisal_id: str) -> bool:
        """Cancel appraisal"""
        if appraisal_id not in self.statuses:
            return False
        
        self.statuses[appraisal_id].cancel()
        return True
    
    def get_user_appraisals(self, user_id: str) -> List[AppraisalStatusInfo]:
        """Get all appraisals for a user"""
        return [status for status in self.statuses.values() if status.user_id == user_id]
    
    def get_active_appraisals(self) -> List[AppraisalStatusInfo]:
        """Get all active (not completed/failed/cancelled) appraisals"""
        active_statuses = [
            AppraisalStatus.SUBMITTED,
            AppraisalStatus.VALIDATING,
            AppraisalStatus.UPLOADING,
            AppraisalStatus.PROCESSING_IMAGE,
            AppraisalStatus.ANALYZING_AI,
            AppraisalStatus.SEARCHING_MARKET,
            AppraisalStatus.CALCULATING_PRICE,
            AppraisalStatus.FINALIZING
        ]
        
        return [status for status in self.statuses.values() if status.status in active_statuses]
    
    def cleanup_old_statuses(self, max_age_hours: int = 24):
        """Clean up old completed/failed statuses"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        statuses_to_remove = []
        for appraisal_id, status in self.statuses.items():
            if (status.status in [AppraisalStatus.COMPLETED, AppraisalStatus.FAILED, AppraisalStatus.CANCELLED] and
                status.completed_at and status.completed_at < cutoff_time):
                statuses_to_remove.append(appraisal_id)
        
        for appraisal_id in statuses_to_remove:
            del self.statuses[appraisal_id]
        
        logger.info(f"Cleaned up {len(statuses_to_remove)} old appraisal statuses")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        status_counts = {}
        for status in self.statuses.values():
            status_counts[status.status] = status_counts.get(status.status, 0) + 1
        
        # Calculate average processing time
        completed_statuses = [s for s in self.statuses.values() 
                            if s.status == AppraisalStatus.COMPLETED and s.get_duration()]
        
        avg_processing_time = None
        if completed_statuses:
            total_time = sum(s.get_duration().total_seconds() for s in completed_statuses)
            avg_processing_time = total_time / len(completed_statuses)
        
        return {
            'total_appraisals': len(self.statuses),
            'status_counts': status_counts,
            'active_appraisals': len(self.get_active_appraisals()),
            'average_processing_time_seconds': avg_processing_time
        }

# Global status tracker instance
status_tracker = StatusTracker()

# Utility functions
def create_appraisal_status(
    appraisal_id: str,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> AppraisalStatusInfo:
    """Create a new appraisal status"""
    return status_tracker.create_appraisal_status(appraisal_id, user_id, correlation_id)

def get_appraisal_status(appraisal_id: str) -> Optional[AppraisalStatusInfo]:
    """Get appraisal status"""
    return status_tracker.get_status(appraisal_id)

def update_appraisal_status(
    appraisal_id: str,
    status: AppraisalStatus,
    step: Optional[ProcessingStep] = None
) -> bool:
    """Update appraisal status"""
    return status_tracker.update_status(appraisal_id, status, step)

# Context manager for step tracking
class StepTracker:
    """Context manager for automatic step tracking"""
    
    def __init__(self, appraisal_id: str, step: ProcessingStep):
        self.appraisal_id = appraisal_id
        self.step = step
        self.step_result = None
    
    def __enter__(self):
        self.step_result = status_tracker.start_step(self.appraisal_id, self.step)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Step failed
            error_message = str(exc_val) if exc_val else "Unknown error"
            status_tracker.complete_step(self.appraisal_id, self.step, error=error_message)
        else:
            # Step succeeded
            status_tracker.complete_step(self.appraisal_id, self.step)
        
        return False  # Don't suppress exceptions