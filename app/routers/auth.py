from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_user_optional,
)
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, UserOut, Token, SessionInfo

router = APIRouter(tags=["Authentication"])

def _issue_token_response(user: User, response: Response) -> Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "name": user.name},
        expires_delta=access_token_expires,
    )
    # Set HTTP-only cookie for secure browser interactions
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Allow local HTTP testing
    )
    user_out = UserOut.model_validate(user)
    return Token(access_token=token, token_type="bearer", user=user_out)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@router.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Registers a new user account."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return _issue_token_response(new_user, response)

@router.post("/login", response_model=Token)
@router.post("/api/auth/login", response_model=Token)
def login(login_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticates a user with JSON email and password."""
    user = db.query(User).filter(User.email == login_in.email.lower().strip()).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    return _issue_token_response(user, response)

@router.post("/token", response_model=Token)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login for tools and Swagger UI."""
    user = db.query(User).filter(User.email == form_data.username.lower().strip()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_token_response(user, response)

@router.post("/logout")
@router.post("/api/auth/logout")
def logout(response: Response):
    """Logs out the user by clearing the access_token cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully", "authenticated": False}

@router.get("/me", response_model=UserOut)
@router.get("/api/auth/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return UserOut.model_validate(current_user)

@router.get("/session-info", response_model=SessionInfo)
@router.get("/api/session-info", response_model=SessionInfo)
def get_session_info(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Safe endpoint returning whether the user is logged in and their profile."""
    if current_user:
        return SessionInfo(authenticated=True, user=UserOut.model_validate(current_user))
    return SessionInfo(authenticated=False, user=None)
