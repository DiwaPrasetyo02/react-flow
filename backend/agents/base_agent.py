from abc import ABC, abstractmethod
from typing import Any, Dict
import time

class BaseAgent(ABC):
    def __init__(self, name: str, layer: int):
        self.name = name
        self.layer = layer

    @abstractmethod
    async def execute(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """Execute the agent's main task"""
        pass

    async def process(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """Process input and return standardized response"""
        start_time = time.time()

        try:
            result = await self.execute(input_data, parameters)
            execution_time = time.time() - start_time

            return {
                "agent_name": self.name,
                "layer": self.layer,
                "status": "completed",
                "input": input_data,
                "output": result,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "agent_name": self.name,
                "layer": self.layer,
                "status": "error",
                "input": input_data,
                "output": None,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "execution_time": execution_time
            }
