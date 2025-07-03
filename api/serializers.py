import logging
from typing import Any, Dict, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseCompatibleSerializer:
    """Serializer optimized for both API responses and database storage"""
    
    def serialize_for_api(self, result: Any) -> Dict[str, Any]:
        """Serialize result for API response"""
        try:
            logger.info(f"🔧 Serializing for API: {type(result)}")
            
            if hasattr(result, 'keys') and hasattr(result, '__getitem__'):
                return self._serialize_dict_like(result)
            elif isinstance(result, dict):
                return self._convert_to_serializable(result)
            else:
                return self._convert_to_serializable(result)
                
        except Exception as e:
            logger.error(f"❌ API serialization error: {e}")
            return self._fallback_serialization(result)
    
    def serialize_for_database(self, result: Any) -> Dict[str, Any]:
        """Serialize result for database storage"""
        try:
            logger.info(f"🗄️ Serializing for database: {type(result)}")
            
            # Extract comprehensive analysis
            if hasattr(result, 'keys'):
                comprehensive_analysis = result.get('comprehensive_analysis')
                if comprehensive_analysis:
                    return self._serialize_comprehensive_analysis(comprehensive_analysis)
            
            return self._convert_to_serializable(result)
            
        except Exception as e:
            logger.error(f"❌ Database serialization error: {e}")
            return {}
    
    def _serialize_dict_like(self, result: Any) -> Dict[str, Any]:
        """Serialize dict-like objects"""
        serialized = {}
        
        # Handle comprehensive analysis specially
        comprehensive_analysis = result.get('comprehensive_analysis')
        if comprehensive_analysis:
            serialized['comprehensive_analysis'] = self._serialize_comprehensive_analysis(comprehensive_analysis)
        
        # Handle other fields
        for key in result.keys():
            if key != 'comprehensive_analysis':
                try:
                    serialized[key] = self._convert_to_serializable(result[key])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to serialize {key}: {e}")
                    serialized[key] = str(result[key])
        
        return serialized
    
    def _serialize_comprehensive_analysis(self, analysis: Any) -> Dict[str, Any]:
        """Serialize comprehensive analysis object with enhanced error handling"""
        
        if hasattr(analysis, 'model_dump'):
            try:
                return analysis.model_dump()
            except Exception as e:
                logger.warning(f"model_dump failed: {e}, trying dict()")
                try:
                    return analysis.dict()
                except Exception as e2:
                    logger.warning(f"dict() failed: {e2}, using manual extraction")
        
        # Manual serialization with error handling
        result = {}
        
        # Script data
        try:
            if hasattr(analysis, 'script_data'):
                result['script_data'] = self._serialize_component(analysis.script_data, 'script_data')
        except Exception as e:
            logger.warning(f"Failed to serialize script_data: {e}")
            result['script_data'] = {}
        
        # Cast breakdown
        try:
            if hasattr(analysis, 'cast_breakdown'):
                result['cast_breakdown'] = self._serialize_component(analysis.cast_breakdown, 'cast_breakdown')
        except Exception as e:
            logger.warning(f"Failed to serialize cast_breakdown: {e}")
            result['cast_breakdown'] = {}
        
        # Cost breakdown
        try:
            if hasattr(analysis, 'cost_breakdown'):
                result['cost_breakdown'] = self._serialize_component(analysis.cost_breakdown, 'cost_breakdown')
        except Exception as e:
            logger.warning(f"Failed to serialize cost_breakdown: {e}")
            result['cost_breakdown'] = {}
        
        # Location breakdown
        try:
            if hasattr(analysis, 'location_breakdown'):
                result['location_breakdown'] = self._serialize_component(analysis.location_breakdown, 'location_breakdown')
        except Exception as e:
            logger.warning(f"Failed to serialize location_breakdown: {e}")
            result['location_breakdown'] = {}
        
        # Props breakdown
        try:
            if hasattr(analysis, 'props_breakdown'):
                result['props_breakdown'] = self._serialize_component(analysis.props_breakdown, 'props_breakdown')
        except Exception as e:
            logger.warning(f"Failed to serialize props_breakdown: {e}")
            result['props_breakdown'] = {}
        
        return result
    
    def _serialize_component(self, component: Any, component_name: str) -> Dict[str, Any]:
        """Serialize individual analysis component"""
        
        if hasattr(component, 'model_dump'):
            return component.model_dump()
        elif hasattr(component, 'dict'):
            return component.dict()
        elif isinstance(component, dict):
            return component
        elif hasattr(component, '__dict__'):
            return self._convert_to_serializable(component.__dict__)
        else:
            logger.warning(f"Unknown component format for {component_name}: {type(component)}")
            return {}
    
    def _convert_to_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON serializable format with enhanced handling"""
        try:
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, dict):
                return {k: self._convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [self._convert_to_serializable(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return {k: self._convert_to_serializable(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            else:
                return str(obj)
                
        except Exception as e:
            logger.warning(f"⚠️ Conversion error for {type(obj)}: {e}")
            return str(obj)
    
    def _fallback_serialization(self, result: Any) -> Dict[str, Any]:
        """Enhanced fallback serialization for edge cases"""
        fallback_result = {
            "serialization_error": True,
            "original_type": str(type(result)),
            "data": {}
        }
        
        if hasattr(result, 'keys'):
            for key in result.keys():
                try:
                    value = result[key]
                    fallback_result["data"][key] = self._convert_to_serializable(value)
                except Exception as field_error:
                    logger.warning(f"⚠️ Failed to serialize field {key}: {field_error}")
                    fallback_result["data"][key] = f"Serialization failed: {str(field_error)}"
        else:
            fallback_result["data"] = str(result)
        
        return fallback_result

# Update the main ResultSerializer to use enhanced version
class ResultSerializer(DatabaseCompatibleSerializer):
    """Main result serializer with database compatibility"""
    
    def serialize(self, result: Any) -> Dict[str, Any]:
        """Main serialization method for API responses"""
        return self.serialize_for_api(result)
    
    def serialize_for_storage(self, result: Any) -> Dict[str, Any]:
        """Serialization method for database storage"""
        return self.serialize_for_database(result)