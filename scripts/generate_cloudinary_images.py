import sqlite3
import requests
import cloudinary
import cloudinary.uploader
import time

cloudinary.config(
    cloud_name="dqr1zbyeb",
    api_key="273174792865529",
    api_secret="jF_wQ3z_92GCh6kCk_YxmN1G4r0",
    secure=True
)

conn = sqlite3.connect("c:/PocketSmart/pocketsmart.db")
c = conn.cursor()

c.execute("SELECT DISTINCT name FROM recommendation_items WHERE image_url IS NULL OR image_url = ''")
unique_items = [row[0] for row in c.fetchall()]
print(f"Generating images for {len(unique_items)} unique item names...")

cache = {}

for name in unique_items:
    try:
        clean = name.strip()
        prompt = f"professional product photography of {clean}, isolated on clean studio background, high resolution 4k"
        safe_encoded = requests.utils.quote(prompt)
        pollinations_url = f"https://image.pollinations.ai/prompt/{safe_encoded}?width=400&height=400&nologo=true"
        
        # Upload directly to Cloudinary
        res = cloudinary.uploader.upload(
            pollinations_url,
            folder="pocketsmart_items"
        )
        url = res.get("secure_url")
        if url:
            cache[name] = url
            print(f"[OK] {name} -> {url}")
        else:
            fallback = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean)}?width=400&height=400&nologo=true"
            cache[name] = fallback
            print(f"[FALLBACK] {name} -> {fallback}")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        fallback = f"https://image.pollinations.ai/prompt/{requests.utils.quote(name)}?width=400&height=400&nologo=true"
        cache[name] = fallback

for name, url in cache.items():
    c.execute("UPDATE recommendation_items SET image_url = ? WHERE name = ? AND (image_url IS NULL OR image_url = '')", (url, name))

conn.commit()
print("All missing item images updated with Cloudinary URLs!")

# Verify recommendation 13
c.execute("SELECT id, name, image_url FROM recommendation_items WHERE recommendation_id = 13")
print("Recommendation 13 items:")
for row in c.fetchall():
    print(row)

conn.close()
