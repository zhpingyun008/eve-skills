"""Pydantic schemas for API."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# --- Auth Schemas ---
class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    tier: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# --- Skill Schemas ---
class SkillFile(BaseModel):
    path: str
    size_bytes: int
    ext: str


class SkillOut(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    version: str
    author: str
    triggers: List[str]
    tags: List[str]
    level: int
    content_preview: str
    file_count: int
    total_size_bytes: int
    download_count: int
    avg_rating: Optional[float] = None
    rating_count: int = 0

    class Config:
        from_attributes = True


class SkillDetail(SkillOut):
    content_length: int
    files: List[SkillFile] = []
    scripts_count: int
    path: str
    depends_on: List[str] = []
    related_skills: List[str] = []
    content_full: str = ""

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    skills: List[SkillOut]
    categories: Dict[str, int]


class CategoryOut(BaseModel):
    name: str
    count: int


# --- Rating Schemas ---
class RatingCreate(BaseModel):
    skill_id: str
    rating: int  # 1-5


class RatingOut(BaseModel):
    id: int
    user_id: int
    skill_id: str
    rating: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Payment Schemas ---
class PaymentCreate(BaseModel):
    tier: str  # pro, enterprise


class PaymentOut(BaseModel):
    id: int
    amount: float
    tier: str
    status: str
    out_trade_no: str
    qr_code_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Admin Schemas ---
class StatsOut(BaseModel):
    total_skills: int
    total_categories: int
    total_users: int
    total_downloads: int
    total_revenue: float
    categories: Dict[str, int]
