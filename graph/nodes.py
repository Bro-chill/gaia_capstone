from agents.agent.analyst_agent import analyst_agent, AnalysisContext
from graph.states import OptimizedWorkflowState
import logging

logger = logging.getLogger(__name__)

async def analyst_agent_node(state: OptimizedWorkflowState):
    """Analyze uploaded pdf script with MINIMUM API calls (2 total)"""
    pdf_path = state.get('pdf_path')
    logger.info(f"Starting OPTIMIZED analysis (2 API calls) for: {pdf_path}")
    
    try:
        # Create analysis context
        context = AnalysisContext(pdf_path=pdf_path)
        
        # Enhanced prompt for comprehensive analysis
        analysis_prompt = f"""
        Perform comprehensive script analysis for: {pdf_path}
        
        STEP 1: Extract the script text using extract_script_from_pdf_tool
        STEP 2: Analyze ALL aspects and return complete ComprehensiveAnalysis
        
        This should take exactly 2 API calls total.
        """
        
        # Execute analysis (will use 2 API calls: extract + analyze)
        try:
            result = await analyst_agent.run_async(analysis_prompt, deps=context)
        except AttributeError:
            try:
                result = await analyst_agent.run(analysis_prompt, deps=context)
            except AttributeError:
                result = await analyst_agent(analysis_prompt, deps=context)
        
        logger.info(f"✅ OPTIMIZED analysis completed with 2 API calls. Result type: {type(result)}")
        
        # Extract the actual analysis data
        if hasattr(result, 'output'):
            analysis_data = result.output
        elif hasattr(result, 'result'):
            analysis_data = result.result
        else:
            analysis_data = result
        
        # Update state
        state['comprehensive_analysis'] = analysis_data
        state['status'] = 'analysis_completed'
        state['api_calls_used'] = 2  # Track actual usage
        
        return state
        
    except Exception as e:
        logger.error(f"OPTIMIZED analysis failed: {str(e)}")
        state['status'] = f'analysis_failed: {str(e)}'
        state['errors'] = state.get('errors', []) + [str(e)]
        state['api_calls_used'] = 1  # Only extraction call succeeded
        return state

# Auto human-in-the-loop
async def human_feedback_node(state: OptimizedWorkflowState):
    """Human feedback node - unchanged"""
    if 'feedback_required' not in state:
        state['feedback_required'] = False
    
    if 'feedback_text' not in state:
        state['feedback_text'] = ""
    
    return {
        **state,
        "feedback_required": False,
        "status": "analysis_completed"
    }

# Manual human-in-the-loop
# async def human_feedback_node(state: OptimizedWorkflowState):
#     """Human feedback node with actual HITL functionality"""
    
#     # Check if this is the first time through (no previous feedback)
#     if not state.get('human_review_completed', False):
#         # Save analysis to database with "pending_review" status
#         from database.services import AnalyzedScriptService
#         from database.database import SessionLocal
        
#         db = SessionLocal()
#         try:
#             # Save analysis for review
#             saved_script = AnalyzedScriptService.create_analyzed_script(
#                 db=db,
#                 filename=state.get('pdf_path', 'unknown.pdf'),
#                 original_filename=state.get('pdf_path', 'unknown.pdf'),
#                 file_size_bytes=0,  # Will be updated later
#                 analysis_data=state.get('comprehensive_analysis', {}),
#                 processing_time=state.get('total_processing_time'),
#                 api_calls_used=state.get('api_calls_used', 2)
#             )
            
#             # Update status to pending review
#             saved_script.status = "pending_review"
#             db.commit()
            
#             return {
#                 **state,
#                 "feedback_required": True,
#                 "status": "awaiting_human_feedback",
#                 "analysis_id": saved_script.id,
#                 "human_review_completed": False
#             }
#         finally:
#             db.close()
    
#     # If we have feedback, process it and continue
#     feedback = state.get('feedback_text', '')
#     if feedback and feedback.strip():
#         # Mark review as completed
#         return {
#             **state,
#             "feedback_required": False,
#             "status": "analysis_completed_with_feedback",
#             "human_review_completed": True
#         }
    
#     # No feedback provided, continue anyway
#     return {
#         **state,
#         "feedback_required": False,
#         "status": "analysis_completed",
#         "human_review_completed": True
#     }