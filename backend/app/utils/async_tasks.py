import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback

from app.utils.logging import get_logger, set_correlation_id
from app.utils.exceptions import AIProcessingError

logger = get_logger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class TaskProgress:
    """Progress tracking for tasks"""
    current_step: int = 0
    total_steps: int = 1
    step_name: str = "Starting"
    percentage: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, step: int, step_name: str, details: Optional[Dict] = None):
        """Update progress"""
        self.current_step = step
        self.step_name = step_name
        self.percentage = (step / self.total_steps) * 100 if self.total_steps > 0 else 0
        if details:
            self.details.update(details)

@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    error_details: Optional[Dict] = None
    progress: TaskProgress = field(default_factory=TaskProgress)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    correlation_id: Optional[str] = None

@dataclass
class TaskDefinition:
    """Task definition"""
    task_id: str
    task_type: str
    priority: TaskPriority
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

class TaskManager:
    """Async task manager for handling background processing"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskResult] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_queue: List[TaskDefinition] = []
        self.workers: List[asyncio.Task] = []
        self.max_workers = 5
        self.is_running = False
        self.worker_semaphore = asyncio.Semaphore(self.max_workers)
        
    async def start(self):
        """Start the task manager"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker_{i}"))
            self.workers.append(worker)
        
        logger.info(f"Task manager started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the task manager"""
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Cancel running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        logger.info("Task manager stopped")
    
    async def submit_task(
        self,
        task_type: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        metadata: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Submit a task for execution
        
        Args:
            task_type: Type of task
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            max_retries: Maximum retry attempts
            timeout: Task timeout in seconds
            metadata: Additional metadata
            correlation_id: Correlation ID for tracking
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        if kwargs is None:
            kwargs = {}
        
        if metadata is None:
            metadata = {}
        
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        task_def = TaskDefinition(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
            timeout=timeout,
            metadata=metadata,
            correlation_id=correlation_id
        )
        
        # Create task result
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            correlation_id=correlation_id
        )
        
        self.tasks[task_id] = task_result
        
        # Add to queue (sorted by priority)
        self.task_queue.append(task_def)
        self.task_queue.sort(key=lambda t: self._priority_value(t.priority), reverse=True)
        
        logger.info(f"Task submitted: {task_id} ({task_type})")
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get task status"""
        return self.tasks.get(task_id)
    
    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress"""
        task_result = self.tasks.get(task_id)
        return task_result.progress if task_result else None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            
            # Update task status
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus.CANCELLED
                self.tasks[task_id].completed_at = datetime.utcnow()
            
            logger.info(f"Task cancelled: {task_id}")
            return True
        
        # Remove from queue if pending
        self.task_queue = [t for t in self.task_queue if t.task_id != task_id]
        
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.CANCELLED
            return True
        
        return False
    
    async def _worker(self, worker_name: str):
        """Worker task that processes the queue"""
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get next task from queue
                if not self.task_queue:
                    await asyncio.sleep(0.1)
                    continue
                
                task_def = self.task_queue.pop(0)
                
                # Execute task
                async with self.worker_semaphore:
                    await self._execute_task(task_def, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _execute_task(self, task_def: TaskDefinition, worker_name: str):
        """Execute a single task"""
        task_id = task_def.task_id
        
        try:
            # Set correlation ID
            if task_def.correlation_id:
                set_correlation_id(task_def.correlation_id)
            
            # Update task status
            task_result = self.tasks[task_id]
            task_result.status = TaskStatus.RUNNING
            task_result.started_at = datetime.utcnow()
            
            logger.info(f"Worker {worker_name} executing task {task_id} ({task_def.task_type})")
            
            # Create async task
            if asyncio.iscoroutinefunction(task_def.func):
                # Async function
                coro = task_def.func(*task_def.args, **task_def.kwargs)
            else:
                # Sync function - run in executor
                loop = asyncio.get_event_loop()
                coro = loop.run_in_executor(None, lambda: task_def.func(*task_def.args, **task_def.kwargs))
            
            # Apply timeout if specified
            if task_def.timeout:
                async_task = asyncio.create_task(coro)
                self.running_tasks[task_id] = async_task
                
                try:
                    result = await asyncio.wait_for(async_task, timeout=task_def.timeout)
                except asyncio.TimeoutError:
                    async_task.cancel()
                    raise AIProcessingError(f"Task {task_id} timed out after {task_def.timeout} seconds")
            else:
                result = await coro
            
            # Task completed successfully
            task_result.status = TaskStatus.COMPLETED
            task_result.result = result
            task_result.completed_at = datetime.utcnow()
            task_result.duration_seconds = (task_result.completed_at - task_result.started_at).total_seconds()
            
            # Update progress to 100%
            task_result.progress.update(
                task_result.progress.total_steps,
                "Completed",
                {"completed": True}
            )
            
            logger.info(f"Task {task_id} completed successfully in {task_result.duration_seconds:.2f}s")
            
        except asyncio.CancelledError:
            task_result.status = TaskStatus.CANCELLED
            task_result.completed_at = datetime.utcnow()
            logger.info(f"Task {task_id} was cancelled")
            
        except Exception as e:
            # Task failed
            error_msg = str(e)
            error_details = {
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            
            task_result.error = error_msg
            task_result.error_details = error_details
            task_result.completed_at = datetime.utcnow()
            
            # Check if we should retry
            if task_result.retry_count < task_def.max_retries:
                task_result.retry_count += 1
                task_result.status = TaskStatus.RETRYING
                
                logger.warning(f"Task {task_id} failed, retrying ({task_result.retry_count}/{task_def.max_retries}): {error_msg}")
                
                # Add back to queue with delay
                await asyncio.sleep(task_def.retry_delay * task_result.retry_count)
                self.task_queue.append(task_def)
            else:
                task_result.status = TaskStatus.FAILED
                logger.error(f"Task {task_id} failed permanently after {task_result.retry_count} retries: {error_msg}")
        
        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def _priority_value(self, priority: TaskPriority) -> int:
        """Get numeric value for priority"""
        priority_values = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        return priority_values.get(priority, 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics"""
        status_counts = {}
        for task in self.tasks.values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        return {
            'total_tasks': len(self.tasks),
            'running_tasks': len(self.running_tasks),
            'queued_tasks': len(self.task_queue),
            'max_workers': self.max_workers,
            'status_counts': status_counts,
            'is_running': self.is_running
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        tasks_to_remove = []
        for task_id, task_result in self.tasks.items():
            if (task_result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task_result.completed_at and task_result.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

# Global task manager instance
task_manager = TaskManager()

# Utility functions for progress tracking
class ProgressTracker:
    """Progress tracker for long-running operations"""
    
    def __init__(self, task_id: str, total_steps: int):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
    
    async def update(self, step: int, step_name: str, details: Optional[Dict] = None):
        """Update progress"""
        self.current_step = step
        
        task_result = await task_manager.get_task_status(self.task_id)
        if task_result:
            task_result.progress.update(step, step_name, details)
            logger.debug(f"Task {self.task_id} progress: {step}/{self.total_steps} - {step_name}")
    
    async def increment(self, step_name: str, details: Optional[Dict] = None):
        """Increment progress by one step"""
        await self.update(self.current_step + 1, step_name, details)

# Decorator for automatic progress tracking
def track_progress(total_steps: int):
    """Decorator to automatically track progress"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get task_id from kwargs or create one
            task_id = kwargs.get('task_id', str(uuid.uuid4()))
            tracker = ProgressTracker(task_id, total_steps)
            
            # Add tracker to kwargs
            kwargs['progress_tracker'] = tracker
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Utility functions
async def submit_appraisal_task(
    task_type: str,
    func: Callable,
    args: tuple = (),
    kwargs: Optional[Dict] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: Optional[float] = None,
    correlation_id: Optional[str] = None
) -> str:
    """Submit an appraisal-related task"""
    return await task_manager.submit_task(
        task_type=task_type,
        func=func,
        args=args,
        kwargs=kwargs or {},
        priority=priority,
        timeout=timeout,
        correlation_id=correlation_id
    )

async def wait_for_task_completion(
    task_id: str,
    timeout: Optional[float] = None,
    poll_interval: float = 1.0
) -> TaskResult:
    """Wait for a task to complete"""
    start_time = datetime.utcnow()
    
    while True:
        task_result = await task_manager.get_task_status(task_id)
        
        if not task_result:
            raise ValueError(f"Task {task_id} not found")
        
        if task_result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return task_result
        
        # Check timeout
        if timeout and (datetime.utcnow() - start_time).total_seconds() > timeout:
            raise asyncio.TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
        
        await asyncio.sleep(poll_interval)

async def start_task_manager():
    """Start the global task manager"""
    await task_manager.start()

async def stop_task_manager():
    """Stop the global task manager"""
    await task_manager.stop()