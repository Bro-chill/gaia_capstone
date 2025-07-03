from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from agents.states.states import ComprehensiveAnalysis
from datetime import datetime

class FileValidator:
    """Validate uploaded files"""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.min_file_size = 1024  # 1KB
        self.allowed_extensions = ['.pdf']
    
    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file extension
        if not any(file.filename.lower().endswith(ext) for ext in self.allowed_extensions):
            raise HTTPException(
                status_code=400, 
                detail=f"Only {', '.join(self.allowed_extensions)} files are supported"
            )
    
    def validate_file_size(self, content: bytes) -> int:
        """Validate file size after reading content"""
        file_size = len(content)
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.max_file_size // (1024*1024)}MB"
            )
        
        if file_size < self.min_file_size:
            raise HTTPException(
                status_code=400,
                detail="File too small. Please provide a valid PDF script"
            )
        
        return file_size

# NEW: Request models for save endpoint
class SaveAnalysisRequest(BaseModel):
    """Request model for saving analysis to database"""
    filename: str = Field(description="Original filename")
    original_filename: Optional[str] = Field(None, description="Original filename if different")
    file_size_bytes: int = Field(description="File size in bytes", gt=0)
    analysis_data: Dict[str, Any] = Field(description="Complete analysis results as dict")  # ✅ CHANGED
    processing_time_seconds: Optional[float] = Field(None, description="Processing time", ge=0)
    api_calls_used: int = Field(default=2, description="Number of API calls used", ge=1)
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip()
    
    @field_validator('file_size_bytes')
    @classmethod
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('File size must be positive')
        if v > 50 * 1024 * 1024:  # 50MB
            raise ValueError('File size too large')
        return v
    
    # ✅ NEW: Validate analysis_data structure
    @field_validator('analysis_data')
    @classmethod
    def validate_analysis_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Analysis data must be a dictionary')
        
        required_keys = ['script_data', 'cast_breakdown', 'cost_breakdown', 'location_breakdown', 'props_breakdown']
        missing_keys = [key for key in required_keys if key not in v]
        
        if missing_keys:
            raise ValueError(f'Analysis data missing required keys: {missing_keys}')
        
        return v

# NEW: Response models
class SaveAnalysisResponse(BaseModel):
    """Response model for save analysis endpoint"""
    success: bool = Field(description="Save operation success status")
    message: str = Field(description="Response message")
    database_id: str = Field(description="Database record ID")
    saved_at: str = Field(description="Timestamp when saved")
    metadata: Dict[str, Any] = Field(description="Saved record metadata")

# NEW: Proper Pydantic Models for API
class AnalysisMetadata(BaseModel):
    """Metadata for analysis response"""
    filename: str = Field(description="Original filename")
    file_size_bytes: int = Field(description="File size in bytes")
    processing_time_seconds: float = Field(description="Processing time")
    timestamp: str = Field(description="Analysis timestamp")
    api_calls_used: int = Field(default=2, description="Number of API calls used")

class OptimizationInfo(BaseModel):
    """Optimization information"""
    actual_calls_used: int = Field(description="Actual API calls used")
    expected_calls: int = Field(default=2, description="Expected API calls")

class AnalyzeScriptResponse(BaseModel):
    """Complete response model for script analysis"""
    success: bool = Field(description="Analysis success status")
    message: str = Field(description="Response message")
    optimization_info: OptimizationInfo = Field(description="API optimization details")
    metadata: AnalysisMetadata = Field(description="Analysis metadata")
    data: ComprehensiveAnalysis = Field(description="Complete analysis results")
    database_id: Optional[str] = Field(None, description="Database record ID if saved")
    database_error: Optional[str] = Field(None, description="Database error if occurred")

class DatabaseScriptResponse(BaseModel):
    """Response model for database operations"""
    success: bool = Field(description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Script data")
    message: Optional[str] = Field(None, description="Response message")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination info")
    search_term: Optional[str] = Field(None, description="Search term used")

class ScriptListResponse(BaseModel):
    """Response model for script list"""
    success: bool = Field(description="Operation success")
    data: List[Dict[str, Any]] = Field(description="List of scripts")
    pagination: Dict[str, Any] = Field(description="Pagination information")
    search_term: Optional[str] = Field(None, description="Search term if used")

# Validation Functions
class AnalysisValidator:
    """Validator for analysis results"""
    
    @staticmethod
    def validate_comprehensive_analysis(analysis: ComprehensiveAnalysis) -> None:
        """Validate comprehensive analysis structure"""
        
        # Validate script data
        if not analysis.script_data.scenes:
            raise ValueError("Script must contain at least one scene")
        
        # Validate scene numbers are sequential
        scene_numbers = [scene.scene_number for scene in analysis.script_data.scenes]
        expected_numbers = list(range(1, len(scene_numbers) + 1))
        if scene_numbers != expected_numbers:
            raise ValueError("Scene numbers must be sequential starting from 1")
        
        # Validate cost consistency
        scene_total = sum(scene.total_scene_cost for scene in analysis.cost_breakdown.scene_costs)
        if abs(analysis.cost_breakdown.total_costs - scene_total) > 0.01:
            raise ValueError("Total costs don't match sum of scene costs")
        
        # Validate budget category
        valid_categories = ["Low", "Medium", "High"]
        if analysis.cost_breakdown.budget_category not in valid_categories:
            raise ValueError(f"Budget category must be one of: {valid_categories}")
        
        # Validate location consistency
        scene_numbers_in_breakdown = {loc.scene_number for loc in analysis.location_breakdown.scene_locations}
        script_scene_numbers = {scene.scene_number for scene in analysis.script_data.scenes}
        if scene_numbers_in_breakdown != script_scene_numbers:
            raise ValueError("Location breakdown missing for some scenes")

# For manual human-in-the-loop
class HumanFeedback(BaseModel):
    feedback_text: str = Field(description="Human feedback on the analysis")
    approved: bool = Field(default=True, description="Whether analysis is approved")
    corrections: Optional[Dict[str, Any]] = Field(None, description="Specific corrections")