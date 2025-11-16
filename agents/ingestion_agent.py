#Agent/ingestion_agent.py
"""
Ingestion Agent - Handles document ingestion workflow
"""
from typing import Dict, Any
from agents.base_agent import BaseAgent
from workflows.ingestion_workflow import ingestion_app


class IngestionAgent(BaseAgent):
    """Agent for document ingestion and processing"""
    
    def __init__(self):
        super().__init__("IngestionAgent")
    
    def validate_input(self, **kwargs) -> bool:
        """Validate ingestion input"""
        required_fields = ['file_url', 'project_id', 'tender_number']
        return all(field in kwargs for field in required_fields)
    
    def process(self, **kwargs) -> Dict[str, Any]:
        """Process document ingestion"""
        self.logger.info(f"Processing document from: {kwargs.get('file_url')}")
        
        # Execute ingestion workflow
        final_state = ingestion_app.invoke(kwargs)
        
        if final_state.get('error'):
            return {
                "success": False,
                "error": final_state['error']
            }
        
        return {
            "success": True,
            "tender_file_id": final_state.get('tender_file_id'),
            "tender_id": final_state.get('tender_id'),
            "project_id": final_state.get('project_id'),
            "chunks_created": len(final_state.get('chunks', []))
        }

