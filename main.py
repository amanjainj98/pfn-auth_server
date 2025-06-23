from fastapi import FastAPI, HTTPException, Header, Request, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security.utils import get_authorization_scheme_param
import base64
import re

app = FastAPI()

# User DB in memory for simplicity
users_db: Dict[str, Dict] = {}

# Validation regex patterns
USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{6,20}$")
PASSWORD_PATTERN = re.compile(r"^[\x21-\x7E]{8,20}$")  # ASCII without spaces/control chars

# Schemas
class SignupRequest(BaseModel):
    user_id: str
    password: str

    @validator("user_id")
    def validate_user_id(cls, v):
        if not USER_ID_PATTERN.match(v):
            raise ValueError("user_id must be 6-20 alphanumeric characters")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not PASSWORD_PATTERN.match(v):
            raise ValueError("password must be 8-20 ASCII characters without spaces/control codes")
        return v

class PatchUserRequest(BaseModel):
    nickname: Optional[str] = None
    comment: Optional[str] = None

    @validator("nickname")
    def validate_nickname(cls, v):
        if v is not None and len(v) > 30:
            raise ValueError("nickname too long")
        return v

    @validator("comment")
    def validate_comment(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("comment too long")
        return v

# Utility Functions
def decode_auth(auth_header: str):
    scheme, credentials = get_authorization_scheme_param(auth_header)
    if scheme is None or scheme.lower() != "basic" or not credentials:
        return None, None
    try:
        decoded = base64.b64decode(credentials).decode("utf-8")
    except Exception:
        return None, None
    parts = decoded.split(":", 1)
    return parts if len(parts) == 2 else (None, None)


# Routes
@app.post("/signup")
def signup(data: SignupRequest):
    if data.user_id in users_db:
        raise HTTPException(status_code=400, detail={"message": "Account creation failed", "cause": "already same user_id is used"})

    users_db[data.user_id] = {
        "password": data.password,
        "nickname": data.user_id,
        "comment": ""
    }
    return {
        "message": "Account successfully created",
        "user": {
            "user_id": data.user_id,
            "nickname": data.user_id
        }
    }

@app.get("/users/{user_id}")
def get_user(user_id: str, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail={"message": "Authentication Failed"})
    auth_user, password = decode_auth(authorization)
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail={"message": "No User found"})
    if auth_user != user_id or users_db[user_id]["password"] != password:
        raise HTTPException(status_code=401, detail={"message": "Authentication Failed"})

    user = users_db[user_id]
    response = {
        "user_id": user_id,
        "nickname": user.get("nickname", user_id)
    }
    if user.get("comment"):
        response["comment"] = user["comment"]

    return {
        "message": "User details by user_id",
        "user": response
    }

@app.patch("/users/{user_id}")
def update_user(user_id: str, data: PatchUserRequest, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail={"message": "Authentication Failed"})
    auth_user, password = decode_auth(authorization)
    if auth_user not in users_db or users_db[auth_user]["password"] != password:
        raise HTTPException(status_code=401, detail={"message": "Authentication Failed"})
    if auth_user != user_id:
        raise HTTPException(status_code=403, detail={"message": "No Permission for Update"})
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail={"message": "No User found"})

    if data.nickname is None and data.comment is None:
        raise HTTPException(status_code=400, detail={"message": "User updation failed", "cause": "required nickname or comment"})

    if hasattr(data, "user_id") or hasattr(data, "password"):
        raise HTTPException(status_code=400, detail={"message": "User updation failed", "cause": "not updatable user_id and password"})

    if data.nickname is not None:
        users_db[user_id]["nickname"] = data.nickname if data.nickname else user_id
    if data.comment is not None:
        users_db[user_id]["comment"] = data.comment

    return {
        "message": "User successfully updated",
        "recipe": [{
            "nickname": users_db[user_id].get("nickname"),
            "comment": users_db[user_id].get("comment", "")
        }]
    }

@app.post("/close")
def close_account(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail={"message": "Authentication Failed"})
    user_id, password = decode_auth(authorization)
    if user_id not in users_db or users_db[user_id]["password"] != password:
        raise HTTPException(status_code=401, detail={"message": "Authentication Failed"})

    del users_db[user_id]
    return {"message": "Account and user successfully removed"}
