"""
Enterprise-grade plugin registry for prompting techniques
OpenAI-compatible architecture with versioning and metrics
"""

from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import json
from datetime import datetime
import importlib
import inspect

@dataclass
class PluginMetadata:
    """Comprehensive plugin metadata following OpenAI standards"""
    name: str
    version: str
    description: str
    author: str
    research_paper: Optional[str] = None
    arxiv_link: Optional[str] = None
    safety_rating: float = 1.0
    performance_tier: str = "experimental"  # experimental, beta, production
    supported_tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

class PromptingTechnique(ABC):
    """
    Base class for all prompting techniques
    Follows OpenAI's plugin architecture patterns
    """
    
    metadata: PluginMetadata
    
    @abstractmethod
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request using the prompting technique"""
        pass
    
    @abstractmethod
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate request format and content"""
        pass
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Return usage statistics for monitoring"""
        return {
            "total_requests": getattr(self, '_request_count', 0),
            "average_latency": getattr(self, '_avg_latency', 0.0),
            "success_rate": getattr(self, '_success_rate', 1.0),
            "last_used": getattr(self, '_last_used', None)
        }

class EnterprisePluginRegistry:
    """
    Enterprise-grade plugin registry with:
    - Automatic discovery
    - Version management  
    - Performance monitoring
    - Safety validation
    - Load balancing
    """
    
    def __init__(self):
        self.plugins: Dict[str, PromptingTechnique] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.usage_stats: Dict[str, Dict] = {}
        self.load_balancer = LoadBalancer()
        
    async def register_plugin(
        self, 
        plugin_class: Type[PromptingTechnique],
        metadata: PluginMetadata
    ) -> bool:
        """Register a new prompting technique plugin"""
        
        try:
            # Validate plugin implementation
            if not self._validate_plugin(plugin_class):
                return False
            
            # Safety check
            if metadata.safety_rating < 0.7:
                print(f"⚠ Plugin {metadata.name} has low safety rating: {metadata.safety_rating}")
                return False
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            plugin_instance.metadata = metadata
            
            # Register in system
            plugin_key = f"{metadata.name}:{metadata.version}"
            self.plugins[plugin_key] = plugin_instance
            self.plugin_metadata[plugin_key] = metadata
            self.usage_stats[plugin_key] = {}
            
            print(f"✅ Registered plugin: {plugin_key}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register plugin {metadata.name}: {e}")
            return False
    
    async def discover_plugins(self, plugin_directory: str = "src/research/techniques/prompting_plugins"):
        """Automatically discover and register plugins"""
        
        import os
        import glob
        
        plugin_files = glob.glob(f"{plugin_directory}/*.py")
        
        for plugin_file in plugin_files:
            if plugin_file.endswith("__init__.py") or plugin_file.endswith("registry.py"):
                continue
                
            try:
                # Import module
                module_name = os.path.basename(plugin_file)[:-3]
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, PromptingTechnique) and 
                        obj != PromptingTechnique):
                        
                        # Check for metadata
                        if hasattr(obj, 'METADATA'):
                            await self.register_plugin(obj, obj.METADATA)
                        else:
                            print(f"⚠ Plugin {name} missing metadata")
                            
            except Exception as e:
                print(f"❌ Error loading plugin from {plugin_file}: {e}")
    
    async def execute_technique(
        self, 
        technique_name: str, 
        request: Dict[str, Any],
        version: str = "latest"
    ) -> Dict[str, Any]:
        """Execute a prompting technique with monitoring"""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Find plugin
            plugin_key = self._resolve_plugin_key(technique_name, version)
            if plugin_key not in self.plugins:
                raise ValueError(f"Plugin not found: {technique_name}:{version}")
            
            plugin = self.plugins[plugin_key]
            
            # Validate request
            if not plugin.validate_request(request):
                raise ValueError("Invalid request format")
            
            # Load balancing
            if await self.load_balancer.should_throttle(plugin_key):
                raise RuntimeError("Plugin temporarily throttled due to high load")
            
            # Execute technique
            result = await plugin.process(request)
            
            # Record metrics
            end_time = asyncio.get_event_loop().time()
            await self._record_usage(plugin_key, end_time - start_time, True)
            
            return {
                **result,
                "technique_used": technique_name,
                "version": version,
                "execution_time": end_time - start_time,
                "api_version": "enterprise-v1.0"
            }
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            await self._record_usage(plugin_key, end_time - start_time, False)
            
            return {
                "error": str(e),
                "technique_used": technique_name,
                "version": version,
                "execution_time": end_time - start_time,
                "api_version": "enterprise-v1.0"
            }
    
    def list_available_techniques(self) -> List[Dict[str, Any]]:
        """List all available prompting techniques"""
        
        techniques = []
        for plugin_key, metadata in self.plugin_metadata.items():
            name, version = plugin_key.split(":")
            
            techniques.append({
                "name": name,
                "version": version,
                "description": metadata.description,
                "safety_rating": metadata.safety_rating,
                "performance_tier": metadata.performance_tier,
                "supported_tasks": metadata.supported_tasks,
                "research_paper": metadata.research_paper,
                "usage_stats": self.usage_stats.get(plugin_key, {})
            })
        
        return sorted(techniques, key=lambda x: x["safety_rating"], reverse=True)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics"""
        
        total_plugins = len(self.plugins)
        healthy_plugins = sum(
            1 for key in self.plugins.keys()
            if self.usage_stats.get(key, {}).get('success_rate', 1.0) > 0.95
        )
        
        return {
            "total_plugins": total_plugins,
            "healthy_plugins": healthy_plugins,
            "system_health": healthy_plugins / max(total_plugins, 1),
            "load_balancer_status": await self.load_balancer.get_status(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _validate_plugin(self, plugin_class: Type[PromptingTechnique]) -> bool:
        """Validate plugin implementation"""
        
        required_methods = ['process', 'validate_request']
        
        for method in required_methods:
            if not hasattr(plugin_class, method):
                print(f"❌ Plugin missing required method: {method}")
                return False
        
        return True
    
    def _resolve_plugin_key(self, name: str, version: str) -> str:
        """Resolve plugin key handling 'latest' version"""
        
        if version == "latest":
            # Find latest version
            matching_keys = [key for key in self.plugins.keys() if key.startswith(f"{name}:")]
            if not matching_keys:
                raise ValueError(f"No versions found for plugin: {name}")
            
            # Sort by version and return latest
            latest_key = sorted(matching_keys, reverse=True)[0]
            return latest_key
        else:
            return f"{name}:{version}"
    
    async def _record_usage(self, plugin_key: str, latency: float, success: bool):
        """Record usage statistics"""
        
        if plugin_key not in self.usage_stats:
            self.usage_stats[plugin_key] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_latency': 0.0,
                'last_used': None
            }
        
        stats = self.usage_stats[plugin_key]
        stats['total_requests'] += 1
        stats['total_latency'] += latency
        stats['last_used'] = datetime.now().isoformat()
        
        if success:
            stats['successful_requests'] += 1
        
        # Calculate derived metrics
        stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
        stats['average_latency'] = stats['total_latency'] / stats['total_requests']

class LoadBalancer:
    """Simple load balancer for plugin execution"""
    
    def __init__(self):
        self.request_counts = {}
        self.throttle_limits = {}
    
    async def should_throttle(self, plugin_key: str) -> bool:
        """Determine if plugin should be throttled"""
        
        current_count = self.request_counts.get(plugin_key, 0)
        limit = self.throttle_limits.get(plugin_key, 100)  # Default limit
        
        return current_count > limit
    
    async def get_status(self) -> Dict[str, Any]:
        """Get load balancer status"""
        
        return {
            "active_plugins": len(self.request_counts),
            "total_requests": sum(self.request_counts.values()),
            "throttled_plugins": [
                key for key in self.request_counts.keys()
                if await self.should_throttle(key)
            ]
        }

# Global registry instance
registry = EnterprisePluginRegistry()