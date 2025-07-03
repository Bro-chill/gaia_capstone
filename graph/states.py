from typing import TypedDict, List, Optional, Dict, Any
from agents.states.states import ComprehensiveAnalysis

class OptimizedWorkflowState(TypedDict, total=False):
    # Input
    pdf_path: str
    
    # Single comprehensive analysis result
    comprehensive_analysis: Optional[ComprehensiveAnalysis]
    
    # Human feedback
    feedback_required: bool
    feedback_text: str
    
    # Workflow status
    status: str
    errors: Optional[List[str]]
    
    # ADD THIS LINE:
    api_calls_used: Optional[int]  # Track actual API calls
    
    # Processing metadata
    processing_start_time: Optional[str]
    processing_end_time: Optional[str]
    total_processing_time: Optional[float]

    # If human-in-the-loop manual
    # analysis_id: Optional[str]
    # human_review_completed: Optional[bool]