from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

app = FastAPI()

# Simulated in-memory database
users_db = {}

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserResponse(UserCreate):
    user_id: str

# RESTful Endpoints

@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate):
    user_id = str(uuid.uuid4())
    users_db[user_id] = user.dict()
    return {**user.dict(), "user_id": user_id}

# @app.get("/users/{user_id}", response_model=UserResponse)
# def get_user(user_id: str = Path(..., description="User ID to retrieve")):
#     if user_id not in users_db:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {**users_db[user_id], "user_id": user_id}

# @app.patch("/users/{user_id}", response_model=UserResponse)
# def update_user(user_id: str, user_update: UserUpdate):
#     if user_id not in users_db:
#         raise HTTPException(status_code=404, detail="User not found")

#     current_data = users_db[user_id]
#     update_data = user_update.dict(exclude_unset=True)
#     current_data.update(update_data)
#     users_db[user_id] = current_data

#     return {**current_data, "user_id": user_id}

# @app.post("/close")
# def delete_user(user_id: str):
#     if user_id not in users_db:
#         raise HTTPException(status_code=404, detail="User not found")
#     del users_db[user_id]
#     return {"message": f"User {user_id} account deleted"}
