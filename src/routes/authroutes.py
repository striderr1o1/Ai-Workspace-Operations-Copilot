from fastapi import APIRouter
from pydantic import BaseModel
from services.auth import signup, signin
router = APIRouter()

class credentials(BaseModel):
    email: str
    password: str

class token(BaseModel):
    access_token: str

@router.post('/signup')
async def signup_endpoint(cred: credentials):
    response = signup(cred.email, cred.password)
    return response

@router.post('/signin')
async def signin_endpoint():
    response = signin()
    return response 

@router.post('/logout')
async def logout_endpoint(tok: token):
    pass
