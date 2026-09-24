import sqlite3
import psycopg2
import urllib.parse

pwd = urllib.parse.quote_plus("Pocket@Smart#2026")
ref = "cpfjuxmxocvvefzaxint"
pg_url = f"postgresql://postgres:{pwd}@db.{ref}.supabase.co:5432/postgres"

print("Connecting to Supabase PostgreSQL...")
pg_conn = psycopg2.connect(pg_url)
pg_cur = pg_conn.cursor()

# Connect to SQLite
sqlite_conn = sqlite3.connect("c:/PocketSmart/pocketsmart.db")
sqlite_cur = sqlite_conn.cursor()

# 1. Migrate Users
sqlite_cur.execute("SELECT id, name, email, password_hash, created_at FROM users")
users = sqlite_cur.fetchall()
for u in users:
    pg_cur.execute("""
        INSERT INTO users (id, name, email, password_hash, is_active, created_at)
        VALUES (%s, %s, %s, %s, TRUE, %s)
        ON CONFLICT (id) DO UPDATE SET 
            name = EXCLUDED.name,
            password_hash = EXCLUDED.password_hash;
    """, u)
print(f"Migrated {len(users)} users.")

# 2. Migrate Recommendations
sqlite_cur.execute("SELECT id, user_id, planner_type, budget, total_estimated_cost, remaining_budget, input_data, plan_data, ai_notes, is_mock_ai, created_at FROM recommendations")
recs = sqlite_cur.fetchall()
for r in recs:
    clean_r = list(r)
    clean_r[9] = bool(clean_r[9])  # convert 0/1 to boolean
    pg_cur.execute("""
        INSERT INTO recommendations (id, user_id, planner_type, budget, total_estimated_cost, remaining_budget, input_data, plan_data, ai_notes, is_mock_ai, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, clean_r)
print(f"Migrated {len(recs)} recommendations.")

# 3. Migrate Recommendation Items
sqlite_cur.execute("SELECT id, recommendation_id, name, category, estimated_price, platform, product_url, reason, image_url FROM recommendation_items")
items = sqlite_cur.fetchall()
for i in items:
    pg_cur.execute("""
        INSERT INTO recommendation_items (id, recommendation_id, name, category, estimated_price, platform, product_url, reason, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, i)
print(f"Migrated {len(items)} recommendation items.")

# Update auto-increment sequences so new inserts don't collide
pg_cur.execute("SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));")
pg_cur.execute("SELECT setval('recommendations_id_seq', COALESCE((SELECT MAX(id) FROM recommendations), 1));")
pg_cur.execute("SELECT setval('recommendation_items_id_seq', COALESCE((SELECT MAX(id) FROM recommendation_items), 1));")

pg_conn.commit()

# Verify counts in Supabase
pg_cur.execute("SELECT count(*) FROM users;")
print("Supabase Users count:", pg_cur.fetchone()[0])
pg_cur.execute("SELECT count(*) FROM recommendations;")
print("Supabase Recommendations count:", pg_cur.fetchone()[0])
pg_cur.execute("SELECT count(*) FROM recommendation_items;")
print("Supabase Items count:", pg_cur.fetchone()[0])

sqlite_conn.close()
pg_conn.close()
print("Supabase migration complete successfully!")
