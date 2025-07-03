from graph.workflow import create_workflow
from graph.states import OptimizedWorkflowState
import asyncio
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_optimized_script_analysis(pdf_path: str, timeout: int = 300) -> OptimizedWorkflowState:
    """
    Optimized script analysis with single API call
    """
    
    start_time = time.time()
    logger.info(f"Starting optimized script analysis for: {pdf_path}")
    
    try:
        # Create optimized workflow
        workflow = create_workflow()
        logger.info("Optimized workflow created successfully")
        
        # Initial state
        initial_state = {
            "pdf_path": pdf_path,
            "status": "started",
            "processing_start_time": datetime.now().isoformat(),
            "errors": [],
            "feedback_required": False,
            "feedback_text": ""
        }
        
        logger.info("Starting optimized workflow execution...")
        
        # Execute workflow with timeout
        try:
            result = await asyncio.wait_for(
                workflow.ainvoke(initial_state),
                timeout=timeout
            )
            logger.info(f"Optimized workflow completed. Result keys: {list(result.keys())}")
            
        except asyncio.TimeoutError:
            logger.error(f"Workflow timed out after {timeout} seconds")
            raise TimeoutError(f"Script analysis timed out after {timeout} seconds")
        
        # Add completion metadata
        processing_time = time.time() - start_time
        
        if isinstance(result, dict):
            result["processing_end_time"] = datetime.now().isoformat()
            result["total_processing_time"] = processing_time
            result["status"] = "completed"
        
        logger.info(f"Optimized script analysis completed in {processing_time:.2f} seconds")
        
        # Validate result
        _validate_optimized_result(result)
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Optimized script analysis failed after {processing_time:.2f} seconds: {str(e)}")
        
        # Return error state
        error_result = {
            "pdf_path": pdf_path,
            "status": f"failed: {str(e)}",
            "processing_start_time": datetime.now().isoformat(),
            "processing_end_time": datetime.now().isoformat(),
            "total_processing_time": processing_time,
            "errors": [str(e)],
            "feedback_required": False,
            "feedback_text": ""
        }
        
        return error_result

def _validate_optimized_result(result: OptimizedWorkflowState) -> None:
    """Validate optimized analysis result"""
    
    logger.info(f"Validating optimized result: {type(result)}")
    
    if not isinstance(result, dict):
        raise ValueError("Analysis result must be a dictionary")
    
    # Check for required fields
    if "pdf_path" not in result or "status" not in result:
        raise ValueError("Analysis result missing required fields")
    
    # Check if analysis was successful
    status = result.get("status", "")
    if status.startswith("failed") or status.startswith("error"):
        logger.warning(f"Analysis completed with failure status: {status}")
        return
    
    # Check for comprehensive analysis
    comprehensive_analysis = result.get("comprehensive_analysis")
    if comprehensive_analysis:
        logger.info("✅ Comprehensive analysis found")
        if hasattr(comprehensive_analysis, 'script_data'):
            logger.info(f"  Script data: {len(comprehensive_analysis.script_data.scenes)} scenes")
        if hasattr(comprehensive_analysis, 'cost_breakdown'):
            logger.info(f"  Cost analysis: ${comprehensive_analysis.cost_breakdown.total_costs}")
    else:
        logger.warning("No comprehensive analysis data found")
    
    logger.info("Optimized analysis validation passed")

# Backward compatibility
async def run_script_analysis(pdf_path: str, timeout: int = 300) -> OptimizedWorkflowState:
    """Backward compatible function name"""
    return await run_optimized_script_analysis(pdf_path, timeout)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        asyncio.run(run_optimized_script_analysis(pdf_path))
    else:
        print("Usage: python main.py <path_to_script.pdf>")

async def test_optimized_analysis(pdf_path: str) -> None:
    """Test function for optimized analysis"""
    try:
        result = await run_optimized_script_analysis(pdf_path)
        print("✅ Optimized analysis completed successfully!")
        print(f"Status: {result.get('status')}")
        print(f"Processing time: {result.get('total_processing_time', 0):.2f} seconds")
        
        comprehensive_analysis = result.get('comprehensive_analysis')
        if comprehensive_analysis:
            print(f"📄 Scenes: {len(comprehensive_analysis.script_data.scenes)}")
            print(f"👥 Characters: {len(comprehensive_analysis.script_data.total_characters)}")
            print(f"📍 Locations: {len(comprehensive_analysis.script_data.total_locations)}")
            print(f"💰 Total budget: ${comprehensive_analysis.cost_breakdown.total_costs:,.2f}")
            print(f"🏷️ Budget category: {comprehensive_analysis.cost_breakdown.budget_category}")
        
    except Exception as e:
        print(f"❌ Optimized analysis failed: {e}")