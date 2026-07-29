from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from services.auth_logic import sign_up, sign_in
from utils.exceptions import AuthenticationError

router = APIRouter(prefix="/auth")


class Credentials(BaseModel):
    # EmailStr rejects malformed addresses before we spend a round trip on Supabase
    email: EmailStr
    # Supabase's own default minimum - catching it here gives a cleaner 422 than a 400 from GoTrue
    password: str = Field(min_length=6)


@router.post("/signup")
async def signup(credentials: Credentials):
    try:
        return sign_up(credentials.email, credentials.password)
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.text)


@router.post("/login")
async def login(credentials: Credentials):
    try:
        return sign_in(credentials.email, credentials.password)
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.text)
