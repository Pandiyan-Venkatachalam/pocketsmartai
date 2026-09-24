import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RateService:
    def __init__(self):
        self.rates = {}
        self.config_file = Path(__file__).parent.parent / "data" / "rates.json"
        self.reload()

    def reload(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self.rates = json.load(f)
                logger.info("Rates configuration loaded successfully.")
            else:
                logger.warning(f"Rates file not found at {self.config_file}. Using hardcoded fallback defaults.")
        except Exception as e:
            logger.error(f"Failed to load rates configuration: {e}")

    def get_rate(self, category: str, key: str, default: float) -> float:
        try:
            return float(self.rates.get(category, {}).get(key, default))
        except (ValueError, TypeError):
            return default

rate_service = RateService()
