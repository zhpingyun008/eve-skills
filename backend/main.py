"""FastAPI Main Application."""
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from routers import admin, auth, payment, skills

app = FastAPI(
    title="AI Agent Skills Marketplace",
    description="Browse, search, and purchase AI Agent skills",
    version="1.0.0",
)

# CORS - allow all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(payment.router)
app.include_router(admin.router)


@app.get("/")
def landing_page():
    from fastapi.responses import HTMLResponse
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    init_db()
    
    # Create admin user if not exists
    from database import SessionLocal
    from models import User
    from auth import hash_password
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@skillsmarket.com",
                hashed_password=hash_password("admin123"),
                tier="enterprise",
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
    except Exception:
        pass
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "healthy"}
