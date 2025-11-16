#Agent/base_agent.py
"""
Base Agent Class - Common functionality for all agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import time
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agents.{agent_name}")
    
    def log_start(self, task: str, **kwargs):
        """Log task start"""
        self.logger.info(f"[{self.agent_name}] Starting: {task}")
        if kwargs:
            self.logger.debug(f"Parameters: {kwargs}")
    
    def log_complete(self, task: str, duration: float):
        """Log task completion"""
        self.logger.info(f"[{self.agent_name}] Completed: {task} in {duration:.2f}s")
    
    def log_error(self, task: str, error: Exception):
        """Log error"""
        self.logger.error(f"[{self.agent_name}] Error in {task}: {str(error)}")
    
    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters"""
        pass
    
    @abstractmethod
    def process(self, **kwargs) -> Dict[str, Any]:
        """Main processing logic"""
        pass
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute agent with validation and error handling"""
        try:
            # Validate input
            if not self.validate_input(**kwargs):
                return {
                    "success": False,
                    "error": "Invalid input parameters",
                    "agent": self.agent_name
                }
            
            # Process
            self.log_start("execution", **kwargs)
            start_time = time.time()
            
            result = self.process(**kwargs)
            
            duration = time.time() - start_time
            self.log_complete("execution", duration)
            
            # Add metadata
            result["agent"] = self.agent_name
            result["processing_time"] = duration
            
            return result
            
        except Exception as e:
            self.log_error("execution", e)
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name
            }
