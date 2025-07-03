from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# Individual component models (unchanged)
class SceneData(BaseModel):
    scene_number: int = Field(description='Scene sequence number')
    scene_header: str = Field(description='Scene header/title')
    time_of_day: str = Field(description='Scene time (Day/Night/Dawn/Dusk)')
    scene_type: str = Field(description='Interior or Exterior (INT/EXT)')
    characters_present: List[str] = Field(default=[], description='Characters in specific scene')
    props_mentioned: List[str] = Field(default=[], description='Props explicitly mentioned')
    location: str = Field(description='Location name')
    dialogue_lines: List[str] = Field(default=[], description='Dialogue by character')
    action_lines: List[str] = Field(default=[], description='Action description lines')
    estimated_pages: int = Field(default=1, description='Estimated page count')
    special_requirements: List[str] = Field(default=[], description='SFX, stunts or technical requirements')

class ScriptData(BaseModel):
    scenes: List[SceneData] = Field(default=[], description='List of all scenes with detailed data')
    total_characters: List[str] = Field(default=[], description='All characters across script')
    total_locations: List[str] = Field(default=[], description='All locations across script')
    total_pages: int = Field(default=0, description='Total script pages')
    total_words: int = Field(default=0, description='Total script words')
    languages: List[str] = Field(default=["English"], description='Script languages')

class SceneCastBreakdown(BaseModel):
    scene_number: int = Field(description='Scene number')
    characters_in_scene: List[str] = Field(default=[], description='Characters present in this scene')
    character_interactions: List[str] = Field(default=[], description='Key character interactions/relationships shown')
    dialogue_complexity: str = Field(default="Simple", description='Simple/Moderate/Complex dialogue requirements')
    emotional_beats: List[str] = Field(default=[], description='Emotional moments for characters in scene')

class CastBreakdown(BaseModel):
    scene_characters: List[SceneCastBreakdown] = Field(default=[], description='Character breakdown per scene')
    main_characters: List[str] = Field(default=[], description='Main characters with descriptions')
    supporting_characters: List[str] = Field(default=[], description='Supporting characters')
    character_scene_count: List[str] = Field(default=[], description='Character scene count as strings')
    casting_requirements: List[str] = Field(default=[], description='Casting specifications for each character')

class SceneCostBreakdown(BaseModel):
    scene_number: int = Field(description='Scene number')
    cast_cost: float = Field(default=0.0, description='Total cost for cast in this scene')
    location_cost: float = Field(default=0.0, description='Cost for location rent/permit')
    props_cost: float = Field(default=0.0, description='Cost for props')
    wardrobe_cost: float = Field(default=0.0, description='Cost for wardrobe')
    crew_cost: float = Field(default=0.0, description='Cost for crew')
    equipment_cost: float = Field(default=0.0, description='Cost for equipment rental')
    total_scene_cost: float = Field(default=0.0, description='Total cost for this scene')

class CostBreakdown(BaseModel):
    scene_costs: List[SceneCostBreakdown] = Field(default=[], description='Cost breakdown per scene')
    total_costs: float = Field(default=0.0, description='Total production cost')
    total_cast_costs: float = Field(default=0.0, description='Total cost for cast')
    total_location_costs: float = Field(default=0.0, description='Total cost for locations')
    total_props_costs: float = Field(default=0.0, description='Total cost for props')
    total_wardrobe_costs: float = Field(default=0.0, description='Total cost for wardrobe')
    total_crew_costs: float = Field(default=0.0, description='Total cost for crew')
    total_equipment_costs: float = Field(default=0.0, description='Total cost for equipment')
    budget_category: str = Field(default="Medium", description='Low/Medium/High budget category')

class SceneLocationBreakdown(BaseModel):
    scene_number: int = Field(description='Scene number')
    location_name: str = Field(description='Location name')
    location_type: str = Field(description='INT/EXT and specific type')
    time_of_day: str = Field(description='Time requirements')
    setup_complexity: str = Field(default="Simple", description='Simple/Moderate/Complex setup')
    permit_needed: bool = Field(default=False, description='Whether permits are required')
    estimated_setup_time: int = Field(default=60, description='Setup time in minutes')
    accessibility: str = Field(default="Good", description='Location accessibility rating')

class LocationBreakdown(BaseModel):
    scene_locations: List[SceneLocationBreakdown] = Field(default=[], description='Location breakdown per scene')
    unique_locations: List[str] = Field(default=[], description='All unique locations needed')
    locations_by_type: List[str] = Field(default=[], description='Locations grouped by type as strings')
    location_shooting_groups: List[str] = Field(default=[], description='Recommended shooting groups by location')
    permit_requirements: List[str] = Field(default=[], description='Permit needs by location')
    total_location_days: int = Field(default=0, description='Total shooting days needed')

class ScenePropsBreakdown(BaseModel):
    scene_number: int = Field(description='Scene number')
    props_needed: List[str] = Field(default=[], description='All props needed in this scene')
    costume_requirements: List[str] = Field(default=[], description='Costumes for characters in this scene')
    set_decoration: List[str] = Field(default=[], description='Set decoration items needed')
    prop_complexity: str = Field(default="Simple", description='Simple/Moderate/Complex prop requirements')
    special_effects_props: List[str] = Field(default=[], description='Props requiring special effects')

class PropsBreakdown(BaseModel):
    scene_props: List[ScenePropsBreakdown] = Field(default=[], description='Props breakdown per scene')
    master_props_list: List[str] = Field(default=[], description='Complete props list across all scenes')
    props_by_category: List[str] = Field(default=[], description='Props organized by category as strings')
    costume_by_character: List[str] = Field(default=[], description='Costume requirements as strings')
    prop_budget_estimate: str = Field(default="Medium", description='Low/Medium/High props budget category')
    rental_vs_purchase: List[str] = Field(default=[], description='Rental vs purchase recommendations as strings')

# NEW: Comprehensive analysis output
class ComprehensiveAnalysis(BaseModel):
    script_data: ScriptData = Field(description='Complete script breakdown')
    cast_breakdown: CastBreakdown = Field(description='Cast analysis and requirements')
    cost_breakdown: CostBreakdown = Field(description='Budget analysis and estimates')
    location_breakdown: LocationBreakdown = Field(description='Location requirements and logistics')
    props_breakdown: PropsBreakdown = Field(description='Props, costumes, and set decoration')