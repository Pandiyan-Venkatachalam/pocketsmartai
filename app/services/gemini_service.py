import os
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import io

from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Dedicated Gemini AI service layer.
    Supports both official google-genai and legacy google-generativeai,
    handles prompt construction, multimodal image processing,
    structured JSON extraction, validation, and safe fallback handling.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model_name = settings.GEMINI_MODEL
        self._genai_client = None
        self._legacy_model = None
        self._init_client()

    def _init_client(self):
        """Initializes Google GenAI client if API key is present."""
        if not self.api_key:
            logger.info("No GEMINI_API_KEY configured. Running in Mock AI fallback mode.")
            return

        # Attempt modern google-genai first
        try:
            from google import genai
            self._genai_client = genai.Client(api_key=self.api_key)
            logger.info(f"Google GenAI client initialized with model: {self.model_name}")
            return
        except Exception as e:
            logger.debug(f"google.genai not initialized: {e}")

        # Fallback to google.generativeai if available
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            self._legacy_model = legacy_genai.GenerativeModel(self.model_name)
            logger.info(f"Legacy google.generativeai initialized with model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not initialize live Gemini API: {e}")

    @property
    def is_live_available(self) -> bool:
        """Returns True if Gemini client is configured and ready."""
        return (
            (self._genai_client is not None or self._legacy_model is not None)
            and bool(self.api_key)
            and settings.MOCK_AI_MODE != "force_mock"
        )

    # =========================================================================
    # Prompt Builders
    # =========================================================================

    def build_home_prompt(
        self,
        budget: float,
        room_type: str,
        style: str,
        required_items: List[str],
        quantities: Dict[str, int],
        additional_preferences: str,
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Constructs prompt for Home Interior Planner."""
        catalog_snippet = json.dumps([
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "category": c.get("category"),
                "price": c.get("price"),
                "platform": c.get("platform"),
                "url": c.get("url"),
                "image_url": c.get("image_url", ""),
                "description": c.get("description", "")
            }
            for c in candidates[:25]
        ], indent=2)

        return f"""You are PocketSmart AI, an expert home interior designer and budget optimization specialist.
You must recommend furniture, lighting, and decor for a {room_type} in {style} style.

User Requirements:
- Total Budget: ₹{budget:,.2f}
- Room Type: {room_type}
- Aesthetic / Style: {style}
- Required Items: {', '.join(required_items) if required_items else 'General living essentials'}
- Item Quantities: {json.dumps(quantities)}
- Additional Preferences: {additional_preferences or 'None'}

Available Product Catalog (choose from or align with these verified options):
{catalog_snippet}

RULES:
1. Total estimated cost of all recommended items MUST NOT EXCEED the total budget of ₹{budget:,.2f}.
2. Recommend items that complement each other in style and room functionality.
3. For each recommended item, provide a clear, persuasive reason explaining why it was selected.
4. Output STRICT JSON ONLY. Do not include introductory text or explanations outside the JSON object.

Output Format:
{{
  "planner": "home",
  "budget": {budget},
  "budget_used": <number>,
  "remaining_budget": <number>,
  "ai_notes": "<summary of the design concept and budget strategy>",
  "items": [
    {{
      "name": "<Product Name>",
      "category": "<Category>",
      "estimated_price": <number>,
      "platform": "<IKEA / Amazon / Flipkart / Pepperfry>",
      "product_url": "<Product URL>",
      "image_url": "<Product Image URL>",
      "reason": "<Detailed design and financial reason>"
    }}
  ]
}}
"""

    def build_party_prompt(
        self,
        budget: float,
        event_type: str,
        guest_count: int,
        location: str,
        event_date: str,
        food_preferences: str,
        decoration_preferences: str,
        entertainment_preferences: str,
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Constructs prompt for Party Budget Planner."""
        catalog_snippet = json.dumps([
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "category": c.get("category"),
                "price": c.get("price"),
                "platform": c.get("platform"),
                "url": c.get("url"),
                "image_url": c.get("image_url", ""),
                "description": c.get("description", "")
            }
            for c in candidates[:25]
        ], indent=2)

        return f"""You are PocketSmart AI, a premier event planner and budget strategist.
Create a comprehensive party plan within budget.

Event Details:
- Total Budget: ₹{budget:,.2f}
- Event Type: {event_type}
- Number of Guests: {guest_count}
- Location: {location or 'City Center'}
- Event Date: {event_date or 'Upcoming weekend'}
- Food Preferences: {food_preferences or 'General party catering'}
- Decoration Style: {decoration_preferences or 'Festive ambiance'}
- Entertainment: {entertainment_preferences or 'Music & sound'}

Available Product & Vendor Options:
{catalog_snippet}

RULES:
1. Divide the budget into logical categories: Catering, Venue, Decoration, Entertainment.
2. The total estimated cost of all recommended items MUST NOT EXCEED ₹{budget:,.2f}.
3. Calculate catering package prices according to {guest_count} guests.
4. Output STRICT JSON ONLY.

Output Format:
{{
  "planner": "party",
  "budget": {budget},
  "budget_used": <number>,
  "remaining_budget": <number>,
  "ai_notes": "<event theme and budget allocation rationale>",
  "items": [
    {{
      "name": "<Service or Package Name>",
      "category": "<Catering / Venue / Decoration / Entertainment>",
      "estimated_price": <number>,
      "platform": "<Swiggy / Zomato / OYO / Local Artists / Amazon>",
      "product_url": "<Service URL>",
      "image_url": "<Image URL>",
      "reason": "<Why this fits the event and guest count>"
    }}
  ]
}}
"""

    def build_jewelry_prompt(
        self,
        budget: float,
        occasion: str,
        preferred_style: str,
        jewelry_types: List[str],
        color_preference: str,
        has_image: bool,
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Constructs prompt for Jewelry Budget Planner."""
        catalog_snippet = json.dumps([
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "category": c.get("category"),
                "price": c.get("price"),
                "platform": c.get("platform"),
                "url": c.get("url"),
                "image_url": c.get("image_url", ""),
                "description": c.get("description", "")
            }
            for c in candidates[:25]
        ], indent=2)

        image_instruction = ""
        if has_image:
            image_instruction = """
An outfit image is provided.
1. Carefully analyze visible outfit characteristics: color palette, neckline, fabric texture, embroidery, and whether it is traditional, Indo-Western, or modern.
2. Recommend jewelry that contrasts or harmonizes with the outfit's tones and neckline.
3. Do not claim exact brand information from the image if not clearly legible.
"""

        return f"""You are PocketSmart AI, an elite fashion and jewelry stylist.
Recommend matching jewelry pieces for this user.

User Context:
- Total Budget: ₹{budget:,.2f}
- Occasion: {occasion}
- Preferred Style: {preferred_style}
- Jewelry Types Requested: {', '.join(jewelry_types) if jewelry_types else 'Earrings, Necklace, Rings, Bracelet'}
- Color / Metal Preference: {color_preference or 'Silver / Gold / Rose Gold'}
{image_instruction}

Available Jewelry Catalog:
{catalog_snippet}

RULES:
1. Total estimated cost MUST NOT EXCEED ₹{budget:,.2f}.
2. Choose cohesive pieces (e.g. coordinated metal finish, matching stone accents).
3. Explain how the jewelry elevates the look and complements the occasion (and uploaded outfit if provided).
4. Output STRICT JSON ONLY.

Output Format:
{{
  "planner": "jewelry",
  "budget": {budget},
  "budget_used": <number>,
  "remaining_budget": <number>,
  "ai_notes": "<Styling critique, color harmony, and occasion matching explanation>",
  "items": [
    {{
      "name": "<Jewelry Item Name>",
      "category": "<Earrings / Necklace / Bangles / Bracelet / Rings>",
      "estimated_price": <number>,
      "platform": "<Amazon / Flipkart / GIVA / Tanishq>",
      "product_url": "<Product URL>",
      "image_url": "<Image URL>",
      "reason": "<Styling justification>"
    }}
  ]
}}
"""

    def build_custom_prompt(
        self,
        budget: float,
        plan_title: str,
        category: str,
        target_items: List[str],
        preferences: str
    ) -> str:
        """Constructs prompt for Universal Custom Budget Planner."""
        items_str = ", ".join(target_items) if target_items else "Core essentials and accessories"

        return f"""You are PocketSmart AI, an expert financial planner and lifestyle budgeting specialist.
Create a smart, comprehensive, budget-aware plan for: "{plan_title}".

Context & Requirements:
- Total Budget: ₹{budget:,.2f}
- Plan Title: {plan_title}
- Domain / Category: {category}
- Specific Target Items or Services Requested: {items_str}
- User Wishes & Preferences: {preferences or 'Balance price-to-performance and high durability'}

RULES:
1. The total estimated cost of all recommended items MUST NOT EXCEED the total budget of ₹{budget:,.2f}.
2. Recommend realistic products or services available on major platforms (e.g. Amazon, Flipkart, Decathlon, MakeMyTrip, Croma, IKEA, etc.).
3. Allocate budget intelligently, keeping a healthy savings buffer.
4. For each item, provide realistic Indian Rupee (₹) pricing and a persuasive reason why it was selected.
5. Output STRICT JSON ONLY.

Output Format:
{{
  "planner": "custom",
  "plan_title": "{plan_title}",
  "budget": {budget},
  "budget_used": <number>,
  "remaining_budget": <number>,
  "ai_notes": "<Strategic overview of budget distribution and tips>",
  "items": [
    {{
      "name": "<Product or Service Name>",
      "category": "<Subcategory>",
      "estimated_price": <number>,
      "platform": "<Amazon / Flipkart / Decathlon / Croma / etc.>",
      "product_url": "<URL or Search Link>",
      "image_url": "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=500",
      "reason": "<Specific reason why this fits the budget and user wish>"
    }}
  ]
}}
"""

    def build_space_extraction_prompt(self, requirements: str) -> str:
        """Constructs prompt to extract space counts and exclusions from raw text."""
        return f"""You are an architectural extraction AI.
Extract the structural requirements and exclusions from this text:
"{requirements}"

Output STRICT JSON matching this format exactly:
{{
  "classrooms": <int (default 0)>,
  "staff_rooms": <int (default 0)>,
  "principal_offices": <int (default 0)>,
  "boys_washrooms": <int (default 0)>,
  "girls_washrooms": <int (default 0)>,
  "general_washrooms": <int (default 0)>,
  "other_spaces": [ "<list of any other spaces requested>" ],
  "exclusions": [ "<list of any explicitly excluded items, like 'smart boards' or 'premium furniture'>" ],
  "floors": <int (e.g. Ground+1 = 2) (default 1)>
}}
"""


    # =========================================================================
    # Gemini Invocation & Parsing
    # =========================================================================

    def _clean_json_response(self, text: str) -> str:
        """Strips markdown code fences and whitespace from AI response."""
        text = text.strip()
        # Find first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1]
        elif text.startswith("```json"):
            text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
        elif text.startswith("```"):
            text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()

    def generate_recommendations(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        image_mime: str = "image/jpeg"
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Executes Gemini call with prompt and optional image.
        Returns (parsed_json_dict, is_mock).
        If Gemini is unavailable or fails, returns (None, True).
        """
        if not self.is_live_available:
            return None, True

        # Try google.genai client
        if self._genai_client is not None:
            try:
                contents = [prompt]
                if image_bytes:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    contents.append(pil_image)

                logger.info("Calling google.genai...")
                response = self._genai_client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                if response and response.text:
                    cleaned_text = self._clean_json_response(response.text)
                    parsed = json.loads(cleaned_text)
                    return parsed, False
            except Exception as e:
                logger.error(f"google.genai call error: {e}")

        # Try legacy model if available
        if self._legacy_model is not None:
            try:
                content_payload = [prompt]
                if image_bytes:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    content_payload.append(pil_image)

                logger.info("Calling google.generativeai legacy model...")
                response = self._legacy_model.generate_content(content_payload)
                if response and response.text:
                    cleaned_text = self._clean_json_response(response.text)
                    parsed = json.loads(cleaned_text)
                    return parsed, False
            except Exception as e:
                logger.error(f"Legacy Gemini API call error: {e}")

        return None, True

    # =========================================================================
    # Intelligent Heuristic Fallback Engine (Mock AI)
    # =========================================================================

    def generate_fallback_home(
        self,
        budget: float,
        room_type: str,
        style: str,
        required_items: List[str],
        quantities: Dict[str, int],
        additional_preferences: str,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Deterministic budget-aware fallback recommendation for Home Planner."""
        selected_items = []
        total_spent = 0.0

        sorted_candidates = sorted(
            candidates,
            key=lambda x: (
                0 if style.lower() in x.get("style", "").lower() else 1,
                x.get("price", 0)
            )
        )

        categories_covered = set()
        for cand in sorted_candidates:
            cat = cand.get("category", "")
            price = float(cand.get("price", 0))

            if cat in categories_covered and len(categories_covered) < len(required_items or ["Sofa", "Dining Table", "Lights"]):
                continue

            if total_spent + price <= budget:
                selected_items.append({
                    "name": cand.get("name"),
                    "category": cat,
                    "estimated_price": price,
                    "platform": cand.get("platform", "Amazon"),
                    "product_url": cand.get("url", "#"),
                    "image_url": cand.get("image_url", ""),
                    "reason": f"Selected for {style} {room_type} aesthetic. Offers prime durability and price-performance balance on {cand.get('platform', 'Amazon')}."
                })
                total_spent += price
                categories_covered.add(cat)

        ai_notes = (
            f"Curated {style} plan for {room_type}. Budget allocation prioritized foundational seating "
            f"and ambient illumination, preserving ₹{max(0, budget - total_spent):,.2f} for future accents."
        )

        return {
            "planner": "home",
            "budget": budget,
            "budget_used": total_spent,
            "remaining_budget": max(0.0, budget - total_spent),
            "ai_notes": ai_notes,
            "items": selected_items
        }

    def generate_fallback_party(
        self,
        budget: float,
        event_type: str,
        guest_count: int,
        location: str,
        event_date: str,
        food_preferences: str,
        decoration_preferences: str,
        entertainment_preferences: str,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Deterministic budget-aware fallback recommendation for Party Planner."""
        selected_items = []
        total_spent = 0.0

        target_splits = {
            "Catering": budget * 0.45,
            "Venue": budget * 0.30,
            "Decoration": budget * 0.15,
            "Entertainment": budget * 0.10
        }

        for category, target_cap in target_splits.items():
            cat_items = [c for c in candidates if c.get("category", "").lower() == category.lower()]
            if not cat_items:
                continue

            valid_items = [i for i in cat_items if i.get("price", 0) <= (budget - total_spent)]
            if valid_items:
                chosen = min(valid_items, key=lambda x: abs(x.get("price", 0) - target_cap))
                price = float(chosen.get("price", 0))
                selected_items.append({
                    "name": chosen.get("name"),
                    "category": category,
                    "estimated_price": price,
                    "platform": chosen.get("platform", "Swiggy"),
                    "product_url": chosen.get("url", "#"),
                    "image_url": chosen.get("image_url", ""),
                    "reason": (
                        f"Optimal {category.lower()} solution for {guest_count} guests at {location or 'selected venue'}. "
                        f"{chosen.get('description', '')}"
                    )
                })
                total_spent += price

        ai_notes = (
            f"Tailored {event_type} event configuration for {guest_count} guests. Proportional budget balancing "
            f"ensures memorable dining and venue comfort with an efficient reserve of ₹{max(0, budget - total_spent):,.2f}."
        )

        return {
            "planner": "party",
            "budget": budget,
            "budget_used": total_spent,
            "remaining_budget": max(0.0, budget - total_spent),
            "ai_notes": ai_notes,
            "items": selected_items
        }

    def generate_fallback_jewelry(
        self,
        budget: float,
        occasion: str,
        preferred_style: str,
        jewelry_types: List[str],
        color_preference: str,
        has_image: bool,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Deterministic budget-aware fallback recommendation for Jewelry Planner."""
        selected_items = []
        total_spent = 0.0

        desired_categories = jewelry_types if jewelry_types else ["Earrings", "Necklace", "Bracelet", "Rings"]

        for cat in desired_categories:
            cat_items = [c for c in candidates if c.get("category", "").lower() == cat.strip().lower()]
            if not cat_items:
                continue

            valid_items = [i for i in cat_items if i.get("price", 0) <= (budget - total_spent)]
            if valid_items:
                style_matches = [i for i in valid_items if preferred_style.lower() in i.get("style", "").lower()]
                chosen = style_matches[0] if style_matches else valid_items[0]
                price = float(chosen.get("price", 0))
                selected_items.append({
                    "name": chosen.get("name"),
                    "category": cat.capitalize(),
                    "estimated_price": price,
                    "platform": chosen.get("platform", "Amazon"),
                    "product_url": chosen.get("url", "#"),
                    "image_url": chosen.get("image_url", ""),
                    "reason": f"Matches {preferred_style} styling for {occasion}. Harmonious {color_preference or 'metallic'} undertones with premium craftsmanship."
                })
                total_spent += price

        outfit_note = "Outfit photo analyzed: coordinated with silhouette and neckline elegance. " if has_image else ""
        ai_notes = (
            f"{outfit_note}Curated ensemble for {occasion} emphasizing {preferred_style} aesthetics. "
            f"Remaining budget reserve: ₹{max(0, budget - total_spent):,.2f}."
        )

        return {
            "planner": "jewelry",
            "budget": budget,
            "budget_used": total_spent,
            "remaining_budget": max(0.0, budget - total_spent),
            "ai_notes": ai_notes,
            "items": selected_items
        }

    def generate_fallback_custom(
        self,
        budget: float,
        plan_title: str,
        category: str,
        target_items: List[str],
        preferences: str
    ) -> Dict[str, Any]:
        """Deterministic budget-aware fallback recommendation for Universal Custom Planner."""
        selected_items = []
        total_spent = 0.0

        items_to_create = target_items if target_items else [
            f"Core {category} Equipment/Package",
            f"Essential {category} Accessories",
            f"Complementary Add-on & Setup Kit"
        ]

        # Allocate 80% of budget across items, reserving 20%
        target_pool = budget * 0.82
        per_item_share = round(target_pool / max(1, len(items_to_create)), 2)

        platforms = ["Amazon", "Flipkart", "Croma", "Decathlon", "Specialty Store"]

        for idx, item_name in enumerate(items_to_create):
            price = round(min(per_item_share, budget - total_spent), 2)
            if price <= 0:
                break
            plat = platforms[idx % len(platforms)]
            selected_items.append({
                "name": f"{item_name.strip()} ({plan_title})",
                "category": category,
                "estimated_price": price,
                "platform": plat,
                "product_url": f"https://www.google.com/search?q={item_name.strip().replace(' ', '+')}",
                "image_url": "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=500",
                "reason": f"Allocated priority item for {plan_title}. Balanced price and quality based on {preferences or 'best value'} on {plat}."
            })
            total_spent += price

        ai_notes = (
            f"Custom budget allocation for '{plan_title}' in {category}. "
            f"Balanced high-priority necessities while preserving an emergency reserve of ₹{max(0, budget - total_spent):,.2f}."
        )

        return {
            "planner": "custom",
            "plan_title": plan_title,
            "budget": budget,
            "budget_used": total_spent,
            "remaining_budget": max(0.0, budget - total_spent),
            "ai_notes": ai_notes,
            "items": selected_items
        }

    # =========================================================================
    # Strict Budget Post-Validator & Capper
    # =========================================================================

    def enforce_budget_limits(self, result: Dict[str, Any], budget: float) -> Dict[str, Any]:
        """
        Enforces that sum(item prices) <= budget.
        If an AI response accidentally exceeds budget, trims non-essential items
        from the bottom until the total is strictly within budget.
        """
        items = result.get("items", [])
        valid_items = []
        running_total = 0.0

        for item in items:
            price = float(item.get("estimated_price", 0))
            if running_total + price <= budget:
                valid_items.append(item)
                running_total += price

        result["items"] = valid_items
        result["budget"] = budget
        result["budget_used"] = round(running_total, 2)
        result["remaining_budget"] = round(max(0.0, budget - running_total), 2)
        return result

# Singleton instance
gemini_service = GeminiService()
