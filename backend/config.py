"""Application configuration."""
import os
import secrets

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skills_market.db")

# Generate a random secret key if not set in environment
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

SKILLS_DATA_PATH = os.getenv(
    "SKILLS_DATA_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "skills.json"),
)

# Tier pricing (in CNY)
PRICING = {
    "free": {"price": 0, "max_skills": 50, "label": "Free"},
    "pro": {"price": 99, "max_skills": None, "label": "Pro ¥99/mo"},
    "enterprise": {"price": 299, "max_skills": None, "label": "Enterprise ¥299/mo"},
}

ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY", "")
ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_PUBLIC_KEY", "")
