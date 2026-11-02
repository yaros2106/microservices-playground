from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, FastAPI, HTTPException
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import User


app = FastAPI()

JWT_KID = "users-1"


password_hasher = PasswordHash.recommended()
private_key = Path(settings.jwt_private_key_path).read_text()
public_key = load_pem_public_key(Path(settings.jwt_public_key_path).read_bytes())
public_jwk = RSAAlgorithm.to_jwk(public_key, as_dict=True)

public_jwk.update({
    "kid": JWT_KID,
    "alg": "RS256",
    "use": "sig",
})


class UserBase(BaseModel):
    email: str = Field(max_length=255)
    name: str = Field(max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.get("/healthcheck")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"service": "users", "status": "ok"}


@app.post("/users", response_model=UserRead, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    password_hash = password_hasher.hash(user.password)
    new_user = User(**user.model_dump(exclude={"password"}), password_hash=password_hash)
    db.add(new_user)
    try:
        await db.commit()
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="user with this email already exists")


@app.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"user with id {user_id} not found")
    return user


@app.post("/login", response_model=TokenResponse)
async def login(creds: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == creds.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if user is None or not password_hasher.verify(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")
    payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": JWT_KID})
    return TokenResponse(access_token=token)


@app.get("/.well-known/jwks.json")
async def jwks():
    return {"keys": [public_jwk]}