
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import settings
from app.db.models import Customer, OTPChallenge


OTP_EXPIRY_SECONDS = 300
RESEND_COOLDOWN_SECONDS = 60
MAX_ATTEMPTS = 5
TOKEN_EXPIRY_MINUTES = 15


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) != 10:
        raise ValueError("Enter a valid 10-digit mobile number.")
    return digits


def hash_otp(phone: str, otp: str) -> str:
    message = f"{phone}:{otp}".encode()
    return hmac.new(
        settings.SECRET_KEY.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def request_otp(db: Session, phone: str) -> str:
    phone = normalize_phone(phone)

    customer = db.scalar(
        select(Customer).where(Customer.phone == phone)
    )
    if customer is None:
        raise ValueError("Unable to send OTP to this number.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    previous = db.scalar(
        select(OTPChallenge)
        .where(
            OTPChallenge.phone == phone,
            OTPChallenge.consumed_at.is_(None),
        )
        .order_by(OTPChallenge.id.desc())
        .limit(1)
    )

    if previous and (now - previous.last_sent_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        raise ValueError("Please wait before requesting another OTP.")

    otp = f"{secrets.randbelow(1_000_000):06d}"

    challenge = OTPChallenge(
        phone=phone,
        otp_hash=hash_otp(phone, otp),
        created_at=now,
        expires_at=now + timedelta(seconds=OTP_EXPIRY_SECONDS),
        last_sent_at=now,
        attempts=0,
    )
    db.add(challenge)
    db.commit()

    # Development-only test adapter. Never return OTP from the API.
    if settings.ENVIRONMENT == "development":
        print(f"[DEV OTP] Test code for {phone}: {otp}")

    return "If the number is registered, an OTP request has been processed."


def verify_otp(db: Session, phone: str, otp: str) -> str:
    phone = normalize_phone(phone)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    challenge = db.scalar(
        select(OTPChallenge)
        .where(
            OTPChallenge.phone == phone,
            OTPChallenge.consumed_at.is_(None),
        )
        .order_by(OTPChallenge.id.desc())
        .limit(1)
        .with_for_update()
    )

    if challenge is None:
        raise ValueError("Invalid or expired OTP.")

    if now >= challenge.expires_at:
        raise ValueError("Invalid or expired OTP.")

    if challenge.attempts >= MAX_ATTEMPTS:
        raise ValueError("Maximum verification attempts reached.")

    challenge.attempts += 1

    expected = hash_otp(phone, otp)
    if not hmac.compare_digest(challenge.otp_hash, expected):
        db.commit()
        raise ValueError("Invalid or expired OTP.")

    challenge.consumed_at = now

    customer = db.scalar(
        select(Customer).where(Customer.phone == phone)
    )
    if customer is None:
        db.commit()
        raise ValueError("Invalid or expired OTP.")

    token = jwt.encode(
        {
            "sub": str(customer.id),
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    db.commit()
    return token


def get_customer_from_token(db: Session, token: str) -> Customer:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        customer_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise ValueError("Invalid or expired access token.")

    customer = db.get(Customer, customer_id)

    if customer is None:
        raise ValueError("Customer not found.")

    return customer
