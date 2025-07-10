from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import asyncio
import uuid

from app.services.base_service import BaseService
from app.services.appraisal_service import AppraisalService
from app.utils.async_tasks import (
    task_manager, TaskPriority, TaskStatus, submit_appraisal_task
)
from app.utils.status_tracking import (
    status_tracker, AppraisalStatus, ProcessingStep
)
from app.utils.result_caching import cleanup_all_caches, get_all_cache_stats
from app.utils.exceptions import ValidationError, AIProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry

logger = get_logger(__name__)

class ProcessingService(BaseService):
    """Service for managing processing workflows and system operations"""
    
    def __init__(self, db: Optional[Session] = None):
        super().__init__(db)
        self.appraisal_service = AppraisalService(db)
        
        # Configuration
        self.max_concurrent_tasks = 10
        self.cleanup_interval_hours = 6
        self.health_check_interval_minutes = 5
        
        # Workflow definitions
        self.workflows = {
            'standard_appraisal': self._standard_appraisal_workflow,
            'batch_appraisal': self._batch_appraisal_workflow,
            'priority_appraisal': self._priority_appraisal_workflow
        }
    
    def validate_input(self, data) -> bool:
        """Validate input for processing operations"""
        if not isinstance(data, dict):
            return False
        
        return 'workflow_type' in data or 'operation' in data
    
    def process(self, data: Dict) -> Dict:
        """Process workflow operation - main entry point"""
        if not self.validate_input(data):
            raise ValidationError("Invalid input data for processing operation")
        
        operation = data.get('operation', 'workflow')
        
        if operation == 'workflow':
            return self.execute_workflow(
                data.get('workflow_type', 'standard_appraisal'),
                data.get('workflow_data', {}),
                data.get('options', {})
            )
        elif operation == 'batch_process':
            return self.process_batch(
                data.get('items', []),
                data.get('options', {})
            )
        elif operation == 'system_status':
            return self.get_system_status()
        else:
            raise ValidationError(f"Unknown operation: {operation}")
    
    def execute_workflow(
        self,
        workflow_type: str,
        workflow_data: Dict,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Execute a processing workflow
        
        Args:
            workflow_type: Type of workflow to execute
            workflow_data: Data for the workflow
            options: Workflow options
            
        Returns:
            Workflow execution results
        """
        if options is None:
            options = {}
        
        log_service_call("ProcessingService", "execute_workflow", 
                        workflow_type=workflow_type)
        
        try:
            if workflow_type not in self.workflows:
                raise ValidationError(f"Unknown workflow type: {workflow_type}")
            
            # Get workflow function
            workflow_func = self.workflows[workflow_type]
            
            # Execute workflow
            result = workflow_func(workflow_data, options)
            
            log_service_result("ProcessingService", "execute_workflow", True, 
                             workflow_type=workflow_type)
            
            return result
            
        except Exception as e:
            self.log_error(e, "execute_workflow")
            raise
    
    def _standard_appraisal_workflow(self, data: Dict, options: Dict) -> Dict:
        """Standard appraisal workflow"""
        try:
            # Submit standard appraisal
            result = self.appraisal_service.submit_appraisal(
                file_content=data.get('file_content'),
                filename=data.get('filename'),
                user_id=data.get('user_id'),
                image_url=data.get('image_url'),
                options=options
            )
            
            return {
                'workflow_type': 'standard_appraisal',
                'execution_id': str(uuid.uuid4()),
                'appraisal_result': result,
                'status': 'submitted',
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Standard appraisal workflow failed: {e}")
            raise AIProcessingError(f"Workflow execution failed: {str(e)}")
    
    def _priority_appraisal_workflow(self, data: Dict, options: Dict) -> Dict:
        """Priority appraisal workflow with expedited processing"""
        try:
            # Set priority options
            priority_options = {
                **options,
                'priority': 'high',
                'timeout': 180,  # 3 minutes instead of 5
                'use_cache': True,
                'ai_options': {
                    'features': ['objects', 'labels', 'properties'],  # Faster subset
                    'generate_multimodal_embeddings': True
                }
            }
            
            # Submit with high priority
            result = self.appraisal_service.submit_appraisal(
                file_content=data.get('file_content'),
                filename=data.get('filename'),
                user_id=data.get('user_id'),
                image_url=data.get('image_url'),
                options=priority_options
            )
            
            return {
                'workflow_type': 'priority_appraisal',
                'execution_id': str(uuid.uuid4()),
                'appraisal_result': result,
                'status': 'submitted',
                'priority': 'high',
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Priority appraisal workflow failed: {e}")
            raise AIProcessingError(f"Priority workflow execution failed: {str(e)}")
    
    def _batch_appraisal_workflow(self, data: Dict, options: Dict) -> Dict:
        """Batch appraisal workflow for multiple items"""
        try:
            items = data.get('items', [])
            if not items:
                raise ValidationError("No items provided for batch processing")
            
            batch_id = str(uuid.uuid4())
            results = []
            
            # Process each item
            for i, item in enumerate(items):
                try:
                    # Submit appraisal for each item
                    appraisal_result = self.appraisal_service.submit_appraisal(
                        file_content=item.get('file_content'),
                        filename=item.get('filename'),
                        user_id=item.get('user_id'),
                        image_url=item.get('image_url'),
                        options=options
                    )
                    
                    results.append({
                        'item_index': i,
                        'item_id': item.get('id', f"item_{i}"),
                        'success': True,
                        'appraisal_result': appraisal_result
                    })
                    
                except Exception as e:
                    results.append({
                        'item_index': i,
                        'item_id': item.get('id', f"item_{i}"),
                        'success': False,
                        'error': str(e)
                    })
            
            successful_items = len([r for r in results if r['success']])
            
            return {
                'workflow_type': 'batch_appraisal',
                'execution_id': batch_id,
                'batch_results': {
                    'total_items': len(items),
                    'successful_items': successful_items,
                    'failed_items': len(items) - successful_items,
                    'items': results
                },
                'status': 'submitted',
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch appraisal workflow failed: {e}")
            raise AIProcessingError(f"Batch workflow execution failed: {str(e)}")
    
    def process_batch(self, items: List[Dict], options: Optional[Dict] = None) -> Dict:
        """Process a batch of items"""
        log_service_call("ProcessingService", "process_batch", items_count=len(items))
        
        try:
            return self._batch_appraisal_workflow({'items': items}, options or {})
            
        except Exception as e:
            self.log_error(e, "process_batch")
            raise
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        log_service_call("ProcessingService", "get_system_status")
        
        try:
            # Task manager statistics
            task_stats = task_manager.get_stats()
            
            # Status tracker statistics
            status_stats = status_tracker.get_statistics()
            
            # Cache statistics
            cache_stats = get_all_cache_stats()
            
            # Active appraisals
            active_appraisals = status_tracker.get_active_appraisals()
            
            # Service health checks
            service_health = {
                'appraisal_service': self.appraisal_service.health_check()
            }
            
            system_status = {
                'status': 'healthy' if all(service_health.values()) else 'degraded',
                'timestamp': datetime.utcnow().isoformat(),
                'task_manager': task_stats,
                'status_tracker': status_stats,
                'cache_stats': cache_stats,
                'active_appraisals': len(active_appraisals),
                'service_health': service_health,
                'system_metrics': {
                    'uptime_hours': self._calculate_uptime_hours(),
                    'total_processed_today': self._get_daily_processing_count(),
                    'avg_processing_time_seconds': status_stats.get('average_processing_time_seconds')
                }
            }
            
            log_service_result("ProcessingService", "get_system_status", True, 
                             status=system_status['status'])
            
            return system_status
            
        except Exception as e:
            self.log_error(e, "get_system_status")
            raise AIProcessingError(f"Failed to get system status: {str(e)}")
    
    def get_processing_queue_status(self) -> Dict:
        """Get processing queue status"""
        log_service_call("ProcessingService", "get_processing_queue_status")
        
        try:
            task_stats = task_manager.get_stats()
            active_appraisals = status_tracker.get_active_appraisals()
            
            # Categorize active appraisals by status
            status_breakdown = {}
            for appraisal in active_appraisals:
                status = appraisal.status
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            queue_status = {
                'queue_length': task_stats.get('queued_tasks', 0),
                'running_tasks': task_stats.get('running_tasks', 0),
                'active_appraisals': len(active_appraisals),
                'status_breakdown': status_breakdown,
                'worker_utilization': {
                    'active_workers': task_stats.get('running_tasks', 0),
                    'max_workers': task_stats.get('max_workers', 0),
                    'utilization_percent': (task_stats.get('running_tasks', 0) / max(1, task_stats.get('max_workers', 1))) * 100
                },
                'estimated_wait_time_minutes': self._estimate_queue_wait_time(task_stats)
            }
            
            log_service_result("ProcessingService", "get_processing_queue_status", True)
            
            return queue_status
            
        except Exception as e:
            self.log_error(e, "get_processing_queue_status")
            raise
    
    def cleanup_system(self, max_age_hours: int = 24) -> Dict:
        """Perform system cleanup"""
        log_service_call("ProcessingService", "cleanup_system", max_age_hours=max_age_hours)
        
        try:
            cleanup_results = {
                'started_at': datetime.utcnow().isoformat(),
                'operations': {}
            }
            
            # Cleanup old tasks
            try:
                asyncio.run(task_manager.cleanup_old_tasks(max_age_hours))
                cleanup_results['operations']['task_cleanup'] = 'completed'
            except Exception as e:
                cleanup_results['operations']['task_cleanup'] = f'failed: {str(e)}'
            
            # Cleanup old statuses
            try:
                status_tracker.cleanup_old_statuses(max_age_hours)
                cleanup_results['operations']['status_cleanup'] = 'completed'
            except Exception as e:
                cleanup_results['operations']['status_cleanup'] = f'failed: {str(e)}'
            
            # Cleanup cache
            try:
                cleanup_all_caches()
                cleanup_results['operations']['cache_cleanup'] = 'completed'
            except Exception as e:
                cleanup_results['operations']['cache_cleanup'] = f'failed: {str(e)}'
            
            cleanup_results['completed_at'] = datetime.utcnow().isoformat()
            cleanup_results['success'] = all(
                'completed' in result for result in cleanup_results['operations'].values()
            )
            
            log_service_result("ProcessingService", "cleanup_system", 
                             cleanup_results['success'])
            
            return cleanup_results
            
        except Exception as e:
            self.log_error(e, "cleanup_system")
            raise AIProcessingError(f"System cleanup failed: {str(e)}")
    
    def pause_processing(self) -> Dict:
        """Pause processing (stop accepting new tasks)"""
        log_service_call("ProcessingService", "pause_processing")
        
        try:
            # This would typically set a flag to stop accepting new tasks
            # For now, we'll return a status indicating the request
            
            result = {
                'action': 'pause_processing',
                'status': 'requested',
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Processing pause requested - new tasks will be queued but not processed'
            }
            
            log_service_result("ProcessingService", "pause_processing", True)
            
            return result
            
        except Exception as e:
            self.log_error(e, "pause_processing")
            raise
    
    def resume_processing(self) -> Dict:
        """Resume processing"""
        log_service_call("ProcessingService", "resume_processing")
        
        try:
            # This would typically clear the pause flag
            
            result = {
                'action': 'resume_processing',
                'status': 'requested',
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Processing resume requested - queued tasks will begin processing'
            }
            
            log_service_result("ProcessingService", "resume_processing", True)
            
            return result
            
        except Exception as e:
            self.log_error(e, "resume_processing")
            raise
    
    def _calculate_uptime_hours(self) -> float:
        """Calculate system uptime in hours"""
        # This would typically track actual uptime
        # For now, return a placeholder
        return 24.0
    
    def _get_daily_processing_count(self) -> int:
        """Get count of items processed today"""
        try:
            # Count completed appraisals from today
            today = datetime.utcnow().date()
            count = 0
            
            for appraisal in status_tracker.statuses.values():
                if (appraisal.status == AppraisalStatus.COMPLETED and 
                    appraisal.completed_at and 
                    appraisal.completed_at.date() == today):
                    count += 1
            
            return count
            
        except Exception:
            return 0
    
    def _estimate_queue_wait_time(self, task_stats: Dict) -> float:
        """Estimate queue wait time in minutes"""
        try:
            queued_tasks = task_stats.get('queued_tasks', 0)
            running_tasks = task_stats.get('running_tasks', 0)
            max_workers = task_stats.get('max_workers', 1)
            
            # Estimate based on average processing time (2 minutes per task)
            avg_processing_minutes = 2.0
            
            if running_tasks >= max_workers:
                # All workers busy
                tasks_ahead = queued_tasks
                wait_time = (tasks_ahead / max_workers) * avg_processing_minutes
            else:
                # Some workers available
                wait_time = 0.0
            
            return round(wait_time, 1)
            
        except Exception:
            return 0.0
    
    def health_check(self) -> bool:
        """Health check for processing service"""
        try:
            # Check dependent services
            return self.appraisal_service.health_check()
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("processing_service", ProcessingService, singleton=True)