import sqlite3
import json

conn = sqlite3.connect('pocketsmart.db')
c = conn.cursor()
c.execute('SELECT id, planner_type, plan_data FROM recommendations')
rows = c.fetchall()
added = 0

for rid, ptype, pdata in rows:
    c.execute('SELECT count(*) FROM recommendation_items WHERE recommendation_id = ?', (rid,))
    if c.fetchone()[0] > 0:
        continue
    if not pdata:
        continue
    try:
        plan = json.loads(pdata)
    except Exception:
        continue
        
    items_to_add = []
    if plan.get('items'):
        items_to_add = plan['items']
    elif plan.get('materials'):
        items_to_add = [
            {
                'name': m.get('name', 'Material'),
                'category': m.get('category', 'Materials & Services'),
                'estimated_price': float(m.get('cost_estimate', 0)),
                'platform': m.get('source', 'Market Rate'),
                'product_url': '#',
                'reason': f"Quantity: {m.get('estimated_quantity', '1 unit')}",
                'image_url': None
            }
            for m in plan['materials']
        ]
    elif plan.get('cost_breakdown'):
        items_to_add = [
            {
                'name': cb.get('category', 'Cost Allocation'),
                'category': cb.get('category', 'Breakdown'),
                'estimated_price': float(cb.get('cost', 0)),
                'platform': 'Budget Model',
                'product_url': '#',
                'reason': f"{cb.get('percentage', 0)}% of total working budget",
                'image_url': None
            }
            for cb in plan['cost_breakdown']
        ]
        
    for it in items_to_add:
        c.execute('''
            INSERT INTO recommendation_items (recommendation_id, name, category, estimated_price, platform, product_url, reason, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rid,
            it.get('name', 'Item'),
            it.get('category', 'General'),
            float(it.get('estimated_price', 0)),
            it.get('platform', 'Online'),
            it.get('product_url', '#'),
            it.get('reason', 'Plan component'),
            it.get('image_url')
        ))
        added += 1

conn.commit()
print(f'Successfully backfilled {added} items!')

c.execute('SELECT id, planner_type, (SELECT count(*) from recommendation_items where recommendation_id=recommendations.id) from recommendations')
print('Updated counts:')
for row in c.fetchall():
    print(f'Rec {row[0]} ({row[1]}): {row[2]} items')
conn.close()
