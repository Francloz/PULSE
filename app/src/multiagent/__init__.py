# Package metadata
__version__ = "0.0.0"
__author__ = "Francisco Lozano del Moral"

# Import key classes/functions at the package level for convenience
from .agents import Agent, AgentManager
from .base_model import BaseModel
from .model import AdvancedModel

# Define what gets imported when using 'from multiagent import *'
__all__ = [
    "Agent", "AgentManager"
    "BaseModel", "Model"
]