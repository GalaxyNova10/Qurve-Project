from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    profile: dict | None = None
    settings: dict | None = None

async def get_current_active_user() -> User:
    return User(
        username="demo@qurve.ai", 
        email="demo@qurve.ai", 
        full_name="Demo User",
        profile={},
        settings={}
    )

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "demo@qurve.ai" and form_data.password == "password123":
        return {"access_token": "fake-demo-token", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

@router.get("/users/me/")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/users/me/profile")
async def update_profile(profile_data: dict, current_user: User = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": profile_data.get("name", current_user.full_name),
        "profile": profile_data
    }

@router.put("/users/me/settings")
async def update_settings(settings_data: dict, current_user: User = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "settings": settings_data
    }
