"""
Safe async execution utilities to prevent race conditions and event loop conflicts.
"""

import asyncio
import threading
import concurrent.futures
from typing import Any, Awaitable, Optional, TypeVar
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SafeAsyncRunner:
    """
    Thread-safe async runner that prevents event loop conflicts and race conditions.
    
    This utility safely executes async functions from sync contexts without creating
    dangerous event loop scenarios that can cause race conditions and memory leaks.
    """
    
    _thread_local = threading.local()
    _executor_pool = None
    _executor_lock = threading.Lock()
    
    @classmethod
    def _get_executor(cls) -> concurrent.futures.ThreadPoolExecutor:
        """Get or create thread pool executor for async operations"""
        with cls._executor_lock:
            if cls._executor_pool is None or cls._executor_pool._shutdown:
                cls._executor_pool = concurrent.futures.ThreadPoolExecutor(
                    max_workers=4,
                    thread_name_prefix="SafeAsyncRunner"
                )
        return cls._executor_pool
    
    @classmethod
    def run_safe(cls, coro: Awaitable[T], timeout: float = 30.0) -> T:
        """
        Safely run a coroutine from sync context without event loop conflicts.
        
        Args:
            coro: The coroutine to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            The result of the coroutine execution
            
        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
            Exception: Any exception raised by the coroutine
        """
        start_time = time.time()
        
        try:
            # First, try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - need to run in separate thread
                logger.debug("Running coroutine in separate thread (async context detected)")
                return cls._run_in_dedicated_thread(coro, timeout)
                
            except RuntimeError:
                # No running loop - safe to use asyncio.run
                logger.debug("Running coroutine with asyncio.run (no loop detected)")
                return asyncio.run(cls._with_timeout(coro, timeout))
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"SafeAsyncRunner failed after {execution_time:.2f}s: {e}",
                exc_info=True
            )
            raise
    
    @classmethod
    def _run_in_dedicated_thread(cls, coro: Awaitable[T], timeout: float) -> T:
        """
        Run coroutine in a dedicated thread with its own event loop.
        
        This prevents interference with the main event loop and ensures
        proper cleanup of resources.
        """
        def create_and_run():
            """Create new event loop and run coroutine"""
            # Create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            
            # Set the loop for this thread
            asyncio.set_event_loop(new_loop)
            
            try:
                # Run the coroutine with timeout
                return new_loop.run_until_complete(cls._with_timeout(coro, timeout))
            finally:
                # Ensure proper cleanup
                try:
                    # Cancel any remaining tasks
                    pending_tasks = [task for task in asyncio.all_tasks(new_loop) 
                                   if not task.done()]
                    
                    if pending_tasks:
                        logger.warning(f"Cancelling {len(pending_tasks)} pending tasks")
                        for task in pending_tasks:
                            task.cancel()
                        
                        # Wait briefly for tasks to cancel
                        new_loop.run_until_complete(
                            asyncio.gather(*pending_tasks, return_exceptions=True)
                        )
                finally:
                    # Close the loop
                    new_loop.close()
                    # Clear the thread's event loop
                    asyncio.set_event_loop(None)
        
        # Execute in thread pool with timeout
        executor = cls._get_executor()
        future = executor.submit(create_and_run)
        
        try:
            return future.result(timeout=timeout + 5)  # Add buffer for cleanup
        except concurrent.futures.TimeoutError:
            # Cancel the future if it's still running
            future.cancel()
            raise asyncio.TimeoutError(f"Coroutine execution exceeded {timeout}s timeout")
    
    @classmethod
    async def _with_timeout(cls, coro: Awaitable[T], timeout: float) -> T:
        """Wrap coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Coroutine timed out after {timeout}s")
            raise
    
    @classmethod
    def shutdown(cls):
        """Shutdown the executor pool and cleanup resources"""
        with cls._executor_lock:
            if cls._executor_pool and not cls._executor_pool._shutdown:
                logger.info("Shutting down SafeAsyncRunner executor pool")
                cls._executor_pool.shutdown(wait=True, cancel_futures=True)
                cls._executor_pool = None


class AsyncContextManager:
    """
    Context manager for safely handling async operations in sync contexts.
    
    Usage:
        with AsyncContextManager() as runner:
            result = runner.run(my_async_function())
    """
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.runner = SafeAsyncRunner()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup is handled by SafeAsyncRunner
        pass
    
    def run(self, coro: Awaitable[T]) -> T:
        """Run coroutine safely within the context"""
        return self.runner.run_safe(coro, self.timeout)


# Convenience function for simple usage
def run_async_safe(coro: Awaitable[T], timeout: float = 30.0) -> T:
    """
    Convenience function to safely run async code from sync context.
    
    Args:
        coro: The coroutine to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        The result of the coroutine execution
    """
    return SafeAsyncRunner.run_safe(coro, timeout)