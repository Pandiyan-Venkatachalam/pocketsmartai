from app.services.planning.interfaces import IPlanningDomainDetector
from app.schemas.custom_planner import CustomPlannerInput

class HeuristicDomainDetector(IPlanningDomainDetector):
    def detect_domain(self, input_data: CustomPlannerInput) -> str:
        items_str = " ".join(input_data.target_items) if isinstance(input_data.target_items, list) else str(input_data.target_items or "")
        text = f"{input_data.plan_title} {input_data.category} {input_data.custom_category} {items_str} {input_data.preferences}".lower()
        
        if any(w in text for w in ["school", "college", "institute", "university", "classroom"]):
            return "SCHOOL_CONSTRUCTION"
        if any(w in text for w in ["house", "construct", "building", "home build", "villa"]):
            return "HOUSE_CONSTRUCTION"
        if any(w in text for w in ["wedding", "marriage", "reception", "bride", "groom"]):
            return "WEDDING"
        if any(w in text for w in ["travel", "trip", "vacation", "holiday", "tour", "beach"]):
            return "TRAVEL"
        if any(w in text for w in ["business", "shop", "restaurant", "bakery", "cafe", "startup", "office setup", "factory"]):
            return "BUSINESS_SETUP"
        if any(w in text for w in ["party", "event", "birthday", "anniversary", "function"]):
            return "EVENT"
        if any(w in text for w in ["farm", "agriculture", "tractor"]):
            return "AGRICULTURE"
        if any(w in text for w in ["car ", "vehicle", "bike", "motorcycle"]):
            return "VEHICLE"
            
        return "GENERAL"

domain_detector = HeuristicDomainDetector()
