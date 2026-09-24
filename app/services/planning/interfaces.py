# Interfaces for the Domain-Aware Planning Engine

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from app.schemas.custom_planner import CustomPlannerOutput, CustomPlannerInput

class IPlanningDomainDetector(ABC):
    @abstractmethod
    def detect_domain(self, input_data: CustomPlannerInput) -> str:
        pass

class ICalculationEngine(ABC):
    @abstractmethod
    def calculate(self, budget: float, requirements: Dict[str, Any]) -> Dict[str, Any]:
        pass

class IPlanner(ABC):
    @property
    @abstractmethod
    def domain(self) -> str:
        pass

    @abstractmethod
    def generate_plan(self, request: CustomPlannerInput) -> CustomPlannerOutput:
        pass

class IPlannerFactory(ABC):
    @abstractmethod
    def get_planner(self, domain: str) -> IPlanner:
        pass
