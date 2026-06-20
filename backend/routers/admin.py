"""Admin router: stats, user management."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_admin_user, get_current_user
from database import get_db
from models import Download, PaymentRecord, User
from routers.skills import load_skills_json
from schemas import StatsOut, UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=StatsOut)
def get_stats(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get system statistics."""
    skills = load_skills_json()
    categories = {}
    for s in skills:
        cat = s.get("category", "uncategorized")
        categories[cat] = categories.get(cat, 0) + 1

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_downloads = db.query(func.count(Download.id)).scalar() or 0
    total_revenue = db.query(func.sum(PaymentRecord.amount)).filter(
        PaymentRecord.status == "paid"
    ).scalar() or 0.0

    return StatsOut(
        total_skills=len(skills),
        total_categories=len(categories),
        total_users=total_users,
        total_downloads=total_downloads,
        total_revenue=total_revenue,
        categories=dict(sorted(categories.items(), key=lambda x: -x[1])),
    )


@router.get("/users", response_model=list[UserOut])
def list_users(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """List all users."""
    users = db.query(User).all()
    return [UserOut.model_validate(u) for u in users]


@router.put("/users/{user_id}/tier")
def set_user_tier(
    user_id: int,
    tier: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Manually set a user's tier (for testing/management)."""
    if tier not in ("free", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="Invalid tier")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.tier = tier
    from config import PRICING
    if tier == "free":
        user.tier_expires = None
    elif not user.tier_expires or user.tier_expires < datetime.utcnow():
        user.tier_expires = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + __import__('datetime').timedelta(days=30)
    db.commit()
    return {"message": f"User {user.username} tier set to {tier}"}
