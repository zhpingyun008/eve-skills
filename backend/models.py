"""SQLAlchemy models."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    tier = Column(String(20), default="free")  # free, pro, enterprise
    tier_expires = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship
    downloads = relationship("Download", back_populates="user")
    ratings = relationship("SkillRating", back_populates="user")


class Skill(Base):
    """Cached skill metadata from the JSON dataset."""
    __tablename__ = "skills"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="uncategorized")
    version = Column(String(20), default="1.0.0")
    author = Column(String(100), default="Unknown")
    level = Column(Integer, default=1)
    path = Column(String(200), default="")
    content_length = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    scripts_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(100), nullable=False)
    skill_name = Column(String(200), default="")
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="downloads")


class SkillRating(Base):
    __tablename__ = "skill_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    tier = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")  # pending, paid, expired
    out_trade_no = Column(String(100), unique=True, nullable=False)
    alipay_trade_no = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
