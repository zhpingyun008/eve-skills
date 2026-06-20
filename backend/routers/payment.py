"""Payment router: Alipay QR code integration."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import ALIPAY_APP_ID, PRICING
from database import get_db
from models import PaymentRecord, User
from auth import get_current_user
from schemas import PaymentCreate, PaymentOut

router = APIRouter(prefix="/api/payment", tags=["payment"])


def generate_out_trade_no() -> str:
    """Generate a unique order number."""
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:8]
    return f"SKILLS{ts}{uid}"


def generate_alipay_qr_url(out_trade_no: str, subject: str, amount: float) -> str:
    """
    Generate Alipay QR code URL.
    
    In production, this calls Alipay's SDK to create a payment QR.
    For dev/demo, we return a mock URL and QR placeholder.
    """
    if ALIPAY_APP_ID:
        # Production: Use alipay-sdk-python to generate QR
        # from alipay import Alipay
        # alipay = Alipay(...)
        # qr = alipay.api_alipay_trade_precreate(...)
        # return qr.get('qr_code', '')
        pass

    # Dev mode: return a mock URL (replace with real Alipay integration)
    return f"alipay://qr?trade_no={out_trade_no}&amount={amount}"


@router.post("/create", response_model=PaymentOut)
def create_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a payment order for tier upgrade."""
    if data.tier not in PRICING:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {data.tier}")
    
    tier_info = PRICING[data.tier]
    if tier_info["price"] == 0:
        raise HTTPException(status_code=400, detail="Free tier requires no payment")

    # Don't allow duplicate active subscriptions
    if current_user.tier == data.tier and current_user.tier_expires and current_user.tier_expires > datetime.utcnow():
        raise HTTPException(status_code=400, detail=f"You already have an active {data.tier} subscription")

    out_trade_no = generate_out_trade_no()
    subject = f"Skills Market {tier_info['label']}"

    payment = PaymentRecord(
        user_id=current_user.id,
        amount=tier_info["price"],
        tier=data.tier,
        status="pending",
        out_trade_no=out_trade_no,
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    qr_url = generate_alipay_qr_url(out_trade_no, subject, tier_info["price"])

    return PaymentOut(
        id=payment.id,
        amount=payment.amount,
        tier=payment.tier,
        status=payment.status,
        out_trade_no=payment.out_trade_no,
        qr_code_url=qr_url,
        created_at=payment.created_at,
    )


@router.get("/{payment_id}/status")
def check_payment_status(payment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check the status of a payment."""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "id": payment.id,
        "status": payment.status,
        "tier": payment.tier,
        "amount": payment.amount,
        "out_trade_no": payment.out_trade_no,
    }


@router.post("/{payment_id}/verify")
def verify_payment(payment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verify a payment (simulate Alipay callback).
    In production, this is called by Alipay's async notification.
    """
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == "paid":
        return {"message": "Already paid", "status": "paid"}

    # Simulate payment verification
    payment.status = "paid"
    payment.paid_at = datetime.utcnow()

    # Update user's tier
    user = current_user
    user.tier = payment.tier
    if not user.tier_expires or user.tier_expires < datetime.utcnow():
        user.tier_expires = datetime.utcnow() + timedelta(days=30)
    else:
        user.tier_expires += timedelta(days=30)  # Extend existing

    db.commit()
    return {
        "message": "Payment verified successfully",
        "status": "paid",
        "tier": payment.tier,
        "expires": user.tier_expires.isoformat(),
    }
