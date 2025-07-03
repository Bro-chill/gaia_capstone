from fastapi import FastAPI, HTTPException, UploadFile, Depends, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from dotenv import load_dotenv
from datetime import datetime
import os
import tempfile
import time
import asyncio
import logging

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
    AnalysisValidator
)
from .middleware import setup_middleware

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Script Analysis API",
    version="2.0.0",
    description="Comprehensive film script analysis with AI-powered insights"
)

setup_middleware(app)

# Main_route
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Script Analysis API v2.0 is running",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "AI-powered script analysis",
            "Database storage with search",
            "Cost and production breakdowns",
            "RESTful API with validation",
            "Comprehensive error handling"
        ]
    }

# Health_Endpoint
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
        "version": "2.0.0"
    }

# Main analysis + database saving(postgresql)
@app.post("/analyze-script", response_model=AnalyzeScriptResponse)
async def analyze_script(
    file: UploadFile = File(...),
    save_to_db: bool = Query(True, description="Save analysis to database"),
    db: Session = Depends(get_db)
):
    """
    Analyze a script PDF file with integrated database saving
    
    This endpoint:
    1. Validates the uploaded file
    2. Performs AI analysis
    3. Optionally saves to database
    4. Returns comprehensive results
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
        logger.info(f"Starting analysis for {file.filename} ({file_size} bytes)")
        
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
        
        # Serialize result
        serializer = ResultSerializer()
        clean_result = serializer.serialize(result)
        
        # Validate analysis result
        if 'data' in clean_result:
            try:
                AnalysisValidator.validate_comprehensive_analysis(clean_result['data'])
            except Exception as validation_error:
                logger.warning(f"Analysis validation warning: {validation_error}")
        
        # Prepare response data
        response_data = {
            "success": True,
            "message": "Script analysis completed successfully",
            "optimization_info": {
                "actual_calls_used": result.get('api_calls_used', 2),
                "expected_calls": 2
            },
            "metadata": {
                "filename": file.filename,
                "file_size_bytes": file_size,
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
                "api_calls_used": result.get('api_calls_used', 2)
            },
            "data": clean_result.get('data', clean_result)
        }
        
        # Database saving
        if save_to_db:
            try:
                saved_script = AnalyzedScriptService.create_analyzed_script(
                    db=db,
                    filename=file.filename,
                    original_filename=file.filename,
                    file_size_bytes=file_size,
                    analysis_data=clean_result,
                    processing_time=processing_time,
                    api_calls_used=result.get('api_calls_used', 2)
                )
                response_data["database_id"] = saved_script.id
                logger.info(f"Analysis saved to database with ID: {saved_script.id}")
                
            except Exception as db_error:
                logger.error(f"Database save failed: {str(db_error)}")
                response_data["database_error"] = str(db_error)
                # Don't fail the entire request for database errors
        
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

# Read all analyzed-scripts
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
            total_count = len(scripts)  # For search, we get limited results
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

# Read analyzed script by ID
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

# Delete analyzed-script by ID
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