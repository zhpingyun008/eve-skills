"""Skills router: listing, search, detail, download."""
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Download, Skill, SkillRating, User
from schemas import (
    CategoryOut,
    RatingCreate,
    RatingOut,
    SkillDetail,
    SkillListResponse,
    SkillOut,
)

router = APIRouter(prefix="/api/skills", tags=["skills"])

# Cache for the loaded JSON dataset
_skills_cache = None


def load_skills_json() -> list:
    """Load skills from the JSON dataset."""
    global _skills_cache
    if _skills_cache is not None:
        return _skills_cache

    from config import SKILLS_DATA_PATH

    if os.path.exists(SKILLS_DATA_PATH):
        with open(SKILLS_DATA_PATH, "r", encoding="utf-8") as f:
            _skills_cache = json.load(f)
        return _skills_cache
    return []


def refresh_skills_cache():
    """Force refresh the skills cache."""
    global _skills_cache
    _skills_cache = None
    return load_skills_json()


def skill_json_to_out(skill: dict, db: Session = None) -> dict:
    """Convert a JSON skill record to a response dict."""
    # Get download count from DB
    download_count = 0
    avg_rating = None
    rating_count = 0

    if db:
        download_count = db.query(func.count(Download.id)).filter(
            Download.skill_id == skill["id"]
        ).scalar() or 0

        rating_data = db.query(
            func.avg(SkillRating.rating).label("avg"),
            func.count(SkillRating.id).label("count"),
        ).filter(SkillRating.skill_id == skill["id"]).first()

        if rating_data:
            avg_rating = round(float(rating_data.avg), 1) if rating_data.avg else None
            rating_count = rating_data.count or 0

    triggers = skill.get("triggers", [])
    if isinstance(triggers, list):
        triggers = [t for t in triggers if t.strip()]  # Remove empty strings

    return {
        "id": skill["id"],
        "name": skill["name"],
        "slug": skill.get("slug", skill["name"].lower().replace(" ", "-")),
        "description": skill.get("description", ""),
        "category": skill.get("category", "uncategorized"),
        "version": skill.get("version", "1.0.0"),
        "author": skill.get("author", "Unknown"),
        "triggers": triggers,
        "tags": skill.get("tags", []),
        "level": skill.get("level", 1),
        "content_preview": skill.get("content_preview", ""),
        "file_count": skill.get("file_count", 0),
        "total_size_bytes": skill.get("total_size_bytes", 0),
        "download_count": download_count,
        "avg_rating": avg_rating,
        "rating_count": rating_count,
    }


def get_skill_by_id(skill_id: str) -> Optional[dict]:
    """Find a skill by ID in the JSON dataset."""
    skills = load_skills_json()
    for s in skills:
        if s["id"] == skill_id:
            return s
    return None


@router.get("/categories", response_model=list[CategoryOut])
def list_categories():
    """List all categories with skill counts."""
    skills = load_skills_json()
    counts = {}
    for s in skills:
        cat = s.get("category", "uncategorized")
        counts[cat] = counts.get(cat, 0) + 1
    return [{"name": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


@router.get("", response_model=SkillListResponse)
def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("name"),
    db: Session = Depends(get_db),
):
    """List skills with filtering, search, and pagination."""
    skills = load_skills_json()
    filtered = []

    for s in skills:
        # Category filter
        if category and s.get("category", "") != category:
            continue

        # Search filter
        if search:
            q = search.lower()
            name_match = q in s.get("name", "").lower()
            desc_match = q in s.get("description", "").lower()
            tag_match = any(q in t.lower() for t in s.get("tags", []))
            trigger_match = any(q in t.lower() for t in s.get("triggers", []) if isinstance(t, str))
            if not (name_match or desc_match or tag_match or trigger_match):
                continue

        filtered.append(s)

    # Sort
    if sort == "name":
        filtered.sort(key=lambda x: x.get("name", "").lower())
    elif sort == "size":
        filtered.sort(key=lambda x: x.get("total_size_bytes", 0), reverse=True)
    elif sort == "newest":
        filtered.sort(key=lambda x: x.get("scanned_at", ""), reverse=True)
    elif sort == "popular":
        # Sort by download count (from DB)
        filtered.sort(key=lambda x: x.get("name", "").lower())

    # Compute categories for response
    categories = {}
    for s in skills:
        cat = s.get("category", "uncategorized")
        categories[cat] = categories.get(cat, 0) + 1

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_skills = filtered[start:end]

    return SkillListResponse(
        total=total,
        page=page,
        page_size=page_size,
        skills=[skill_json_to_out(s, db) for s in page_skills],
        categories=dict(sorted(categories.items(), key=lambda x: -x[1])),
    )


@router.get("/{skill_id}", response_model=SkillDetail)
def get_skill_detail(skill_id: str, db: Session = Depends(get_db)):
    """Get full detail of a skill."""
    skill = get_skill_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Also check if there's content_full from reading the actual file
    content_full = ""
    skill_dir = skill.get("skill_dir", "")
    skill_md_path = os.path.join(skill_dir, "SKILL.md") if skill_dir else ""
    if skill_md_path and os.path.exists(skill_md_path):
        try:
            with open(skill_md_path, "r", encoding="utf-8", errors="replace") as f:
                content_full = f.read()
        except Exception:
            content_full = skill.get("content_preview", "")
    else:
        content_full = skill.get("content_preview", "")

    result = skill_json_to_out(skill, db)
    result.update({
        "content_length": skill.get("content_length", 0),
        "files": skill.get("files", []),
        "scripts_count": skill.get("scripts_count", 0),
        "path": skill.get("path", ""),
        "depends_on": skill.get("depends_on", []),
        "related_skills": skill.get("related_skills", []),
        "content_full": content_full,
    })
    return SkillDetail(**result)


@router.get("/{skill_id}/download")
def download_skill(skill_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Download a skill as a ZIP archive."""
    skill = get_skill_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Check tier access
    if current_user.tier == "free":
        # Free users can download at most 50 distinct skills
        downloaded_count = db.query(func.count(Download.id)).filter(
            Download.user_id == current_user.id
        ).scalar() or 0
        if downloaded_count >= 50:
            raise HTTPException(
                status_code=403,
                detail="Free tier limited to 50 downloads. Upgrade to Pro for unlimited access.",
            )

    # Create ZIP
    skill_dir = skill.get("skill_dir", "")
    if not skill_dir or not os.path.isdir(skill_dir):
        raise HTTPException(status_code=500, detail="Skill directory not found on server")

    # Create temp zip
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, fnames in os.walk(skill_dir):
            for fname in fnames:
                file_path = os.path.join(root, fname)
                arcname = os.path.relpath(file_path, skill_dir)
                zf.write(file_path, arcname)

    # Record download
    dl = Download(
        user_id=current_user.id,
        skill_id=skill_id,
        skill_name=skill.get("name", ""),
        downloaded_at=datetime.utcnow(),
    )
    db.add(dl)
    db.commit()

    zip_path = tmp.name
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{skill.get('name', 'skill')}.zip",
        headers={"Content-Disposition": f'attachment; filename="{skill.get("name", "skill")}.zip"'},
    )


@router.post("/rate", response_model=RatingOut)
def rate_skill(data: RatingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rate a skill (1-5)."""
    skill = get_skill_by_id(data.skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Check if user already rated this skill
    existing = db.query(SkillRating).filter(
        SkillRating.user_id == current_user.id,
        SkillRating.skill_id == data.skill_id,
    ).first()

    if existing:
        existing.rating = data.rating
        db.commit()
        db.refresh(existing)
        return RatingOut.model_validate(existing)
    else:
        rating = SkillRating(
            user_id=current_user.id,
            skill_id=data.skill_id,
            rating=data.rating,
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return RatingOut.model_validate(rating)


@router.post("/scan/refresh")
def rescan_skills(current_user: User = Depends(get_current_user)):
    """Force reload skills from JSON file."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    refresh_skills_cache()
    skills = load_skills_json()
    return {"total": len(skills), "message": "Skills cache refreshed"}
