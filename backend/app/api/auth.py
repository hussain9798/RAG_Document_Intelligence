"""Authentication endpoints: register, login, me."""
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.database.mongodb import get_database
from app.models.user import new_user_document, user_to_public
from app.schemas.auth_schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = get_logger("rag.api.auth")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    db = get_database()
    password_hash = hash_password(payload.password)
    user_doc = new_user_document(payload.name, payload.email.lower(), password_hash)

    try:
        result = await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user_doc["_id"] = result.inserted_id
    token = create_access_token(str(result.inserted_id))
    logger.info("User registered: %s", result.inserted_id)

    return TokenResponse(access_token=token, user=UserPublic(**user_to_public(user_doc)))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    db = get_database()
    user = await db.users.find_one({"email": payload.email.lower()})
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(str(user["_id"]))
    logger.info("User logged in: %s", user["_id"])
    return TokenResponse(access_token=token, user=UserPublic(**user_to_public(user)))


@router.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)):
    return UserPublic(**user_to_public(current_user))
