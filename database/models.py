from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class AnalyzedScript(Base):
    __tablename__ = "analyzed_scripts"
    
    # Primary key and basic info
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False, index=True)  # Added index for searches
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    
    # Analysis results (stored as JSON)
    script_data = Column(JSON, nullable=True)
    cast_breakdown = Column(JSON, nullable=True)
    cost_breakdown = Column(JSON, nullable=True)
    location_breakdown = Column(JSON, nullable=True)
    props_breakdown = Column(JSON, nullable=True)
    
    # Processing metadata
    processing_time_seconds = Column(Float, nullable=True)
    api_calls_used = Column(Integer, default=2)
    status = Column(String(50), default="completed", index=True)  # Valid statuses: "completed", "error", "pending_review", "completed_with_feedback", "needs_revision"
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Analysis metadata
    total_scenes = Column(Integer, nullable=True)
    total_characters = Column(Integer, nullable=True)
    total_locations = Column(Integer, nullable=True)
    estimated_budget = Column(Float, nullable=True)
    budget_category = Column(String(20), nullable=True)
    
    # FIXED: Correct timestamp handling
    created_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True  # Added index for sorting
    )
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "script_data": self.script_data,
            "cast_breakdown": self.cast_breakdown,
            "cost_breakdown": self.cost_breakdown,
            "location_breakdown": self.location_breakdown,
            "props_breakdown": self.props_breakdown,
            "processing_time_seconds": self.processing_time_seconds,
            "api_calls_used": self.api_calls_used,
            "status": self.status,
            "error_message": self.error_message,
            "total_scenes": self.total_scenes,
            "total_characters": self.total_characters,
            "total_locations": self.total_locations,
            "estimated_budget": self.estimated_budget,
            "budget_category": self.budget_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_summary_dict(self):
        """Convert to summary dictionary for list views"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "total_scenes": self.total_scenes,
            "estimated_budget": self.estimated_budget,
            "budget_category": self.budget_category,
            "processing_time_seconds": self.processing_time_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<AnalyzedScript(id={self.id}, filename={self.filename}, status={self.status})>"