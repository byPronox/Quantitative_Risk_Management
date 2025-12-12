"""
Authentication controller for user login and registration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import os

from passlib.context import CryptContext
from jose import JWTError, jwt

from config.database import get_db
from models.database_models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "qrms-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ============= Pydantic Models =============

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


# ============= Helper Functions =============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# ============= Endpoints =============

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with username and password.
    Returns JWT access token.
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint for form data.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    Note: In production, this should be admin-only.
    """
    # Check if user exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check email if provided
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        email=user_data.email,
        is_active=True,
        is_admin=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/verify", response_model=UserResponse)
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verify if the current token is valid"""
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout user.
    Note: Since JWT is stateless, client should delete the token.
    """
    return {"message": "Successfully logged out", "detail": "Please delete your token on client side"}


# ============= Seed Default User =============

def seed_default_user(db: Session):
    """
    Create default admin user if it doesn't exist.
    Username: qrms, Password: qrms
    """
    existing_user = get_user_by_username(db, "qrms")
    if not existing_user:
        hashed_password = get_password_hash("qrms")
        default_user = User(
            username="qrms",
            hashed_password=hashed_password,
            email="admin@qrms.local",
            is_active=True,
            is_admin=True
        )
        db.add(default_user)
        db.commit()
        print("✅ Default user 'qrms' created successfully")
        return True
    else:
        print("ℹ️ Default user 'qrms' already exists")
        return False
