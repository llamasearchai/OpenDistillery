from abc import ABC, abstractmethod

class ResearchTechnique(ABC):
    
    @abstractmethod
    async def execute(self, problem, context=None):
        """Executes the research technique."""
        pass 