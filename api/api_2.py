from fastapi import FastAPI, HTTPException, UploadFile, Depends, File, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime
import os
import tempfile
import time
import asyncio
import logging
import json

from database.database import get_db, create_tables
from database.services import AnalyzedScriptService
from database.models import AnalyzedScript
from main import run_optimized_script_analysis
from .serializers import ResultSerializer
from .validators import (
    FileValidator, 
    AnalyzeScriptResponse, 
    DatabaseScriptResponse,
    ScriptListResponse,
    AnalysisValidator,
    SaveAnalysisRequest,
    SaveAnalysisResponse,
    HumanFeedback,
)
from .middleware import setup_middleware

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Script Analysis API",
    version="2.1.0",  # Updated version
    description="Comprehensive film script analysis with AI-powered insights and save compatibility"
)

setup_middleware(app)

# Main route endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Script Analysis API v2.1 is running",
        "status": "healthy",
        "version": "2.1.0",
        "features": [
            "AI-powered script analysis",
            "Save-compatible response structure",
            "Separate analysis and storage endpoints",
            "Database storage with search",
            "Cost and production breakdowns",
            "RESTful API with validation",
            "Comprehensive error handling"
        ]
    }

# Health endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "script-analysis-api",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "version": "2.1.0"
    }

# Analysis endpoint
@app.post("/analyze-script", response_model=AnalyzeScriptResponse)
async def analyze_script(
    file: UploadFile = File(...)
):
    """
    Analyze a script PDF file with save-compatible output structure
    """
    
    # Validate file
    validator = FileValidator()
    validator.validate_file(file)
    
    temp_file_path = None
    file_size = 0
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            file_size = validator.validate_file_size(content)
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        start_time = time.time()
        logger.info(f"Starting save-compatible analysis for {file.filename} ({file_size} bytes)")
        
        # Perform analysis with timeout
        try:
            result = await asyncio.wait_for(
                run_optimized_script_analysis(temp_file_path),
                timeout=300.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="Analysis timed out. Please try with a smaller script."
            )
        
        processing_time = time.time() - start_time
        logger.info(f"Analysis completed in {processing_time:.2f} seconds")
        
        # ✅ FIXED: Extract comprehensive_analysis correctly
        comprehensive_analysis = result.get('comprehensive_analysis')
        
        if not comprehensive_analysis:
            raise HTTPException(
                status_code=500,
                detail="Analysis completed but no comprehensive analysis data found"
            )
        
        # ✅ FIXED: Convert to dict if it's a Pydantic object
        if hasattr(comprehensive_analysis, 'model_dump'):
            analysis_data = comprehensive_analysis.model_dump()
        elif hasattr(comprehensive_analysis, 'dict'):
            analysis_data = comprehensive_analysis.dict()
        else:
            analysis_data = comprehensive_analysis
        
        # Validate analysis result
        try:
            from agents.states.states import ComprehensiveAnalysis
            # Validate by creating a temporary object
            temp_analysis = ComprehensiveAnalysis(**analysis_data)
            logger.info("✅ Analysis validation passed")
        except Exception as validation_error:
            logger.warning(f"Analysis validation warning: {validation_error}")
            # Continue despite validation warnings
        
        # Enhanced metadata
        enhanced_metadata = {
            "filename": file.filename,
            "original_filename": file.filename,
            "file_size_bytes": file_size,
            "processing_time_seconds": round(processing_time, 2),
            "timestamp": datetime.now().isoformat(),
            "api_calls_used": result.get('api_calls_used', 2)
        }
        
        # ✅ FIXED: Pre-built save request object with correct structure
        save_request_data = {
            "filename": file.filename,
            "original_filename": file.filename,
            "file_size_bytes": file_size,
            "analysis_data": analysis_data,  # ✅ Use the extracted dict
            "processing_time_seconds": round(processing_time, 2),
            "api_calls_used": result.get('api_calls_used', 2)
        }
        
        # ✅ ENHANCED: Response with correct structure
        response_data = {
            "success": True,
            "message": "Script analysis completed successfully",
            
            # Optimization info
            "optimization_info": {
                "actual_calls_used": result.get('api_calls_used', 2),
                "expected_calls": 2
            },
            
            # Enhanced metadata
            "metadata": enhanced_metadata,
            
            # ✅ FIXED: Both keys point to the same correct data
            "data": analysis_data,           # Backward compatibility
            "analysis_data": analysis_data,  # Save endpoint compatibility
            
            # ✅ FIXED: Ready-to-use save request object
            "save_request": save_request_data
        }
        
        logger.info("✅ Analysis completed with save-compatible structure")
        logger.info(f"Analysis data keys: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'Not a dict'}")
        
        return JSONResponse(status_code=200, content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        error_message = str(e)
        
        if "extract" in error_message.lower():
            raise HTTPException(status_code=422, detail=f"PDF extraction failed: {error_message}")
        elif "validation" in error_message.lower():
            raise HTTPException(status_code=422, detail=f"Script validation failed: {error_message}")
        elif "analysis" in error_message.lower():
            raise HTTPException(status_code=500, detail=f"Analysis failed: {error_message}")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {error_message}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

# Save analyzed script to DB endpoint
@app.post("/save-analysis", response_model=SaveAnalysisResponse)
async def save_analysis_to_database(
    request: SaveAnalysisRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Saving analysis for {request.filename} to database")
        
        # Enhanced validation of analysis data
        try:
            from agents.states.states import ComprehensiveAnalysis
            temp_analysis = ComprehensiveAnalysis(**request.analysis_data)  # ✅ FIXED
            AnalysisValidator.validate_comprehensive_analysis(temp_analysis)
            logger.info("Analysis data validation passed")
        except Exception as validation_error:
            logger.warning(f"Analysis validation warning: {validation_error}")
            # Continue with save despite validation warnings
        
        # Save to database
        saved_script = AnalyzedScriptService.create_analyzed_script(
            db=db,
            filename=request.filename,
            original_filename=request.original_filename or request.filename,
            file_size_bytes=request.file_size_bytes,
            analysis_data=request.analysis_data,  # ✅ FIXED: Direct assignment
            processing_time=request.processing_time_seconds,
            api_calls_used=request.api_calls_used
        )
        
        response_data = {
            "success": True,
            "message": "Analysis saved to database successfully",
            "database_id": saved_script.id,
            "saved_at": saved_script.created_at.isoformat(),
            "metadata": {
                "filename": saved_script.filename,
                "original_filename": saved_script.original_filename,
                "file_size_bytes": saved_script.file_size_bytes,
                "processing_time_seconds": saved_script.processing_time_seconds,
                "api_calls_used": saved_script.api_calls_used,
                "status": saved_script.status,
                "total_scenes": saved_script.total_scenes,
                "estimated_budget": saved_script.estimated_budget,
                "budget_category": saved_script.budget_category
            }
        }
        
        logger.info(f"Analysis saved to database with ID: {saved_script.id}")
        return JSONResponse(status_code=201, content=response_data)
        
    except Exception as e:
        logger.error(f"Failed to save analysis: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save analysis to database: {str(e)}"
        )

# Read all analyzed scripts from DB endpoint
@app.get("/analyzed-scripts", response_model=ScriptListResponse)
async def get_all_analyzed_scripts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    order_by: str = Query("created_at", description="Order by field"),
    order_direction: str = Query("desc", description="Order direction (asc/desc)"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search term for filename"),
    db: Session = Depends(get_db)
):
    """Get all analyzed scripts with enhanced filtering and search"""
    
    try:
        if search:
            scripts = AnalyzedScriptService.search_scripts(
                db=db, 
                search_term=search, 
                skip=skip, 
                limit=limit
            )
            total_count = len(scripts)
        elif status_filter:
            scripts = AnalyzedScriptService.get_scripts_by_status(
                db=db,
                status=status_filter,
                skip=skip,
                limit=limit
            )
            total_count = AnalyzedScriptService.get_scripts_count(db, status_filter)
        else:
            scripts = AnalyzedScriptService.get_all_analyzed_scripts(
                db=db, 
                skip=skip, 
                limit=limit, 
                order_by=order_by,
                order_direction=order_direction
            )
            total_count = AnalyzedScriptService.get_scripts_count(db)
        
        return {
            "success": True,
            "data": [script.to_summary_dict() for script in scripts],
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "returned": len(scripts),
                "has_more": (skip + len(scripts)) < total_count
            },
            "search_term": search
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve scripts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scripts: {str(e)}")

# Read analyzed script from DB by ID
@app.get("/analyzed-scripts/{script_id}", response_model=DatabaseScriptResponse)
async def get_analyzed_script(
    script_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analyzed script by ID"""
    
    try:
        script = AnalyzedScriptService.get_analyzed_script_by_id(db, script_id)
        
        if not script:
            raise HTTPException(status_code=404, detail="Analyzed script not found")
        
        return {
            "success": True,
            "data": script.to_dict(),
            "message": "Script retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve script {script_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve script: {str(e)}")

# Delete analyzed script from DB by ID
@app.delete("/analyzed-scripts/{script_id}", response_model=DatabaseScriptResponse)
async def delete_analyzed_script(
    script_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analyzed script by ID"""
    
    try:
        deleted = AnalyzedScriptService.delete_analyzed_script(db, script_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Analyzed script not found")
        
        return {
            "success": True,
            "message": f"Analyzed script {script_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete script {script_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete script: {str(e)}")
    
# ---To activate human in the loop---
# @app.get("/pending-reviews")
# async def get_pending_reviews(db: Session = Depends(get_db)):
#     """Get all analyses pending human review"""
#     try:
#         scripts = db.query(AnalyzedScript).filter(
#             AnalyzedScript.status == "pending_review"
#         ).order_by(desc(AnalyzedScript.created_at)).all()
        
#         return {
#             "success": True,
#             "data": [script.to_summary_dict() for script in scripts],
#             "count": len(scripts)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/review/{analysis_id}")
# async def get_analysis_for_review(analysis_id: str, db: Session = Depends(get_db)):
#     """Get specific analysis for human review"""
#     try:
#         script = AnalyzedScriptService.get_analyzed_script_by_id(db, analysis_id)
#         if not script:
#             raise HTTPException(status_code=404, detail="Analysis not found")
        
#         return {
#             "success": True,
#             "data": script.to_dict(),
#             "status": script.status
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/review/{analysis_id}/feedback")
# async def submit_feedback(
#     analysis_id: str, 
#     feedback: HumanFeedback,
#     db: Session = Depends(get_db)
# ):
#     """Submit human feedback and resume workflow"""
#     try:
#         # Get the script
#         script = AnalyzedScriptService.get_analyzed_script_by_id(db, analysis_id)
#         if not script:
#             raise HTTPException(status_code=404, detail="Analysis not found")
        
#         # Update script with feedback
#         script.status = "completed_with_feedback" if feedback.approved else "needs_revision"
        
#         # Store feedback in the database (add to existing analysis_data)
#         if script.script_data:
#             script.script_data["human_feedback"] = {
#                 "feedback_text": feedback.feedback_text,
#                 "approved": feedback.approved,
#                 "corrections": feedback.corrections,
#                 "reviewed_at": datetime.now().isoformat()
#             }
        
#         db.commit()
        
#         return {
#             "success": True,
#             "message": "Feedback submitted successfully",
#             "analysis_id": analysis_id,
#             "status": script.status
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/analyze-script", response_model=AnalyzeScriptResponse)
# async def analyze_script(
#     file: UploadFile = File(...),
#     enable_human_review: bool = Query(False, description="Enable human review step")  # ✅ ADD THIS
# ):
#     """
#     Analyze a script PDF file with optional human review step
#     """
    
#     # Validate file
#     validator = FileValidator()
#     validator.validate_file(file)
    
#     temp_file_path = None
#     file_size = 0
    
#     try:
#         # Create temporary file
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
#             content = await file.read()
#             file_size = validator.validate_file_size(content)
#             temp_file.write(content)
#             temp_file_path = temp_file.name
        
#         start_time = time.time()
#         logger.info(f"Starting analysis for {file.filename} ({file_size} bytes) - HITL: {enable_human_review}")
        
#         # Perform analysis with timeout
#         try:
#             result = await asyncio.wait_for(
#                 run_optimized_script_analysis(temp_file_path),
#                 timeout=300.0
#             )
#         except asyncio.TimeoutError:
#             raise HTTPException(
#                 status_code=408,
#                 detail="Analysis timed out. Please try with a smaller script."
#             )
        
#         processing_time = time.time() - start_time
#         logger.info(f"Analysis completed in {processing_time:.2f} seconds")
        
#         # ✅ Extract comprehensive_analysis correctly
#         comprehensive_analysis = result.get('comprehensive_analysis')
        
#         if not comprehensive_analysis:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Analysis completed but no comprehensive analysis data found"
#             )
        
#         # ✅ Convert to dict if it's a Pydantic object
#         if hasattr(comprehensive_analysis, 'model_dump'):
#             analysis_data = comprehensive_analysis.model_dump()
#         elif hasattr(comprehensive_analysis, 'dict'):
#             analysis_data = comprehensive_analysis.dict()
#         else:
#             analysis_data = comprehensive_analysis
        
#         # Validate analysis result
#         try:
#             from agents.states.states import ComprehensiveAnalysis
#             temp_analysis = ComprehensiveAnalysis(**analysis_data)
#             logger.info("✅ Analysis validation passed")
#         except Exception as validation_error:
#             logger.warning(f"Analysis validation warning: {validation_error}")
        
#         # Enhanced metadata
#         enhanced_metadata = {
#             "filename": file.filename,
#             "original_filename": file.filename,
#             "file_size_bytes": file_size,
#             "processing_time_seconds": round(processing_time, 2),
#             "timestamp": datetime.now().isoformat(),
#             "api_calls_used": result.get('api_calls_used', 2),
#             "human_review_enabled": enable_human_review  # ✅ ADD THIS
#         }
        
#         # ✅ Pre-built save request object
#         save_request_data = {
#             "filename": file.filename,
#             "original_filename": file.filename,
#             "file_size_bytes": file_size,
#             "analysis_data": analysis_data,
#             "processing_time_seconds": round(processing_time, 2),
#             "api_calls_used": result.get('api_calls_used', 2)
#         }
        
#         # ✅ NEW: Handle HITL workflow
#         if enable_human_review:
#             # Save analysis with "pending_review" status for human review
#             try:
#                 saved_script = AnalyzedScriptService.create_analyzed_script(
#                     db=next(get_db()),  # Get DB session
#                     filename=file.filename,
#                     original_filename=file.filename,
#                     file_size_bytes=file_size,
#                     analysis_data=analysis_data,
#                     processing_time=round(processing_time, 2),
#                     api_calls_used=result.get('api_calls_used', 2)
#                 )
                
#                 # Update status to pending review
#                 db_session = next(get_db())
#                 try:
#                     saved_script.status = "pending_review"
#                     db_session.commit()
#                     analysis_id = saved_script.id
#                     logger.info(f"✅ Analysis saved for human review: {analysis_id}")
#                 finally:
#                     db_session.close()
                
#                 # ✅ HITL Response
#                 response_data = {
#                     "success": True,
#                     "message": "Script analysis completed successfully. Pending human review.",
                    
#                     # Optimization info
#                     "optimization_info": {
#                         "actual_calls_used": result.get('api_calls_used', 2),
#                         "expected_calls": 2
#                     },
                    
#                     # Enhanced metadata
#                     "metadata": enhanced_metadata,
                    
#                     # Analysis data
#                     "data": analysis_data,
#                     "analysis_data": analysis_data,
                    
#                     # Save request (for reference)
#                     "save_request": save_request_data,
                    
#                     # ✅ HITL-specific fields
#                     "human_review_required": True,
#                     "analysis_id": analysis_id,
#                     "status": "pending_review",
#                     "next_steps": {
#                         "review_url": f"/review/{analysis_id}",
#                         "pending_reviews_url": "/pending-reviews",
#                         "submit_feedback_url": f"/review/{analysis_id}/feedback"
#                     },
#                     "instructions": "Analysis is saved and awaiting human review. Use the review endpoints to provide feedback."
#                 }
                
#             except Exception as save_error:
#                 logger.error(f"Failed to save for review: {save_error}")
#                 # Fall back to regular response if save fails
#                 response_data = {
#                     "success": True,
#                     "message": "Analysis completed but failed to save for review. Returning direct results.",
#                     "optimization_info": {
#                         "actual_calls_used": result.get('api_calls_used', 2),
#                         "expected_calls": 2
#                     },
#                     "metadata": enhanced_metadata,
#                     "data": analysis_data,
#                     "analysis_data": analysis_data,
#                     "save_request": save_request_data,
#                     "human_review_required": False,
#                     "save_error": str(save_error)
#                 }
        
#         else:
#             # ✅ Original behavior - direct response without HITL
#             response_data = {
#                 "success": True,
#                 "message": "Script analysis completed successfully",
                
#                 # Optimization info
#                 "optimization_info": {
#                     "actual_calls_used": result.get('api_calls_used', 2),
#                     "expected_calls": 2
#                 },
                
#                 # Enhanced metadata
#                 "metadata": enhanced_metadata,
                
#                 # Analysis data
#                 "data": analysis_data,
#                 "analysis_data": analysis_data,
                
#                 # Save request
#                 "save_request": save_request_data,
                
#                 # ✅ No HITL fields
#                 "human_review_required": False,
#                 "instructions": "Analysis completed. Use /save-analysis endpoint to save to database if needed."
#             }
        
#         logger.info(f"✅ Analysis completed - HITL: {enable_human_review}")
#         return JSONResponse(status_code=200, content=response_data)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Analysis failed: {str(e)}")
#         error_message = str(e)
        
#         if "extract" in error_message.lower():
#             raise HTTPException(status_code=422, detail=f"PDF extraction failed: {error_message}")
#         elif "validation" in error_message.lower():
#             raise HTTPException(status_code=422, detail=f"Script validation failed: {error_message}")
#         elif "analysis" in error_message.lower():
#             raise HTTPException(status_code=500, detail=f"Analysis failed: {error_message}")
#         else:
#             raise HTTPException(status_code=500, detail=f"Unexpected error: {error_message}")
    
#     finally:
#         # Clean up temporary file
#         if temp_file_path and os.path.exists(temp_file_path):
#             try:
#                 os.unlink(temp_file_path)
#             except Exception as cleanup_error:
#                 logger.warning(f"Failed to cleanup temp file: {cleanup_error}")