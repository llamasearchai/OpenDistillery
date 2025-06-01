"""
OpenDistillery: Advanced Compound AI Systems for Enterprise Workflow Transformation

A production-ready framework for building intelligent systems using multiple models,
reasoning techniques, and agentic collaboration patterns.
"""

__version__ = "1.0.0"
__author__ = "Nik Jois"
__email__ = "nikjois@llamasearch.ai"

# Package metadata
__title__ = "OpenDistillery"
__description__ = "Advanced Compound AI Systems for Enterprise Workflow Transformation"
__url__ = "https://github.com/opendistillery/opendistillery"
__license__ = "MIT"

# Import core components for easy access
try:
    from .core.compound_system import SystemBuilder, SystemRequirements, SystemArchitecture
    from .agents.base_agent import BaseAgent, AgentCapability
    from .agents.orchestrator import AgentOrchestrator
    from .api.server import app
except ImportError:
    # Handle import errors gracefully during development
    pass

__all__ = [
    "SystemBuilder",
    "SystemRequirements", 
    "SystemArchitecture",
    "BaseAgent",
    "AgentCapability",
    "AgentOrchestrator",
    "app"
] 