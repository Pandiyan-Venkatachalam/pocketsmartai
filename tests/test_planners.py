import io

def test_home_planner_success(client, auth_headers):
    payload = {
        "total_budget": 80000,
        "room_type": "Living Room",
        "style": "Modern",
        "required_items": ["Sofa", "Lights", "Dining Table"],
        "quantities": {"Sofa": 1, "Lights": 2, "Dining Table": 1},
        "additional_preferences": "Neutral tones"
    }
    res = client.post("/api/planners/home", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["planner"] == "home"
    assert data["budget"] == 80000
    assert data["budget_used"] <= 80000
    assert data["remaining_budget"] >= 0
    assert len(data["items"]) > 0
    assert data["recommendation_id"] is not None

    # Check item structure
    first_item = data["items"][0]
    assert "name" in first_item
    assert "estimated_price" in first_item
    assert "platform" in first_item
    assert "reason" in first_item

def test_home_planner_zero_budget_fails(client, auth_headers):
    payload = {
        "total_budget": 0,
        "room_type": "Living Room",
        "style": "Modern"
    }
    res = client.post("/api/planners/home", json=payload, headers=auth_headers)
    assert res.status_code == 422 or res.status_code == 400

def test_party_planner_success(client, auth_headers):
    payload = {
        "budget": 45000,
        "event_type": "Birthday Party",
        "guest_count": 20,
        "location": "City Center",
        "event_date": "Next Weekend",
        "food_preferences": "3-Course Gourmet",
        "decoration_preferences": "Balloons",
        "entertainment_preferences": "DJ"
    }
    res = client.post("/api/planners/party", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["planner"] == "party"
    assert data["budget"] == 45000
    assert data["budget_used"] <= 45000
    assert data["remaining_budget"] >= 0
    assert len(data["items"]) > 0

def test_party_planner_invalid_guests_fails(client, auth_headers):
    payload = {
        "budget": 50000,
        "event_type": "Birthday",
        "guest_count": 0
    }
    res = client.post("/api/planners/party", json=payload, headers=auth_headers)
    assert res.status_code == 422 or res.status_code == 400

def test_jewelry_planner_json(client, auth_headers):
    payload = {
        "budget": 15000,
        "occasion": "Wedding",
        "preferred_style": "Ethnic/Traditional",
        "jewelry_type": ["Earrings", "Necklace"],
        "color_preference": "Gold"
    }
    res = client.post("/api/planners/jewelry/json", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["planner"] == "jewelry"
    assert data["budget"] == 15000
    assert data["budget_used"] <= 15000
    assert len(data["items"]) > 0

def test_jewelry_planner_multipart_with_image(client, auth_headers):
    # Create fake image bytes
    fake_img = io.BytesIO(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00")
    files = {"outfit_image": ("outfit.jpg", fake_img, "image/jpeg")}
    data = {
        "budget": "20000",
        "occasion": "Cocktail Evening",
        "preferred_style": "Modern Luxury",
        "jewelry_types": "Earrings,Bracelet",
        "color_preference": "Rose Gold"
    }
    res = client.post("/api/planners/jewelry", data=data, files=files, headers=auth_headers)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["budget_used"] <= 20000
    assert len(res_data["items"]) > 0

def test_party_planner_custom_typed_wish(client, auth_headers):
    payload = {
        "budget": 35000,
        "event_type": "90s Bollywood Retro Disco Night",
        "guest_count": 15,
        "location": "Indiranagar Rooftop",
        "event_date": "Next Friday",
        "food_preferences": "Authentic Street Food & Live Chaat Counter",
        "decoration_preferences": "Disco Mirror Balls & Neon Glow Signs",
        "entertainment_preferences": "Karaoke Setup & Vinyl DJ"
    }
    res = client.post("/api/planners/party", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["planner"] == "party"
    assert data["budget"] == 35000
    assert data["budget_used"] <= 35000
    assert len(data["items"]) > 0

def test_custom_planner_endpoint(client, auth_headers):
    payload = {
        "plan_title": "Goa Beach Holiday Trip",
        "budget": 60000,
        "category": "Travel & Vacation",
        "target_items": ["Flight Tickets", "Boutique Resort Stay", "Scooty Rental", "Beach Dinner"],
        "preferences": "Sea-facing rooms and fresh seafood"
    }
    res = client.post("/api/planners/custom", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["planner"] == "custom"
    assert data["plan_title"] == "Goa Beach Holiday Trip"
    assert data["budget"] == 60000
    assert data["budget_used"] <= 60000
    assert len(data["items"]) > 0
    assert data["recommendation_id"] is not None

def test_custom_planner_user_defined_category(client, auth_headers):
    payload = {
        "plan_title": "Compact Garage Home Gym",
        "budget": 40000,
        "category": "Custom",
        "custom_category": "Fitness & Weightlifting",
        "target_items": ["Adjustable Dumbbells", "Flat Bench", "Pull-up Bar", "Rubber Flooring Mats"],
        "preferences": "High durability and rubberized weights"
    }
    res = client.post("/api/planners/custom", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["budget_used"] <= 40000
    assert len(data["items"]) > 0
