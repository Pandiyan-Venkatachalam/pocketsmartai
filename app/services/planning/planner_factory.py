from app.services.planning.interfaces import IPlannerFactory, IPlanner
from app.services.planning.house_planner import HouseConstructionPlanner
from app.services.planning.wedding_planner import WeddingPlanner
from app.services.planning.travel_planner import TravelPlanner
from app.services.planning.business_planner import BusinessSetupPlanner
from app.services.planning.school_planner import SchoolConstructionPlanner

class PlannerFactory(IPlannerFactory):
    def __init__(self):
        self.planners = {
            "HOUSE_CONSTRUCTION": HouseConstructionPlanner(),
            "WEDDING": WeddingPlanner(),
            "TRAVEL": TravelPlanner(),
            "BUSINESS_SETUP": BusinessSetupPlanner(),
            "SCHOOL_CONSTRUCTION": SchoolConstructionPlanner(),
        }

    def get_planner(self, domain: str) -> IPlanner:
        return self.planners.get(domain)

planner_factory = PlannerFactory()
