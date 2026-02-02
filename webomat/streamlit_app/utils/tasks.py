"""
Background task utilities for Streamlit app
"""

import streamlit as st
import time
import threading
import queue
from typing import Callable, Any, Optional
from datetime import datetime


class TaskManager:
    """Manage background tasks with progress tracking"""

    def __init__(self):
        if "tasks" not in st.session_state:
            st.session_state.tasks = {}
        if "task_queue" not in st.session_state:
            st.session_state.task_queue = queue.Queue()

    def add_task(self, task_name: str, task_func: Callable, *args, **kwargs):
        """Add a background task"""
        task_id = f"{task_name}_{int(time.time())}"

        task_info = {
            "id": task_id,
            "name": task_name,
            "status": "running",
            "progress": 0,
            "message": "Starting...",
            "start_time": datetime.now(),
            "result": None,
            "error": None,
        }

        st.session_state.tasks[task_id] = task_info

        # Start task in background thread
        thread = threading.Thread(
            target=self._run_task, args=(task_id, task_func, args, kwargs), daemon=True
        )
        thread.start()

        return task_id

    def _run_task(self, task_id: str, task_func: Callable, args: tuple, kwargs: dict):
        """Run task in background thread"""
        try:
            # Create progress callback
            def progress_callback(progress: float, message: str = ""):
                st.session_state.tasks[task_id]["progress"] = progress
                st.session_state.tasks[task_id]["message"] = message

            # Call task with progress callback
            if (
                hasattr(task_func, "__code__")
                and "progress_callback" in task_func.__code__.co_varnames
            ):
                result = task_func(*args, progress_callback=progress_callback, **kwargs)
            else:
                result = task_func(*args, **kwargs)

            st.session_state.tasks[task_id]["status"] = "completed"
            st.session_state.tasks[task_id]["result"] = result
            st.session_state.tasks[task_id]["progress"] = 100
            st.session_state.tasks[task_id]["message"] = "Completed!"

        except Exception as e:
            st.session_state.tasks[task_id]["status"] = "failed"
            st.session_state.tasks[task_id]["error"] = str(e)
            st.session_state.tasks[task_id]["message"] = f"Error: {str(e)}"

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get task information"""
        return st.session_state.tasks.get(task_id)

    def get_running_tasks(self) -> list:
        """Get all running tasks"""
        return [
            task
            for task in st.session_state.tasks.values()
            if task["status"] == "running"
        ]

    def cleanup_old_tasks(self, hours: int = 1):
        """Remove old completed tasks"""
        current_time = datetime.now()
        tasks_to_remove = []

        for task_id, task in st.session_state.tasks.items():
            if task["status"] in ["completed", "failed"]:
                time_diff = (current_time - task["start_time"]).total_seconds()
                if time_diff > hours * 3600:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del st.session_state.tasks[task_id]


# Global task manager instance
task_manager = TaskManager()
