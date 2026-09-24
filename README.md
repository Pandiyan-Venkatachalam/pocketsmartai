# PocketSmart AI - Smart Budget & Project Planner

PocketSmart AI is an intelligent budget planning and estimation platform. It features specialized domain calculation engines and AI-curated product recommendations with live Cloudinary image hosting.

## Features
- **Multi-Domain Planners**: House Construction, Home Interior, Party & Event Planning, Jewelry & Luxury, Travel, School, and Custom Planners.
- **AI Recommendation Engine**: Powered by Google Gemini with live market estimation heuristics.
- **Cloud Storage**: Automatic product image generation and cloud hosting with **Cloudinary**.
- **Cloud Database**: Persistent PostgreSQL integration with **Supabase**.
- **Modern UI**: Responsive dark-mode dashboard with interactive budget and feasibility analytics.

## Tech Stack
- **Backend**: FastAPI, Python 3.11, Uvicorn, SQLAlchemy
- **Database**: PostgreSQL (Supabase)
- **Image Hosting**: Cloudinary
- **Frontend**: Jinja2 HTML5, Vanilla CSS, Vanilla JavaScript

## Local Development
1. Create virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `.env` with your Supabase, Gemini, and Cloudinary credentials.
4. Run server:
   ```bash
   python run.py
   ```
   Open `http://127.0.0.1:8080`.
