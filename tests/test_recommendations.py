from app.services.gemini_service import gemini_service

def test_budget_capping_invariant():
    """Verify that enforce_budget_limits never allows sum of items to exceed budget."""
    unruly_items = [
        {"name": "Item A", "estimated_price": 50000},
        {"name": "Item B", "estimated_price": 40000},
        {"name": "Item C", "estimated_price": 20000},
    ]
    raw_result = {"items": unruly_items}
    budget = 70000

    enforced = gemini_service.enforce_budget_limits(raw_result, budget)
    assert enforced["budget_used"] <= budget
    assert sum(i["estimated_price"] for i in enforced["items"]) <= budget
    assert enforced["remaining_budget"] >= 0

def test_history_and_dashboard_flow(client, auth_headers):
    # 1. Create a home plan
    home_res = client.post("/api/planners/home", json={
        "total_budget": 60000,
        "room_type": "Living Room",
        "style": "Minimalist",
        "required_items": ["Sofa", "Lights"],
        "quantities": {"Sofa": 1, "Lights": 1},
        "additional_preferences": ""
    }, headers=auth_headers)
    assert home_res.status_code == 200
    rec_id = home_res.json()["recommendation_id"]

    # 2. Check dashboard stats
    dash_res = client.get("/api/dashboard", headers=auth_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_recommendations"] >= 1
    assert dash_data["total_budget_planned"] >= 60000

    # 3. Retrieve history list
    hist_res = client.get("/api/history", headers=auth_headers)
    assert hist_res.status_code == 200
    history_items = hist_res.json()
    assert len(history_items) >= 1
    assert any(h["id"] == rec_id for h in history_items)

    # 4. Retrieve single recommendation detail
    detail_res = client.get(f"/api/history/{rec_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == rec_id
    assert len(detail_data["items"]) > 0

    # 5. Delete recommendation
    del_res = client.delete(f"/api/history/{rec_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    after_del_res = client.get(f"/api/history/{rec_id}", headers=auth_headers)
    assert after_del_res.status_code == 404
