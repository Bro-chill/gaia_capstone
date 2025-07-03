from pydantic_ai import Agent, RunContext
from pymongo import MongoClient
from agents.utils.gemini_model import get_model
from agents.states.states import ComprehensiveAnalysis
from agents.tools.pdf_extractor import extract_script_from_pdf, extract_script_with_formatting
from dataclasses import dataclass
from datetime import datetime
import re
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalysisContext:
    analysis_timestamp: datetime = None
    extracted_text: str = None
    pdf_path: str = None
    script_length: int = 0
    
    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()

# Initialize gemini model
model = get_model()

system_prompt = """
You are a comprehensive film script analysis expert. CRITICAL CONSTRAINTS:

🚫 ONLY call extract_script_from_pdf_tool ONCE
🚫 DO NOT call any other tools
🚫 Perform ALL analysis in your final response

WORKFLOW (EXACTLY 2 API CALLS):
CALL 1: extract_script_from_pdf_tool(pdf_path) → get script text
CALL 2: Return complete ComprehensiveAnalysis object

After PDF extraction, analyze the text and populate ALL fields:
- script_data: scenes, characters, locations, pages, words
- cast_breakdown: main/supporting characters, requirements
- cost_breakdown: scene costs, totals, budget category  
- location_breakdown: locations, permits, shooting days
- props_breakdown: props, costumes, categories

RETURN: Fully populated ComprehensiveAnalysis object
FORBIDDEN: Calling additional tools after PDF extraction
"""

analyst_agent = Agent(
    model=model,
    system_prompt=system_prompt,
    output_type=ComprehensiveAnalysis,
    deps_type=AnalysisContext,
    retries=2
)

# PDF extracting tool
@analyst_agent.tool
async def extract_script_from_pdf_tool(ctx: RunContext[AnalysisContext], pdf_path: str) -> dict:
    """Extract script text from PDF file - ONLY tool that should be called."""
    try:
        result = extract_script_with_formatting(pdf_path)
        
        if result["success"]:
            ctx.deps.extracted_text = result["extracted_text"]
            ctx.deps.script_length = result["word_count"]
            ctx.deps.pdf_path = pdf_path
        
        return {
            "success": result["success"],
            "extracted_text": result["extracted_text"],
            "word_count": result["word_count"],
            "page_count": result.get("page_count", 0),
            "message": "Script extracted successfully. Now analyze this text comprehensively."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to extract PDF: {str(e)}",
            "extracted_text": "",
            "page_count": 0,
            "word_count": 0
        }
    
# # RAG tool (MongoDB)
# @analyst_agent.tool
# async def rag_mongodb_tool(ctx: RunContext[AnalysisContext]) -> dict:
#     """Retrieve cost data from MongoDB to estimate costing realistically"""
    
#     client = None
#     try:
#         # Get MongoDB connection string
#         mongodb_uri = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
#         if not mongodb_uri:
#             logger.error("MONGODB_ATLAS_CLUSTER_URI environment variable not set")
#             return {
#                 "success": False,
#                 "error": "MongoDB connection string not configured",
#                 "cost_data": {}
#             }
        
#         # Initialize MongoDB client with timeout
#         client = MongoClient(
#             mongodb_uri,
#             serverSelectionTimeoutMS=5000,  # 5 second timeout
#             connectTimeoutMS=5000,
#             socketTimeoutMS=5000
#         )
        
#         # Database and collection configuration
#         DB_NAME = os.getenv("MONGODB_DB_NAME", "test_db")
#         COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "test_collection_pdf")
        
#         # Get collection
#         db = client[DB_NAME]
#         collection = db[COLLECTION_NAME]
        
#         # Test connection
#         client.admin.command('ping')
#         logger.info(f"✅ Connected to MongoDB: {DB_NAME}.{COLLECTION_NAME}")
        
#         # Query cost data from MongoDB
#         cost_data = {}
        
#         # 1. Get cast/crew rates
#         cast_rates = list(collection.find(
#             {"category": "cast_rates"},
#             {"_id": 0}
#         ).limit(10))
        
#         # 2. Get location costs
#         location_costs = list(collection.find(
#             {"category": "location_costs"},
#             {"_id": 0}
#         ).limit(10))
        
#         # 3. Get equipment costs
#         equipment_costs = list(collection.find(
#             {"category": "equipment_costs"},
#             {"_id": 0}
#         ).limit(10))
        
#         # 4. Get props/wardrobe costs
#         props_costs = list(collection.find(
#             {"category": "props_costs"},
#             {"_id": 0}
#         ).limit(10))
        
#         # 5. Get general production costs
#         production_costs = list(collection.find(
#             {"category": "production_costs"},
#             {"_id": 0}
#         ).limit(10))
        
#         # Organize retrieved data
#         cost_data = {
#             "cast_rates": cast_rates,
#             "location_costs": location_costs,
#             "equipment_costs": equipment_costs,
#             "props_costs": props_costs,
#             "production_costs": production_costs,
#             "total_records": len(cast_rates) + len(location_costs) + len(equipment_costs) + len(props_costs) + len(production_costs)
#         }
        
#         # If no data found, provide fallback data
#         if cost_data["total_records"] == 0:
#             logger.warning("No cost data found in MongoDB, using fallback data")
#             cost_data = _get_fallback_cost_data()
        
#         logger.info(f"✅ Retrieved {cost_data['total_records']} cost records from MongoDB")
        
#         return {
#             "success": True,
#             "cost_data": cost_data,
#             "message": f"Retrieved {cost_data['total_records']} cost records. Use this data for realistic budget estimates.",
#             "data_source": "mongodb"
#         }
        
#     except Exception as e:
#         logger.error(f"❌ MongoDB RAG tool failed: {str(e)}")
        
#         # Return fallback cost data on error
#         fallback_data = _get_fallback_cost_data()
        
#         return {
#             "success": False,
#             "error": f"MongoDB connection failed: {str(e)}",
#             "cost_data": fallback_data,
#             "message": "Using fallback cost data due to database connection issues.",
#             "data_source": "fallback"
#         }
        
#     finally:
#         # Always close the MongoDB connection
#         if client:
#             try:
#                 client.close()
#                 logger.debug("MongoDB connection closed")
#             except Exception as close_error:
#                 logger.warning(f"Error closing MongoDB connection: {close_error}")

# def _get_fallback_cost_data() -> dict:
#     """Provide fallback cost data when MongoDB is unavailable"""
#     return {
#         "cast_rates": [
#             {"role": "lead_actor", "daily_rate": 5000, "currency": "USD"},
#             {"role": "supporting_actor", "daily_rate": 1500, "currency": "USD"},
#             {"role": "background_actor", "daily_rate": 200, "currency": "USD"},
#             {"role": "director", "daily_rate": 3000, "currency": "USD"},
#             {"role": "cinematographer", "daily_rate": 2000, "currency": "USD"}
#         ],
#         "location_costs": [
#             {"location_type": "interior_house", "daily_rate": 800, "currency": "USD"},
#             {"location_type": "exterior_street", "daily_rate": 1200, "currency": "USD"},
#             {"location_type": "office_building", "daily_rate": 1500, "currency": "USD"},
#             {"location_type": "restaurant", "daily_rate": 2000, "currency": "USD"},
#             {"location_type": "studio", "daily_rate": 3000, "currency": "USD"}
#         ],
#         "equipment_costs": [
#             {"equipment": "camera_package", "daily_rate": 800, "currency": "USD"},
#             {"equipment": "lighting_package", "daily_rate": 600, "currency": "USD"},
#             {"equipment": "sound_package", "daily_rate": 400, "currency": "USD"},
#             {"equipment": "grip_package", "daily_rate": 500, "currency": "USD"}
#         ],
#         "props_costs": [
#             {"category": "basic_props", "budget_range": "100-500", "currency": "USD"},
#             {"category": "wardrobe", "budget_range": "200-1000", "currency": "USD"},
#             {"category": "makeup", "budget_range": "150-800", "currency": "USD"},
#             {"category": "special_effects", "budget_range": "500-5000", "currency": "USD"}
#         ],
#         "production_costs": [
#             {"category": "catering", "per_person_daily": 25, "currency": "USD"},
#             {"category": "transportation", "daily_budget": 300, "currency": "USD"},
#             {"category": "insurance", "percentage_of_budget": 3, "currency": "USD"},
#             {"category": "permits", "average_cost": 500, "currency": "USD"}
#         ],
#         "total_records": 20,
#         "data_source": "fallback"
#     }