import httpx
import sys

def test_domains():
    client = httpx.Client(base_url="http://127.0.0.1:8080", timeout=30.0)
    
    # 1. Login
    auth_res = client.post("/api/auth/login", json={
        "email": "alex.demo@pocketsmart.ai",
        "password": "PocketSmart2026!"
    })
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Logged in!")

    # 2. Test House Construction
    print("\n--- Testing House Construction ---")
    res = client.post("/api/planners/custom", json={
        "plan_title": "Dream Villa Construction",
        "category": "Custom",
        "custom_category": "House Building",
        "budget": 2000000,
        "target_items": ["Structure", "Plumbing", "Electrical"],
        "preferences": "Basic finish"
    }, headers=headers)
    
    data = res.json()
    print(f"Domain: {data.get('domain')}")
    print(f"Budget Used: {data.get('budget_used')}")
    if data.get('cost_breakdown'):
        print(f"Breakdown: {data.get('cost_breakdown')[0]}")
    if data.get('materials'):
        print(f"Materials: {data.get('materials')[0]}")
    
    # 3. Test Travel
    print("\n--- Testing Travel Planning ---")
    res = client.post("/api/planners/custom", json={
        "plan_title": "Goa Trip",
        "category": "Travel",
        "budget": 80000,
        "target_items": ["Flights", "Hotel", "Food"],
        "preferences": "Near the beach"
    }, headers=headers)
    
    data = res.json()
    print(f"Domain: {data.get('domain')}")
    print(f"Budget Used: {data.get('budget_used')}")
    if data.get('cost_breakdown'):
        print(f"Breakdown: {data.get('cost_breakdown')[0]}")
        
    print("\n✅ Tested Custom Domain Planners")

if __name__ == "__main__":
    test_domains()
