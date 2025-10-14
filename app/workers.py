"""
Background task execution using ThreadPoolExecutor.
Handles long-running analysis tasks without blocking the UI.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Dict, Optional
from queue import Queue
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskManager:
    """Manages background task execution for analysis jobs."""
    
    def __init__(self, max_workers: int = 2):
        """Initialize task manager with thread pool."""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}  # Store task futures
        self.task_queue = Queue()
        self.results = {}  # Store task results
        self.running = True
        
        # Start background worker
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background execution."""
        if not self.running:
            raise RuntimeError("Task manager is not running")
        
        # Create task info
        task_info = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'status': 'queued',
            'start_time': None,
            'end_time': None,
            'result': None,
            'error': None
        }
        
        # Add to queue
        self.task_queue.put(task_info)
        self.tasks[task_id] = task_info
        
        logger.info(f"Task {task_id} submitted to queue")
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task."""
        if task_id not in self.tasks:
            return {'status': 'not_found'}
        
        task = self.tasks[task_id]
        return {
            'status': task['status'],
            'start_time': task['start_time'],
            'end_time': task['end_time'],
            'result': task['result'],
            'error': task['error']
        }
    
    def get_task_result(self, task_id: str) -> Any:
        """Get result of a completed task."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        if task['status'] == 'completed':
            return task['result']
        elif task['status'] == 'failed':
            raise Exception(f"Task failed: {task['error']}")
        else:
            return None
    
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for a task to complete and return result."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        start_time = time.time()
        
        while task['status'] in ['queued', 'running']:
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            time.sleep(0.1)
        
        if task['status'] == 'completed':
            return task['result']
        elif task['status'] == 'failed':
            raise Exception(f"Task failed: {task['error']}")
        else:
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued or running task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] in ['queued', 'running']:
            task['status'] = 'cancelled'
            logger.info(f"Task {task_id} cancelled")
            return True
        
        return False
    
    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """List all tasks and their status."""
        return {task_id: self.get_task_status(task_id) for task_id in self.tasks}
    
    def cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """Clean up old completed tasks."""
        current_time = time.time()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if (task['status'] in ['completed', 'failed', 'cancelled'] and 
                task['end_time'] and 
                (current_time - task['end_time']) > max_age_seconds):
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old tasks")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the task manager."""
        self.running = False
        self.executor.shutdown(wait=wait)
        logger.info("Task manager shutdown")
    
    def _worker_loop(self):
        """Background worker loop that processes tasks."""
        while self.running:
            try:
                # Get next task from queue
                task_info = self.task_queue.get(timeout=1.0)
                
                # Update task status
                task_info['status'] = 'running'
                task_info['start_time'] = time.time()
                
                logger.info(f"Starting task {task_info['id']}")
                
                try:
                    # Execute task
                    result = task_info['func'](*task_info['args'], **task_info['kwargs'])
                    
                    # Update task with result
                    task_info['status'] = 'completed'
                    task_info['result'] = result
                    task_info['end_time'] = time.time()
                    
                    logger.info(f"Task {task_info['id']} completed successfully")
                    
                except Exception as e:
                    # Update task with error
                    task_info['status'] = 'failed'
                    task_info['error'] = str(e)
                    task_info['end_time'] = time.time()
                    
                    logger.error(f"Task {task_info['id']} failed: {e}")
                
                # Mark task as done
                self.task_queue.task_done()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Worker loop error: {e}")
                time.sleep(0.1)

class AnalysisTask:
    """Wrapper for analysis tasks with progress tracking."""
    
    def __init__(self, task_manager: TaskManager):
        """Initialize analysis task wrapper."""
        self.task_manager = task_manager
        self.task_id = None
    
    def run_analysis(self, analysis_func: Callable, *args, **kwargs) -> str:
        """Run analysis function in background."""
        self.task_id = f"analysis_{int(time.time() * 1000)}"
        return self.task_manager.submit_task(self.task_id, analysis_func, *args, **kwargs)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get progress of current analysis."""
        if not self.task_id:
            return {'status': 'not_started'}
        
        return self.task_manager.get_task_status(self.task_id)
    
    def get_result(self) -> Any:
        """Get result of current analysis."""
        if not self.task_id:
            return None
        
        return self.task_manager.get_task_result(self.task_id)
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> Any:
        """Wait for analysis to complete."""
        if not self.task_id:
            return None
        
        return self.task_manager.wait_for_task(self.task_id, timeout)
