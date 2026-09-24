import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class ProductService:
    """
    Product & Service retrieval layer.
    Allows planners to access verified product catalogs (Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, etc.)
    and can easily be extended to connect to real vendor APIs or databases without modifying recommendation planners.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or settings.MOCK_PRODUCTS_PATH
        self._catalog: Dict[str, List[Dict[str, Any]]] = {}
        self.load_catalog()

    def load_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads and caches the product catalog from JSON file."""
        if not self.data_path.exists():
            logger.warning(f"Mock products file not found at {self.data_path}. Creating fallback empty catalog.")
            self._catalog = {"home": [], "party": [], "jewelry": []}
            return self._catalog

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self._catalog = json.load(f)
            logger.info(
                f"Loaded catalog: {len(self._catalog.get('home', []))} home items, "
                f"{len(self._catalog.get('party', []))} party items, "
                f"{len(self._catalog.get('jewelry', []))} jewelry items."
            )
        except Exception as e:
            logger.error(f"Failed to load product catalog: {e}")
            self._catalog = {"home": [], "party": [], "jewelry": []}

        return self._catalog

    def get_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self._catalog:
            self.load_catalog()
        return self._catalog

    def get_domain_products(self, domain: str) -> List[Dict[str, Any]]:
        """Returns all products for a given domain ('home', 'party', 'jewelry')."""
        return self.get_catalog().get(domain.lower(), [])

    def get_home_candidates(
        self,
        style: Optional[str] = None,
        required_items: Optional[List[str]] = None,
        max_budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Filters home products suitable for the user's constraints."""
        products = self.get_domain_products("home")
        candidates = []

        req_categories = [item.strip().lower() for item in (required_items or []) if item.strip()]

        for item in products:
            item_cat = item.get("category", "").lower()
            item_price = float(item.get("price", 0))

            if max_budget is not None and item_price > max_budget:
                continue

            # Prioritize matching required item categories if specified
            if req_categories:
                matched = any(req_cat in item_cat or item_cat in req_cat for req_cat in req_categories)
                if matched:
                    candidates.append(item)
                    continue

            # Also include style matches or generic options
            if style and style.lower() in item.get("style", "").lower():
                candidates.append(item)
            else:
                candidates.append(item)

        # Deduplicate by id
        unique = {item["id"]: item for item in candidates}
        return list(unique.values())

    def get_party_candidates(
        self,
        guest_count: int,
        max_budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Calculates effective package prices for party products and filters by budget."""
        products = self.get_domain_products("party")
        candidates = []

        for item in products:
            item_copy = item.copy()
            # If price is per guest, compute total package price
            if item.get("unit") == "guest":
                effective_price = float(item.get("price_per_unit", 0)) * max(1, guest_count)
                item_copy["price"] = effective_price
                item_copy["computed_price_note"] = f"₹{item.get('price_per_unit')} x {guest_count} guests"
            else:
                effective_price = float(item.get("price", 0))

            if max_budget is not None and effective_price > max_budget:
                continue

            candidates.append(item_copy)

        return candidates

    def get_jewelry_candidates(
        self,
        jewelry_types: Optional[List[str]] = None,
        preferred_style: Optional[str] = None,
        max_budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Filters jewelry items matching the desired jewelry types and styles within budget."""
        products = self.get_domain_products("jewelry")
        candidates = []
        req_types = [t.strip().lower() for t in (jewelry_types or []) if t.strip()]

        for item in products:
            item_cat = item.get("category", "").lower()
            item_price = float(item.get("price", 0))

            if max_budget is not None and item_price > max_budget:
                continue

            if req_types:
                matched = any(t in item_cat or item_cat in t for t in req_types)
                if matched:
                    candidates.append(item)
                    continue

            candidates.append(item)

        unique = {item["id"]: item for item in candidates}
        return list(unique.values())

    def get_product_by_id(self, domain: str, product_id: str) -> Optional[Dict[str, Any]]:
        for item in self.get_domain_products(domain):
            if item.get("id") == product_id:
                return item
        return None

# Singleton instance
product_service = ProductService()
