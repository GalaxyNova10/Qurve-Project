from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None

async def get_current_active_user() -> User:
    return User(username="admin")
