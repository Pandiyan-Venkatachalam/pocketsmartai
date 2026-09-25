import os
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", settings.PORT))
    debug = settings.DEBUG and (os.environ.get("APP_ENV", "").lower() != "production")
    print(f"Starting {settings.APP_NAME} on http://{host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug
    )
