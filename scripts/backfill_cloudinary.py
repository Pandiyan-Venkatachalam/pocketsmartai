import sqlite3
import cloudinary
import cloudinary.uploader
import requests
import time

cloudinary.config(
    cloud_name="dqr1zbyeb",
    api_key="273174792865529",
    api_secret="jF_wQ3z_92GCh6kCk_YxmN1G4r0",
    secure=True
)

CURATED_PHOTOS = [
    (["cement", "concrete"], "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600"),
    (["steel", "rebar", "iron"], "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600"),
    (["brick", "block", "masonry"], "https://images.unsplash.com/photo-1590069261209-f8e9b8642343?w=600"),
    (["sand", "aggregate"], "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=600"),
    (["sofa", "couch", "living"], "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600"),
    (["fan", "ceiling fan"], "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=600"),
    (["light", "lamp", "spotlight"], "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600"),
    (["dining", "dining table"], "https://images.unsplash.com/photo-1577140917170-285929fb55b7?w=600"),
    (["table", "desk"], "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=600"),
    (["chair", "seating"], "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=600"),
    (["tv unit", "tv", "entertainment"], "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600"),
    (["wardrobe", "closet"], "https://images.unsplash.com/photo-1558997519-83ea9252edf8?w=600"),
    (["bed", "mattress"], "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=600"),
    (["kitchen", "cabinet"], "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600"),
    (["paint", "primer", "color"], "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=600"),
    (["plate", "catering plates", "dinnerware"], "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600"),
    (["catering", "food", "dining"], "https://images.unsplash.com/photo-1555244162-803834f70033?w=600"),
    (["hotel", "accommodation", "resort"], "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600"),
    (["flight", "flight / transport", "airline"], "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=600"),
    (["transport", "tour", "travel", "misc"], "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=600"),
    (["photo", "video", "camera"], "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600"),
    (["music", "dj", "sound", "entertainment"], "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600"),
    (["floral", "decor", "flower"], "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600"),
    (["venue", "hall"], "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=600"),
    (["attire", "makeup", "dress"], "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600"),
    (["invitation", "cards", "favor"], "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=600"),
    (["jewelry", "jewel", "necklace"], "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=600"),
    (["gold", "bangle", "bracelet"], "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600"),
    (["ring", "diamond"], "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=600"),
    (["charger", "ev"], "https://images.unsplash.com/photo-1563720223185-11003d516935?w=600"),
    (["espresso", "coffee"], "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=600"),
    (["register", "cash", "pos"], "https://images.unsplash.com/photo-1556742049-0a67e5572248?w=600"),
]

def get_source_url(name):
    low = name.lower()
    for keywords, url in CURATED_PHOTOS:
        for kw in keywords:
            if kw in low:
                return url
    # fallback to pollinations
    safe = requests.utils.quote(f"product photography of {name}, clean background, commercial high quality")
    return f"https://image.pollinations.ai/prompt/{safe}?width=400&height=400&nologo=true"

conn = sqlite3.connect("c:/PocketSmart/pocketsmart.db")
c = conn.cursor()

c.execute("SELECT DISTINCT name FROM recommendation_items WHERE image_url IS NULL OR image_url = '' OR image_url LIKE '<%'")
missing_names = [row[0] for row in c.fetchall()]
print(f"Missing image count for {len(missing_names)} distinct item names")

cache = {}

for name in missing_names:
    src_url = get_source_url(name)
    try:
        t0 = time.time()
        res = cloudinary.uploader.upload(src_url, folder="pocketsmart_items")
        c_url = res.get("secure_url")
        if c_url:
            cache[name] = c_url
            c.execute("UPDATE recommendation_items SET image_url = ? WHERE name = ? AND (image_url IS NULL OR image_url = '' OR image_url LIKE '<%')", (c_url, name))
            conn.commit()
            print(f"[SUCCESS] {name} ({time.time()-t0:.1f}s) -> {c_url}")
        else:
            print(f"[FAIL] {name}")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        # fallback to direct source url
        c.execute("UPDATE recommendation_items SET image_url = ? WHERE name = ? AND (image_url IS NULL OR image_url = '' OR image_url LIKE '<%')", (src_url, name))
        conn.commit()

# Final check
c.execute("SELECT id, name, image_url FROM recommendation_items WHERE recommendation_id = 13")
print("\nRecommendation 13 items:")
for row in c.fetchall():
    print(row)

conn.close()
print("\nDatabase update complete!")
