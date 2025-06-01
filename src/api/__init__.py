"""
OpenDistillery API Framework
Enterprise-grade API endpoints and services.
"""

# Import only the basic server module to avoid complex dependencies
from .server import app

__all__ = [
    "app"
] 