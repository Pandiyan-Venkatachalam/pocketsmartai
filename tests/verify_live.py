import sys
import httpx
sys.stdout.reconfigure(encoding='utf-8')

def run_verification():
    client = httpx.Client(base_url="http://127.0.0.1:8080", timeout=30.0)

    print("--- 1. Checking Health ---")
    h = client.get("/api/health")
    print("Health response:", h.status_code, h.json())
    assert h.status_code == 200

    print("--- 2. Checking Landing Page ---")
    l = client.get("/")
    print("Landing page status:", l.status_code, "HTML length:", len(l.text))
    assert l.status_code == 200
    assert "PocketSmart" in l.text

    print("--- 3. Testing Login with Demo User ---")
    auth_res = client.post("/api/auth/login", json={
        "email": "alex.demo@pocketsmart.ai",
        "password": "PocketSmart2026!"
    })
    print("Login status:", auth_res.status_code)
    assert auth_res.status_code == 200
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("--- 4. Testing Home Interior Planner ---")
    home_res = client.post("/api/planners/home", json={
        "total_budget": 100000,
        "room_type": "Living Room",
        "style": "Modern",
        "required_items": ["Sofa", "Ceiling Fan", "Lights", "Dining Table"],
        "quantities": {"Sofa": 1, "Ceiling Fan": 1, "Lights": 2, "Dining Table": 1},
        "additional_preferences": "Prefer wooden finish and warm lighting"
    }, headers=headers)
    print("Home Planner status:", home_res.status_code)
    assert home_res.status_code == 200
    home_data = home_res.json()
    print("  Budget:", home_data["budget"], "Spent:", home_data["budget_used"], "Remaining:", home_data["remaining_budget"])
    print("  Items recommended:", len(home_data["items"]))
    for it in home_data["items"]:
        print(f"    - [{it['platform']}] {it['name']}: ₹{it['estimated_price']}")
    home_rec_id = home_data["recommendation_id"]

    print("--- 5. Testing Party Budget Planner with Dropdowns + Custom Wishes ---")
    party_res = client.post("/api/planners/party", json={
        "budget": 50000,
        "event_type": "Birthday Party",
        "guest_count": 25,
        "location": "Koramangala, Bengaluru",
        "event_date": "Next Saturday",
        "food_preferences": "3-Course Gourmet Buffet",
        "decoration_preferences": "Pastel Balloon Arch",
        "entertainment_preferences": "DJ Setup",
        "custom_wishes": "Retro 80s synthwave theme with neon table runners and custom mocktail station"
    }, headers=headers)
    print("Party Planner status:", party_res.status_code)
    assert party_res.status_code == 200
    party_data = party_res.json()
    print("  Budget:", party_data["budget"], "Spent:", party_data["budget_used"], "Remaining:", party_data["remaining_budget"])
    for it in party_data["items"]:
        print(f"    - [{it['category']} on {it['platform']}] {it['name']}: ₹{it['estimated_price']}")

    print("--- 5b. Testing Universal Custom Budget Planner ---")
    custom_res = client.post("/api/planners/custom", json={
        "plan_title": "Ergonomic Home Tech Workstation",
        "category": "Tech & Desk Setup",
        "budget": 85000,
        "target_items": ["Standing Desk", "Ergonomic Chair", "4K Monitor", "Mechanical Keyboard"],
        "preferences": "Minimalist matte black aesthetic with motorized dual motor desk"
    }, headers=headers)
    print("Custom Planner status:", custom_res.status_code)
    assert custom_res.status_code == 200
    custom_data = custom_res.json()
    print("  Budget:", custom_data["budget"], "Spent:", custom_data["budget_used"], "Remaining:", custom_data["remaining_budget"])
    print("  Items count:", len(custom_data["items"]))
    for it in custom_data["items"]:
        print(f"    - [{it['category']} on {it['platform']}] {it['name']}: ₹{it['estimated_price']}")
    assert len(custom_data["items"]) >= 3
    assert custom_data["budget_used"] <= 85000

    print("--- 6. Testing Jewelry Planner (JSON) ---")
    jewel_res = client.post("/api/planners/jewelry/json", json={
        "budget": 15000,
        "occasion": "Wedding Reception",
        "preferred_style": "Ethnic/Traditional",
        "jewelry_type": ["Earrings", "Necklace"],
        "color_preference": "Gold"
    }, headers=headers)
    print("Jewelry Planner status:", jewel_res.status_code)
    assert jewel_res.status_code == 200
    jewel_data = jewel_res.json()
    print("  Budget:", jewel_data["budget"], "Spent:", jewel_data["budget_used"], "Remaining:", jewel_data["remaining_budget"])
    for it in jewel_data["items"]:
        print(f"    - [{it['category']} on {it['platform']}] {it['name']}: ₹{it['estimated_price']}")

    print("--- 7. Testing Dashboard Stats ---")
    dash = client.get("/api/dashboard", headers=headers)
    print("Dashboard status:", dash.status_code)
    assert dash.status_code == 200
    dash_json = dash.json()
    print("  User:", dash_json["user_name"], "Total plans:", dash_json["total_recommendations"], "Total budget:", dash_json["total_budget_planned"])

    print("--- 8. Testing History API ---")
    hist = client.get("/api/history", headers=headers)
    print("History status:", hist.status_code)
    assert hist.status_code == 200
    print("  History count:", len(hist.json()))
    print("--- 9. Testing Recommendation Results HTML View ---")
    cookie_client = httpx.Client(base_url="http://127.0.0.1:8080", cookies={"access_token": f"Bearer {token}"})
    rec_page = cookie_client.get(f"/recommendations/{home_rec_id}")
    print("Recommendations HTML page status:", rec_page.status_code)
    assert rec_page.status_code == 200
    assert "Curated Recommendations" in rec_page.text

    print("--- 10. Testing Planner HTML Views ---")
    party_page = cookie_client.get("/planners/party")
    print("Party Planner HTML page status:", party_page.status_code)
    assert party_page.status_code == 200
    assert "Custom Wishes" in party_page.text

    custom_page = cookie_client.get("/planners/custom")
    print("Custom Planner HTML page status:", custom_page.status_code)
    assert custom_page.status_code == 200
    assert "Universal Budget Planner" in custom_page.text

    print("\n✅ ALL LIVE END-TO-END WORKFLOWS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verification()
